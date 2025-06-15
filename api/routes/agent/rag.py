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
from api.routes.knowledge.search import _elasticsearch_search_internal
from core.agent.coze.coze_agent import CozeAgent
from fastapi.responses import StreamingResponse
from core.utils.logger import register_logger
import urllib.parse
import http.client
import asyncio
from elasticsearch import Elasticsearch
from config import Config
from fastapi import HTTPException

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
        rag_agent = CozeAgent(tag = bot_tag)
        
        sources_text = ""
        for i, source in enumerate(sources):
            title = source.get('title', '无标题')
            content = source.get('content', '') # 使用正确的 'content' 字段
            
            # 构建单条source的文本，确保换行正确
            source_item_text = f"[{i+1}] 标题: {title}\n内容: {content}\n\n"
            sources_text += source_item_text
            
        # 如果sources_text为空，可能需要一个提示
        if not sources_text.strip():
            sources_text = "没有找到相关的参考资料。"

        prompt = f"用户问题：{query}\n\n参考资料：\n{sources_text}"
        
        logger.debug(f"发送给RAG Agent的最终prompt (部分):\n{prompt[:1000]}...")
        
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
                
            response = await asyncio.wait_for(_generate_with_timeout(), timeout=60.0)
            
        except asyncio.TimeoutError:
            logger.warning(f"生成回答请求超时（>60秒）")
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
        platform = req_data.get("platform") 
        max_results = req_data.get("max_results", 10)
        request_format = req_data.get("format", "markdown")
        request_stream = req_data.get("stream", False)
        rewrite_query_enabled = req_data.get("rewrite_query", False)  # 新增参数，默认为False
        
        # 1. 根据参数决定是否查询改写
        if rewrite_query_enabled:
            logger.debug(f"开始改写查询: {query}")
            enhanced_query = await rewrite_query(query)
            logger.debug(f"查询改写完成: {query} -> {enhanced_query}")
        else:
            enhanced_query = query
            logger.debug(f"查询改写已禁用，使用原始查询: {query}")
            
        # 2. 调用共享的Elasticsearch检索函数
        logger.debug(f"开始使用Elasticsearch检索: query='{query}', enhanced_query='{enhanced_query}'")
        response = await _elasticsearch_search_internal(
            query=query,
            enhanced_query=enhanced_query,
            platform=platform,
            size=max_results
        )

        retrieved_docs = response['hits']['hits']
        logger.debug(f"ES检索到 {len(retrieved_docs)} 条相关文档")
        
        sources = []
        for hit in retrieved_docs:
            source_data = hit['_source']
            content_preview = source_data.get('content', '')
            if len(content_preview) > 2000:
                content_preview = content_preview[:2000]

            sources.append({
                "title": source_data.get('title', '无标题'),
                "content": content_preview,
                "author": source_data.get('author', ''),
                "platform": source_data.get('platform', ''),
                "original_url": source_data.get('original_url', ''),
                "relevance": hit['_score']
            })

        logger.debug(f"从 Elasticsearch 获取到 {len(sources)} 条搜索结果")

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
        
        logger.debug(f"RAG处理完成，耗时: {total_time:.2f}秒")
        logger.debug(f"最终响应内容:\n{'-'*30}\n{(answer_result['response'] or '')[:500]}...\n{'-'*30}")
        
        if request_stream:
            return StreamingResponse(get_stream_generator(result)(), media_type="text/event-stream")
        return Response.success(data=result, details={"message": "查询成功"})
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"RAG处理失败: {str(e)}\n{error_detail}")
        return Response.error(message=f"处理失败: {str(e)}")