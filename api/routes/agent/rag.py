"""
基于Coze的RAG系统
提供基于Coze的检索增强生成功能
"""
import os
import time
import json
import traceback
import datetime
from typing import List, Dict, Any, Optional, Union
from fastapi import APIRouter
from api.models.common import Response, Request, validate_params
from core.agent.coze.coze_agent import CozeAgent
from fastapi.responses import StreamingResponse
from core.utils.logger import register_logger
import urllib.parse
import http.client
import asyncio

# 禁用代理设置
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['all_proxy'] = ''

logger = register_logger("agent.rag")

router = APIRouter()

async def rewrite_query(query: str, bot_tag = "queryEnhance") -> str:
    """使用Coze改写bot改写用户查询"""
    try:
        rewrite_agent = CozeAgent(tag = bot_tag)
        prompt = query
        start_time = time.time()
        
        try:
            # 使用异步超时控制，最多等待30秒
            async def _rewrite_with_timeout():
                # 创建可取消的任务
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, lambda: rewrite_agent.chat_with_new_conversation(prompt, stream=False))
                return response
                
            response = await asyncio.wait_for(_rewrite_with_timeout(), timeout=30.0)
            
        except asyncio.TimeoutError:
            logger.warning(f"改写请求超时（>30秒），返回原始查询")
            return query
            
        elapsed = time.time() - start_time

        if response['response']: 
            rewritten_query = response['response'].strip()
            return rewritten_query
        return query
    except Exception as e:
        logger.error(f"查询改写失败: {str(e)}")
        return query

async def generate_answer(query: str, enhanced_query: str, sources: List[Any], bot_tag = "answerGenerate") -> Dict[str, Any]:
    """使用Coze RAG bot生成答案"""
    try:
        rag_agent = CozeAgent(tag = bot_tag, index = 1)
        
        sources_text = ""
        for i, source in enumerate(sources):
            try:
                # 尝试获取source的各个字段
                platform = getattr(source, 'platform', '未知平台') if hasattr(source, 'platform') else source.get('platform', '未知平台') if isinstance(source, dict) else '未知平台'
                title = getattr(source, 'title', '未知标题') if hasattr(source, 'title') else source.get('title', '未知标题') if isinstance(source, dict) else '未知标题'
                content = getattr(source, 'content', '') if hasattr(source, 'content') else source.get('content', '') if isinstance(source, dict) else str(source)
                
                # 精简内容，最多保留100个字符
                if len(content) > 100:
                    content = content[:100] + "..."
                
                # 更简洁的格式
                sources_text += f"[{i+1}] 标题：{title}\n来源：{platform}\n内容：{content}\n\n"
            except Exception as e:
                logger.error(f"处理source[{i}]失败: {str(e)}")
                sources_text += f"[{i+1}] 无法处理的来源\n\n"

        # 简化提示词，只包含查询和来源信息
        prompt = f"用户问题：{query}\n\n参考资料：\n{sources_text}"
        
        start_time = time.time()
        try:
            async def _generate_with_timeout():
                loop = asyncio.get_event_loop()
                
                # 使用chat_with_new_conversation方法直接获取回答和建议问题
                response = await loop.run_in_executor(
                    None, 
                    lambda: rag_agent.chat_with_new_conversation(prompt, stream=False, openid=f"rag_user_{int(time.time())}")
                )
                
                return response
                
            response = await asyncio.wait_for(_generate_with_timeout(), timeout=30.0)
            
        except asyncio.TimeoutError:
            logger.warning(f"生成回答请求超时（>30秒）")
            return {
                "response": "抱歉，回答生成超时，请稍后再试。",
                "suggested_questions": []
            }
        except Exception as e:
            raise
            
        elapsed = time.time() - start_time
        logger.info(f"rag响应耗时: {elapsed:.2f}秒")
        
        # 使用新格式的返回值，包含response和suggested_questions两个字段
        answer = response.get("response", "")
        suggested_questions = response.get("suggested_questions", [])
        
        # 处理可能的格式化前缀
        if answer and (answer.startswith("回答：") or answer.startswith("回答:")):
            answer = answer[3:].strip()
            
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

def get_stream_generator(result: Dict[str, Any]):
    """生成流式响应的生成器"""
    def stream_generator():
        try:
            
            yield f"data: {json.dumps({'type': 'query', 'original': result['original_query'], 'rewritten': result['rewritten_query']})}\n\n"

            response_text = result["response"]
            chunk_size = 20
            
            # 用于记录所有响应块
            all_chunks = []
            
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i+chunk_size]
                all_chunks.append(chunk)
                yield f"data: {json.dumps({'type': 'content', 'chunk': chunk})}\n\n"
                time.sleep(0.05)
                

            # 转换sources为可序列化的格式
            sources_data = []
            for source in result.get('sources', []):
                try:
                    if isinstance(source, bytes):
                        # 如果是字节，先解码
                        source_str = source.decode('utf-8')
                        source_dict = json.loads(source_str)
                        sources_data.append(source_dict)
                    elif hasattr(source, 'dict'):
                        # 如果是Pydantic模型
                        source_dict = source.dict()
                        # 处理日期时间字段
                        for key, value in source_dict.items():
                            if isinstance(value, (datetime.datetime, datetime.date)):
                                source_dict[key] = value.isoformat()
                        sources_data.append(source_dict)
                    elif isinstance(source, dict):
                        # 如果已经是字典，处理日期时间字段
                        source_dict = {}
                        for key, value in source.items():
                            if isinstance(value, (datetime.datetime, datetime.date)):
                                source_dict[key] = value.isoformat()
                            else:
                                source_dict[key] = value
                        sources_data.append(source_dict)
                    else:
                        # 其他情况，尝试转换为字典
                        logger.warning(f"未知的source类型: {type(source)}")
                        # 尝试提取属性
                        source_dict = {
                            'title': getattr(source, 'title', '未知标题'),
                            'content': getattr(source, 'content', ''),
                            'author': getattr(source, 'author', '未知作者'),
                            'platform': getattr(source, 'platform', '未知平台')
                        }
                        sources_data.append(source_dict)
                except Exception as e:
                    logger.error(f"处理source失败: {str(e)}")
                    # 添加一个占位源
                    sources_data.append({
                        'title': '数据处理错误',
                        'content': f'无法处理此来源: {str(e)}',
                        'author': '系统',
                        'platform': '未知'
                    })
                    
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources_data})}\n\n"
            
            if result.get("suggested_questions"):
                logger.debug(f"流式响应包含建议问题: {result['suggested_questions']}")
                yield f"data: {json.dumps({'type': 'suggestions', 'suggestions': result['suggested_questions']})}\n\n"
                
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
            logger.debug(f"流式响应结束")
        except Exception as e:
            logger.error(f"流式生成失败: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
    
    return stream_generator

@router.post("/rag")
async def rag_endpoint(request: Request):
    """coze rag 检索增强生成接口"""
    try:
        start_time = time.time()
        req_data = await request.json()
        required_params = ["query", "openid"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response

        # 获取请求参数
        query = req_data.get("query")
        openid = req_data.get("openid")
        platform = req_data.get("platform", "wechat,website,market,wxapp")  # 默认查询所有平台
        tag = req_data.get("tag", "")  # 标签
        max_results = req_data.get("max_results", 3)  # 单表检索结果数量
        request_format = req_data.get("format", "markdown")  # 返回格式
        request_stream = req_data.get("stream", False)  # 是否流式响应
        
        
        
        # 1. 使用rewrite_bot_id查询改写enhanced_query
        logger.debug(f"开始改写查询: {query}")
        enhanced_query = await rewrite_query(query, 'queryEnhance')
        logger.debug(f"查询改写完成: {query} -> {enhanced_query}")
        
        # 2. 使用enhanced_query调用knowledge/search查询相关信息
        logger.debug(f"开始检索知识: {enhanced_query}")
        
        try:
            # 直接调用search_knowledge函数，无需HTTP请求
            from api.routes.knowledge.search import search_knowledge
            
            # 调整搜索参数，增加返回结果数量
            search_result = await search_knowledge(
                query=enhanced_query,
                openid=openid,
                platform=platform,
                tag=tag,
                max_results=30,  # 显著增加每个表的最大结果数，确保搜索足够多的内容
                page=1,
                page_size=max_results * 4,
                sort_by="relevance",
                max_content_length=2000       # 增加内容长度限制
            )
            
            # 提取搜索结果
            sources = search_result.get("data", [])
            logger.debug(f"获取到 {len(sources)} 条搜索结果")
            
            # 添加日志记录搜索结果的详细信息
            if sources:
                logger.info(f"搜索结果详情（前5条）:")
                for i, source in enumerate(sources[:5]):
                    try:
                        title = getattr(source, 'title', '未知标题') if hasattr(source, 'title') else '未知标题'
                        platform = getattr(source, 'platform', '未知平台') if hasattr(source, 'platform') else '未知平台'
                        content_preview = getattr(source, 'content', '')[:100] if hasattr(source, 'content') else '无内容'
                        logger.info(f"结果[{i+1}] 标题: {title}, 平台: {platform}")
                        logger.info(f"内容预览: {content_preview}...")
                    except Exception as e:
                        logger.error(f"记录搜索结果详情出错: {str(e)}")
                if len(sources) > 5:
                    logger.info(f"... 还有 {len(sources)-5} 条结果未显示")
            
            # 如果没有搜索结果
            if not sources:
                result = {
                    "original_query": query,
                    "rewritten_query": enhanced_query,
                    "response": "抱歉，没有找到相关信息。",
                    "sources": [],
                    "suggested_questions": ["你可以尝试其他问题"],
                    "format": request_format,
                    "retrieved_count": 0,
                    "response_time": time.time() - start_time
                }
                if request_stream:
                    return StreamingResponse(get_stream_generator(result)(), media_type="text/event-stream")
                return Response.success(data=result, details={"message": "未找到相关信息"})
            
            # 3. 使用sources生成答案
            logger.debug(f"开始生成答案: sources数量={len(sources)}")
            answer_result = await generate_answer(query, enhanced_query, sources, 'answerGenerate')
            
            # 构建返回结果
            total_time = time.time() - start_time
            result = {
                "original_query": query,
                "rewritten_query": enhanced_query,
                "response": answer_result["response"],
                "sources": sources,
                "suggested_questions": answer_result["suggested_questions"],
                "format": request_format,
                "retrieved_count": len(sources),
                "response_time": total_time
            }
            
            # 记录最终结果信息
            logger.debug(f"RAG处理完成，耗时: {total_time:.2f}秒")
            logger.debug(f"最终响应内容:\n{'-'*30}\n{(answer_result['response'] or '')[:500]}...\n{'-'*30}")
            
            # 返回结果
            if request_stream:
                return StreamingResponse(get_stream_generator(result)(), media_type="text/event-stream")
            return Response.success(data=result, details={"message": "查询成功"})
            
        except Exception as e:
            logger.error(f"知识库搜索过程异常: {str(e)}\n{traceback.format_exc()}")
            result = {
                "original_query": query,
                "rewritten_query": enhanced_query,
                "response": f"抱歉，搜索过程发生错误: {str(e)}",
                "sources": [],
                "suggested_questions": ["你可以尝试其他问题"],
                "format": request_format,
                "retrieved_count": 0,
                "response_time": time.time() - start_time
            }
            if request_stream:
                return StreamingResponse(get_stream_generator(result)(), media_type="text/event-stream")
            return Response.success(data=result, details={"message": f"搜索过程错误: {str(e)}"})
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"RAG处理失败: {str(e)}\n{error_detail}")
        return Response.error(message=f"处理失败: {str(e)}")