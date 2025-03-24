"""
基于Coze的RAG系统
提供基于Coze的检索增强生成功能，按照指定步骤处理
1. 首先用查询改写bot（rewrite_bot_id），将用户查询改写为更精确的查询
2. 然后在数据库中检索文本，使用回答生成bot（knowledge_bot_id），生成回答和来源
3. 最后使用markdown格式化回答和来源，返回给前端
"""
# 标准库导入
import time
import json
import random
import hashlib
from functools import lru_cache
from typing import List, Dict, Any, Optional, Union

# 第三方库导入
from fastapi import Depends, HTTPException
from api.common import get_api_logger_dep, handle_api_errors
# 本地导入
from api import agent_router
from api.models.agent.rag import RAGRequest, RAGResponse, Source
from core.agent.coze.coze_agent import CozeAgent
from etl.load.py_mysql import async_query_records
from config import Config
from fastapi.responses import JSONResponse, StreamingResponse

config = Config()
logger = get_api_logger_dep()
# 表名映射
TABLE_MAPPING = {
    "wxapp_posts": {"name": "小程序帖子", "content_field": "content", "title_field": "title", "author_field": "nickname"},
    "wxapp_comments": {"name": "小程序评论", "content_field": "content", "title_field": "content", "author_field": "nickname"},
    "wechat_nku": {"name": "微信公众号文章", "content_field": "content", "title_field": "title", "author_field": "account"},
    "website_nku": {"name": "南开网站文章", "content_field": "content", "title_field": "title", "author_field": "author"},
    "market_nku": {"name": "校园集市帖子", "content_field": "content", "title_field": "title", "author_field": "author"}
}

# 缓存配置
CACHE_ENABLED = config.get("core.agent.rag.cache_enabled", True)
CACHE_TTL = config.get("core.agent.rag.cache_ttl", 3600)  # 默认缓存1小时

# 结果缓存字典 {query_hash: (timestamp, result)}
_results_cache = {}

# CozeAgent实例缓存
_coze_agent_instances = {}

def get_coze_agent(tag: str) -> CozeAgent:
    """
    获取或创建CozeAgent实例（单例模式）
    
    Args:
        tag: bot标签，用于从配置中获取bot_id
        
    Returns:
        CozeAgent实例
    """
    if tag not in _coze_agent_instances:
        _coze_agent_instances[tag] = CozeAgent(tag)
    return _coze_agent_instances[tag]

async def rewrite_query(query: str, rewrite_bot_id: str) -> str:
    """
    使用Coze改写bot改写用户查询，使其更适合数据库检索
    
    Args:
        query: 原始查询
        rewrite_bot_id: 改写bot的ID标签
        
    Returns:
        改写后的查询
    """
    try:
        # 最短查询检查
        if len(query.strip()) <= 1:
            logger.debug(f"查询过短，跳过改写: '{query}'")
            return query
            
        # 简单查询不需要改写
        if len(query.strip().split()) <= 2:
            logger.debug(f"查询过于简单，跳过改写: '{query}'")
            return query
            
        # 获取改写bot实例
        rewrite_agent = get_coze_agent(rewrite_bot_id)
        
        # 构建提示词
        prompt = f"请将用户以下查询改写为更精确的搜索查询，以便在数据库中检索相关信息：\n{query}\n只需返回改写后的查询，不要有任何解释或其他文本。"
        
        # 调用改写bot
        start_time = time.time()
        response = rewrite_agent.chat_with_new_conversation(prompt, stream=False)
        elapsed = time.time() - start_time
        
        # 确保结果是字符串
        if response and isinstance(response, str):
            rewritten_query = response.strip()
            logger.debug(f"查询改写耗时: {elapsed:.2f}秒，原查询: '{query}'，改写为: '{rewritten_query}'")
            return rewritten_query
            
        # 如果返回的不是有效字符串，使用原始查询
        logger.warning(f"查询改写返回无效结果类型: {type(response)}，使用原始查询")
        return query
    except Exception as e:
        logger.error(f"查询改写失败: {str(e)}")
        # 如果改写失败，返回原始查询
        return query

async def generate_answer(query: str, context: str, knowledge_bot_id: str) -> Dict[str, Any]:
    """
    使用Coze知识bot生成回答
    
    Args:
        query: 用户查询（可能是改写后的）
        context: 从数据库检索的上下文
        knowledge_bot_id: 知识bot的ID标签
        
    Returns:
        包含回答、建议问题的字典
    """
    try:
        # 获取知识bot实例
        answer_agent = get_coze_agent(knowledge_bot_id)
        
        # 构建提示词
        prompt = f"""基于以下检索到的信息回答用户的问题。
用户问题: {query}

检索到的信息:
{context}

请提供准确、简洁的回答，并在回答的末尾建议3个可能的后续问题。
回答需要使用markdown格式，包含适当的标题、列表和强调。
回答格式应为:

回答：...

建议问题：
1. ...
2. ...
3. ...
"""
        
        # 调用知识bot
        start_time = time.time()
        response = answer_agent.chat_with_new_conversation(prompt, stream=False)
        elapsed = time.time() - start_time
        
        logger.debug(f"回答生成耗时: {elapsed:.2f}秒")
        
        # 处理返回的回答，提取建议问题
        suggested_questions = []
        
        if "建议问题：" in response or "建议问题:" in response:
            # 分割回答和建议问题部分
            parts = response.split("建议问题：" if "建议问题：" in response else "建议问题:")
            answer_part = parts[0].strip()
            
            if len(parts) > 1:
                questions_part = parts[1].strip()
                # 提取建议问题
                for line in questions_part.split("\n"):
                    line = line.strip()
                    if line and any(line.startswith(prefix) for prefix in ["1.", "2.", "3.", "- "]):
                        # 移除序号和前导符号
                        question = line.lstrip("123.- ").strip()
                        if question:
                            suggested_questions.append(question)
        
        # 如果分割失败，直接返回整个回答
        answer = response if not suggested_questions else answer_part
        
        # 确保回答是Markdown格式
        if answer.startswith("回答：") or answer.startswith("回答:"):
            answer = answer[3:].strip()
        
        return {
            "response": answer,
            "suggested_questions": suggested_questions
        }
    
    except Exception as e:
        logger.error(f"回答生成失败: {str(e)}")
        return {
            "response": f"抱歉，无法生成回答。错误: {str(e)}",
            "suggested_questions": []
        }

def get_cache_key(request: RAGRequest) -> str:
    """
    生成请求的缓存键
    
    Args:
        request: RAG请求对象
        
    Returns:
        str: 缓存键
    """
    # 构建包含关键请求参数的字典
    key_dict = {
        "query": request.query,
        "tables": ",".join(sorted(request.tables)),  # 将列表转换为字符串
        "max_results": request.max_results,
        "format": request.format,
        "rewrite_bot_id": request.rewrite_bot_id or "",
        "knowledge_bot_id": request.knowledge_bot_id or ""
    }
    # 序列化为JSON并计算哈希
    key_str = json.dumps(key_dict, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()

def get_cached_result(cache_key: str) -> Optional[Dict[str, Any]]:
    """
    从缓存中获取结果
    
    Args:
        cache_key: 缓存键
        
    Returns:
        Optional[Dict[str, Any]]: 缓存的结果，如果不存在或过期则返回None
    """
    if not CACHE_ENABLED:
        return None
        
    if cache_key in _results_cache:
        timestamp, result = _results_cache[cache_key]
        # 检查缓存是否过期
        if time.time() - timestamp < CACHE_TTL:
            logger.debug(f"缓存命中: {cache_key[:8]}...")
            return result
        else:
            # 清理过期缓存
            del _results_cache[cache_key]
            
    return None

def set_cached_result(cache_key: str, result: Dict[str, Any]) -> None:
    """
    设置缓存结果
    
    Args:
        cache_key: 缓存键
        result: 要缓存的结果
    """
    if not CACHE_ENABLED:
        return
        
    _results_cache[cache_key] = (time.time(), result)
    logger.debug(f"缓存已设置: {cache_key[:8]}...")
    
    # 清理旧缓存
    if len(_results_cache) > 1000:  # 缓存条目过多时清理
        logger.debug(f"清理过期缓存，当前缓存大小: {len(_results_cache)}")
        current_time = time.time()
        expired_keys = [k for k, (ts, _) in _results_cache.items() if current_time - ts > CACHE_TTL]
        for k in expired_keys:
            del _results_cache[k]
        logger.debug(f"已清理 {len(expired_keys)} 个过期缓存条目，当前缓存大小: {len(_results_cache)}")

def get_stream_generator(result: Dict[str, Any]):
    """
    生成流式响应的生成器
    
    Args:
        result: 完整的RAG响应结果
        
    Returns:
        生成器函数，用于流式响应
    """
    def stream_generator():
        # 发送原始查询和改写查询
        yield f"data: {json.dumps({'type': 'query', 'original': result['original_query'], 'rewritten': result['rewritten_query']})}\n\n"
        
        # 分段发送响应内容
        response_text = result["response"]
        chunk_size = 20  # 每次发送的字符数
        for i in range(0, len(response_text), chunk_size):
            chunk = response_text[i:i+chunk_size]
            yield f"data: {json.dumps({'type': 'content', 'chunk': chunk})}\n\n"
            time.sleep(0.05)  # 模拟生成延迟
            
        # 发送来源和建议问题 - 需要处理Source对象的序列化
        sources_data = []
        for source in result['sources']:
            # 如果是Source对象，需要调用dict()方法
            if hasattr(source, 'dict'):
                sources_data.append(source.dict())
            else:
                # 已经是字典
                sources_data.append(source)
                
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources_data})}\n\n"
        yield f"data: {json.dumps({'type': 'suggested', 'questions': result['suggested_questions']})}\n\n"
        
        # 发送完成信号
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return stream_generator

@agent_router.post("/rag", response_model=RAGResponse)
@handle_api_errors("RAG检索增强生成")
async def rag_search(
    request: RAGRequest,
    api_logger=Depends(get_api_logger_dep)
):
    """
    使用Coze实现的RAG系统
    1. 查询改写
    2. 数据库检索
    3. 回答生成
    """
    start_time = time.time()
    
    try:
        # 记录请求信息
        api_logger.debug(f"处理RAG请求: query='{request.query}', tables={request.tables}")
        
        # 尝试从缓存获取结果
        cache_key = get_cache_key(request)
        cached_result = get_cached_result(cache_key)
        if cached_result:
            api_logger.debug(f"使用缓存结果，原始查询: '{request.query}'")
            
            # 对于流式请求，返回流式响应
            if request.stream:
                return StreamingResponse(
                    get_stream_generator(cached_result)(),
                    media_type="text/event-stream"
                )
                
            return cached_result
        
        # 验证表名
        if not request.tables:
            api_logger.warning("表名列表为空")
            return JSONResponse(
                status_code=422,
                content={"detail": "必须指定至少一个表名"}
            )
            
        for table in request.tables:
            if table not in TABLE_MAPPING:
                detail = f"不支持的表名: {table}"
                api_logger.error(f"RAG请求验证失败: {detail}")
                return JSONResponse(
                    status_code=400,
                    content={"detail": detail}
                )
        
        # 获取配置中的bot_id或使用请求中指定的值
        rewrite_bot_id = request.rewrite_bot_id or config.get("core.agent.coze.rewrite_bot_id", "rewrite")
        knowledge_bot_id = request.knowledge_bot_id or config.get("core.agent.coze.knowledge_bot_id", "knowledge")
        
        # 步骤1: 查询改写
        rewritten_query = await rewrite_query(request.query, rewrite_bot_id)
        api_logger.debug(f"原始查询: '{request.query}', 改写查询: '{rewritten_query}'")
        
        # 步骤2: 数据库检索
        all_results = []
        
        for table in request.tables:
            table_info = TABLE_MAPPING[table]
            content_field = table_info["content_field"]
            title_field = table_info["title_field"]
            
            # 构建LIKE条件
            keywords = rewritten_query.split()
            if not keywords:
                keywords = [rewritten_query]  # 如果没有分割出关键词，使用整个查询
                
            conditions = []
            params = []
            
            for keyword in keywords:
                if not keyword.strip():
                    continue  # 跳过空关键词
                    
                # 为每个关键词创建LIKE条件
                conditions.append(f"({content_field} LIKE ? OR {title_field} LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            
            # 组合所有条件，使用OR连接
            if not conditions:
                combined_condition = "1=1"  # 如果没有有效关键词，返回所有结果
                params = []
            else:
                combined_condition = " OR ".join(conditions)
            
            # 查询记录
            try:
                results = await async_query_records(
                    table_name=table,
                    conditions={
                        "where_condition": combined_condition,
                        "params": params
                    },
                    limit=request.max_results,
                    order_by="id DESC"  # 默认使用ID降序
                )
                
                # 添加表名和类型信息
                for item in results:
                    item["_table"] = table
                    item["_type"] = table_info["name"]
                    all_results.append(item)
            except Exception as e:
                api_logger.error(f"查询表{table}时出错: {str(e)}")
                # 继续处理其他表，不中断整个过程
        
        # 步骤3: 构建上下文
        if not all_results:
            # 没有检索到结果时返回提示
            result = {
                "original_query": request.query,
                "rewritten_query": rewritten_query,
                "response": "抱歉，没有找到相关信息。",
                "sources": [],
                "suggested_questions": ["你可以尝试其他问题"],
                "format": request.format,
                "retrieved_count": 0,
                "response_time": time.time() - start_time
            }
            
            # 对于流式请求，返回流式响应
            if request.stream:
                return StreamingResponse(
                    get_stream_generator(result)(),
                    media_type="text/event-stream"
                )
                
            return result
        
        # 按相关性排序结果
        all_results.sort(key=lambda x: len(x.get("content", "")), reverse=True)
        
        # 构建上下文
        context = "\n\n".join([
            f"来源: {item['_type']}\n标题: {item.get(table_info['title_field'], '')}\n内容: {item.get(table_info['content_field'], '')}"
            for item in all_results[:request.max_results]
        ])
        
        # 步骤4: 生成回答
        answer_result = await generate_answer(request.query, context, knowledge_bot_id)
        
        # 步骤5: 构建来源列表
        sources = []
        for item in all_results[:request.max_results]:
            table_name = item.get("_table", "")
            if table_name in TABLE_MAPPING:
                table_info = TABLE_MAPPING[table_name]
                source = Source(
                    type=item.get("_type", "未知来源"),
                    title=item.get(table_info["title_field"], ""),
                    content=item.get(table_info["content_field"], ""),
                    author=item.get(table_info["author_field"], "")
                )
                sources.append(source)
        
        # 计算总耗时
        total_time = time.time() - start_time
        api_logger.debug(f"RAG处理总耗时: {total_time:.2f}秒")
        
        # 构建最终结果
        result = {
            "original_query": request.query,
            "rewritten_query": rewritten_query,
            "response": answer_result["response"],
            "sources": sources,
            "suggested_questions": answer_result["suggested_questions"],
            "format": request.format,
            "retrieved_count": len(all_results),
            "response_time": total_time
        }
        
        # 缓存结果
        set_cached_result(cache_key, result)
        
        # 对于流式请求，返回流式响应
        if request.stream:
            return StreamingResponse(
                get_stream_generator(result)(),
                media_type="text/event-stream"
            )
            
        return result
        
    except Exception as e:
        import traceback
        error_tb = traceback.format_exc()
        logger.error(f"RAG处理失败: {str(e)}")
        logger.error(f"错误详情: {error_tb}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")