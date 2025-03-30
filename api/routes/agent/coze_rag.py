"""
基于Coze的RAG系统
提供基于Coze的检索增强生成功能
"""
import time
import json
import random
import hashlib
import logging
from functools import lru_cache
from typing import List, Dict, Any, Optional, Union

from fastapi import HTTPException, APIRouter
from api.models.agent import Source
from api.models.common import Response, Request, validate_params
from core.agent.coze.coze_agent import CozeAgent
from etl.load.db_core import async_query_records
from config import Config
from fastapi.responses import StreamingResponse

config = Config()
TABLE_MAPPING = {
    "wxapp_post": {"name": "小程序帖子", "content_field": "content", "title_field": "title", "author_field": "nickname"},
    "wxapp_comment": {"name": "小程序评论", "content_field": "content", "title_field": "content", "author_field": "nickname"},
    "wechat_nku": {"name": "微信公众号文章", "content_field": "content", "title_field": "title", "author_field": "account"},
    "website_nku": {"name": "南开网站文章", "content_field": "content", "title_field": "title", "author_field": "author"},
    "market_nku": {"name": "校园集市帖子", "content_field": "content", "title_field": "title", "author_field": "author"}
}

CACHE_ENABLED = config.get("core.agent.rag.cache_enabled", True)
CACHE_TTL = config.get("core.agent.rag.cache_ttl", 3600)

_results_cache = {}

_coze_agent_instances = {}
router = APIRouter()
logger = logging.getLogger("agent.rag")

def get_coze_agent(tag: str) -> CozeAgent:
    """获取或创建CozeAgent实例（单例模式）"""
    # 确保tag是字符串类型
    if isinstance(tag, list):
        if len(tag) > 0:
            tag = tag[0]  # 使用列表的第一个元素
            logger.warning(f"knowledge_bot_id是列表类型，使用第一个元素: {tag}")
        else:
            tag = "default"
            logger.warning(f"knowledge_bot_id是空列表，使用默认值: {tag}")
    elif not isinstance(tag, str):
        tag = str(tag)
        logger.warning(f"knowledge_bot_id不是字符串类型，已转换为: {tag}")
    
    # 如果tag是纯数字ID字符串，则使用direct_tag模式，直接使用tag作为bot_id
    import re
    is_direct_id = re.match(r'^\d+$', tag)
    if is_direct_id:
        tag_key = f"direct:{tag}"
        if tag_key not in _coze_agent_instances:
            try:
                # 创建一个直接使用bot_id的CozeAgent实例
                from core.agent.coze.coze_agent import CozeAgent as DirectCozeAgent
                agent = DirectCozeAgent()
                # 直接设置bot_id而不是通过tag获取
                agent.bot_id = tag
                _coze_agent_instances[tag_key] = agent
                logger.debug(f"直接使用ID创建CozeAgent实例: {tag}")
            except Exception as e:
                logger.error(f"直接使用ID创建CozeAgent实例失败: {str(e)}")
                # 回退到默认tag
                tag_key = "default"
                if tag_key not in _coze_agent_instances:
                    _coze_agent_instances[tag_key] = CozeAgent(tag_key)
        return _coze_agent_instances[tag_key]
    else:
        # 常规模式，通过tag获取bot_id
        if tag not in _coze_agent_instances:
            _coze_agent_instances[tag] = CozeAgent(tag)
        return _coze_agent_instances[tag]

async def rewrite_query(query: str, rewrite_bot_id: str) -> str:
    """使用Coze改写bot改写用户查询"""
    try:
        if len(query.strip()) <= 1:
            return query

        if len(query.strip().split()) <= 2:
            return query

        rewrite_agent = get_coze_agent(rewrite_bot_id)

        prompt = f"请将用户以下查询改写为更精确的搜索查询，以便在数据库中检索相关信息：\n{query}\n只需返回改写后的查询，不要有任何解释或其他文本。"

        start_time = time.time()
        response = rewrite_agent.chat_with_new_conversation(prompt, stream=False)
        elapsed = time.time() - start_time

        if response and isinstance(response, str):
            rewritten_query = response.strip()
            return rewritten_query

        return query
    except Exception as e:
        logger.error(f"查询改写失败: {str(e)}")
        return query

async def generate_answer(query: str, context: str, knowledge_bot_id: str) -> Dict[str, Any]:
    """使用Coze知识bot生成回答"""
    try:
        answer_agent = get_coze_agent(knowledge_bot_id)

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

        # 添加日志
        logger.debug("开始生成回答，参数: query=%s, 上下文长度=%d, bot_id=%s", 
                    query[:30], len(context), knowledge_bot_id)

        start_time = time.time()
        # 添加try-except块进行详细错误排查
        try:
            response = answer_agent.chat_with_new_conversation(prompt, stream=False)
            logger.debug("生成回答成功，响应类型: %s, 长度: %d", type(response), 
                        len(response) if isinstance(response, str) else 0)
        except Exception as e:
            logger.error("生成回答调用失败: %s, %s", str(e), traceback.format_exc())
            raise
        elapsed = time.time() - start_time

        suggested_questions = []

        if "建议问题：" in response or "建议问题:" in response:
            parts = response.split("建议问题：" if "建议问题：" in response else "建议问题:")
            answer_part = parts[0].strip()

            if len(parts) > 1:
                questions_part = parts[1].strip()
                for line in questions_part.split("\n"):
                    line = line.strip()
                    if line and any(line.startswith(prefix) for prefix in ["1.", "2.", "3.", "- "]):
                        question = line.lstrip("123.- ").strip()
                        if question:
                            suggested_questions.append(question)

        answer = response if not suggested_questions else answer_part

        if answer.startswith("回答：") or answer.startswith("回答:"):
            answer = answer[3:].strip()

        logger.debug("生成回答完成, 回答长度=%d, 建议问题数=%d, 用时=%.2fs",
                   len(answer), len(suggested_questions), elapsed)

        return {
            "response": answer,
            "suggested_questions": suggested_questions
        }

    except Exception as e:
        import traceback
        logger.error(f"生成回答失败: {str(e)}\n{traceback.format_exc()}")
        return {
            "response": f"抱歉，无法生成回答。错误: {str(e)}",
            "suggested_questions": []
        }

def get_cache_key(data: Dict[str, Any]) -> str:
    """生成请求的缓存键"""
    key_dict = {
        "query": data.get("query", ""),
        "tables": ",".join(sorted(data.get("tables", []))),
        "max_results": data.get("max_results", 5),
        "format": data.get("format", "markdown"),
        "rewrite_bot_id": data.get("rewrite_bot_id", ""),
        "knowledge_bot_id": data.get("knowledge_bot_id", "")
    }
    key_str = json.dumps(key_dict, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()

def get_cached_result(cache_key: str) -> Optional[Dict[str, Any]]:
    """从缓存中获取结果"""
    if not CACHE_ENABLED:
        return None

    if cache_key in _results_cache:
        timestamp, result = _results_cache[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            return result
        else:
            del _results_cache[cache_key]

    return None

def set_cached_result(cache_key: str, result: Dict[str, Any]) -> None:
    """设置缓存结果"""
    if not CACHE_ENABLED:
        return

    _results_cache[cache_key] = (time.time(), result)

    if len(_results_cache) > 1000:
        current_time = time.time()
        expired_keys = [k for k, (ts, _) in _results_cache.items() if current_time - ts > CACHE_TTL]
        for k in expired_keys:
            del _results_cache[k]

def get_stream_generator(result: Dict[str, Any]):
    """生成流式响应的生成器"""
    def stream_generator():
        try:
            yield f"data: {json.dumps({'type': 'query', 'original': result['original_query'], 'rewritten': result['rewritten_query']})}\n\n"

            response_text = result["response"]
            chunk_size = 20
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i+chunk_size]
                yield f"data: {json.dumps({'type': 'content', 'chunk': chunk})}\n\n"
                time.sleep(0.05)

            # 转换sources为可序列化的格式
            sources_data = []
            for source in result['sources']:
                if hasattr(source, 'dict'):
                    try:
                        source_dict = source.dict()
                        sources_data.append(source_dict)
                    except Exception as e:
                        logger.error(f"无法转换Source对象为字典: {str(e)}")
                        # 提供一个简单的字典作为备选
                        sources_data.append({
                            'type': getattr(source, 'type', '未知'),
                            'title': getattr(source, 'title', ''),
                            'content': getattr(source, 'content', ''),
                            'author': getattr(source, 'author', '')
                        })
                else:
                    # 如果已经是字典，直接添加
                    sources_data.append(source)

            yield f"data: {json.dumps({'type': 'sources', 'sources': sources_data})}\n\n"
            
            # 添加建议问题
            questions = result.get('suggested_questions', [])
            yield f"data: {json.dumps({'type': 'suggested', 'questions': questions})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            import traceback
            logger.error(f"流式生成器错误: {str(e)}\n{traceback.format_exc()}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return stream_generator

@router.post("")
async def rag_endpoint(request: Request):
    """coze rag 搜索接口"""
    try:
        start_time = time.time()
        req_data = await request.json()
        required_params = ["tables", "query", "openid"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response

        query = req_data.get("query")
        tables = req_data.get("tables", [])
        max_results = req_data.get("max_results", 5)
        request_format = req_data.get("format", "markdown")
        request_stream = req_data.get("stream", False)
        openid = req_data.get("openid")
        
        if not tables:
            return Response.bad_request(details={"message": "缺少 tables 参数"})
        for table in tables:
            if table not in TABLE_MAPPING:
                return Response.bad_request(details={"message": f"table: {table} 不存在"})

        if not query:
            return Response.bad_request(details={"message": "缺少 query 参数"})

        logger.debug(f"Coze RAG request, tables: {tables}, query: {query}")
        
        # 缓存处理
        cache_key = get_cache_key(req_data)
        cached_result = get_cached_result(cache_key)
        if cached_result:
            if request_stream:
                return StreamingResponse(get_stream_generator(cached_result)(), media_type="text/event-stream")
            return Response.success(data=cached_result, details={"message": "查询成功(缓存)"})
            
        rewrite_bot_id = req_data.get("rewrite_bot_id") or config.get("core.agent.coze.rewrite_bot_id", "rewrite")
        knowledge_bot_id = req_data.get("knowledge_bot_id") or config.get("core.agent.coze.knowledge_bot_id", "knowledge")
        
        # 确保bot_id是字符串类型
        if isinstance(rewrite_bot_id, list) and rewrite_bot_id:
            rewrite_bot_id = rewrite_bot_id[0]
            logger.warning(f"rewrite_bot_id是列表，使用第一个元素: {rewrite_bot_id}")
        
        if isinstance(knowledge_bot_id, list) and knowledge_bot_id:
            knowledge_bot_id = knowledge_bot_id[0]
            logger.warning(f"knowledge_bot_id是列表，使用第一个元素: {knowledge_bot_id}")

        rewritten_query = await rewrite_query(query, rewrite_bot_id)

        all_results = []
        
        # 检索数据库内容
        for table in tables:
            table_info = TABLE_MAPPING[table]
            content_field = table_info["content_field"]
            title_field = table_info["title_field"]

            # 使用参数化查询代替字符串拼接，避免SQL注入和格式化问题
            sql_params = []
            where_parts = []
            
            # 构建content字段的LIKE条件
            where_parts.append(f"{content_field} LIKE %s")
            sql_params.append(f"%{rewritten_query}%")
            
            # 构建WHERE子句
            where_condition = " OR ".join(where_parts)
            
            logger.debug(f"查询表 {table}，条件: {where_condition}，参数: {sql_params}")
            
            try:
                results = await async_query_records(
                    table_name=table,
                    conditions={"where_condition": where_condition, "params": sql_params},
                    order_by="id DESC",
                    limit=max_results
                )
            except Exception as e:
                logger.error(f"查询表 {table} 失败: {str(e)}")
                results = {"data": []}

            # 如果没有结果，尝试使用原始查询
            if not results["data"] and query != rewritten_query:
                # 使用参数化查询代替字符串拼接
                sql_params = []
                where_parts = []
                
                # 构建content字段的LIKE条件
                where_parts.append(f"{content_field} LIKE %s")
                sql_params.append(f"%{query}%")
                
                # 构建WHERE子句
                where_condition = " OR ".join(where_parts)
                
                logger.debug(f"使用原始查询，表 {table}，条件: {where_condition}，参数: {sql_params}")
                
                try:
                    results = await async_query_records(
                        table_name=table,
                        conditions={"where_condition": where_condition, "params": sql_params},
                        order_by="id DESC",
                        limit=max_results
                    )
                except Exception as e:
                    logger.error(f"原始查询表 {table} 失败: {str(e)}")
                    results = {"data": []}

            for item in results["data"]:
                item["_table"] = table
                item["_type"] = table_info["name"]
                all_results.append(item)

        if not all_results:
            result = {
                "original_query": query,
                "rewritten_query": rewritten_query,
                "response": "抱歉，没有找到相关信息。",
                "sources": [],
                "suggested_questions": ["你可以尝试其他问题"],
                "format": request_format,
                "retrieved_count": 0,
                "response_time": time.time() - start_time
            }

            if request_stream:
                return StreamingResponse(
                    get_stream_generator(result)(),
                    media_type="text/event-stream"
                )

            return Response.success(data=result, details={"message": "未找到相关信息"})

        all_results.sort(key=lambda x: len(x.get("content", "")), reverse=True)

        context_items = []
        for item in all_results[:max_results]:
            table_name = item.get("_table", "")
            if table_name in TABLE_MAPPING:
                table_info = TABLE_MAPPING[table_name]
                context_items.append(
                    f"来源: {item['_type']}\n标题: {item.get(table_info['title_field'], '')}\n内容: {item.get(table_info['content_field'], '')}"
                )
        
        context = "\n\n".join(context_items)
        answer_result = await generate_answer(query, context, knowledge_bot_id)

        sources = []
        for item in all_results[:max_results]:
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

        total_time = time.time() - start_time

        result = {
            "original_query": query,
            "rewritten_query": rewritten_query,
            "response": answer_result["response"],
            "sources": sources,
            "suggested_questions": answer_result["suggested_questions"],
            "format": request_format,
            "retrieved_count": len(all_results),
            "response_time": total_time
        }

        set_cached_result(cache_key, result)

        if request_stream:
            return StreamingResponse(
                get_stream_generator(result)(),
                media_type="text/event-stream"
            )

        return Response.success(data=result, details={"message": "查询成功"})

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"RAG处理失败: {str(e)}\n{error_detail}")
        return Response.error(message=f"处理失败: {str(e)}")