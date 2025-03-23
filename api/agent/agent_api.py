"""
Agent聊天API
提供AI智能体的聊天和知识检索功能
"""
import re
import json
from fastapi import Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Dict, Any, Optional, Union
from loguru import logger
import os
import logging
import time
from datetime import datetime

# 导入通用组件
from api.common import get_api_logger, handle_api_errors, create_standard_response
from api import agent_router as router

# 导入必要的Agent组件
import config
from core.agent.coze.coze_agent import CozeAgent
from core.agent.agent_factory import AgentFactory
from core.agent.session_manager import SessionManager
from core.bridge.context import Context, ContextType
from core.bridge.reply import ReplyType
from etl.load.py_mysql import execute_custom_query

# 导入帖子搜索相关功能
from api.wxapp.search_api import SearchPostRequest

# 请求和响应模型
class ChatRequest(BaseModel):
    query: str = Field(..., description="用户输入的问题")
    history: Optional[List[Dict[str, str]]] = Field(default=[], description="对话历史")
    stream: bool = Field(default=False, description="是否使用流式响应")
    format: Optional[str] = Field(default="markdown", description="返回格式，支持 'markdown', 'text', 'html'")
    openid: Optional[str] = Field(default="default_user", description="用户唯一标识")
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError("问题不能为空")
        return v.strip()
    
    @validator('format')
    def validate_format(cls, v):
        valid_formats = ['markdown', 'text', 'html']
        if v.lower() not in valid_formats:
            raise ValueError(f"格式必须是以下之一: {', '.join(valid_formats)}")
        return v.lower()
    
    @validator('openid')
    def validate_openid(cls, v):
        if not v.strip():
            return "default_user"
        return v.strip()

class ChatResponse(BaseModel):
    response: str = Field(..., description="Agent的回答")
    sources: List[Dict[str, Any]] = Field(default=[], description="引用的知识来源") 
    format: str = Field(default="markdown", description="返回的格式类型")

class SearchRequest(BaseModel):
    keyword: str = Field(..., description="搜索关键词")
    limit: int = Field(default=10, ge=1, le=50, description="返回结果数量上限")
    
    @validator('keyword')
    def validate_keyword(cls, v):
        if not v.strip():
            raise ValueError("关键词不能为空")
        return v.strip()

# RAG请求模型
class RAGRequest(BaseModel):
    """知识库增强生成请求模型"""
    query: str = Field(..., description="用户查询")
    tables: List[str] = Field(["wxapp_posts"], description="要检索的表名列表")
    max_results: int = Field(5, description="每个表返回的最大结果数")
    stream: bool = Field(False, description="是否流式返回")
    format: str = Field("markdown", description="回复格式: markdown|text|html")
    openid: Optional[str] = None
    
    @validator("tables")
    def validate_tables(cls, tables):
        """验证表名"""
        valid_tables = ["wxapp_posts", "wxapp_comments", "wxapp_users", "wechat_nku", "website_nku", "market_nku"]
        for table in tables:
            if table not in valid_tables:
                raise ValueError(f"不支持的表: {table}，有效的表为: {', '.join(valid_tables)}")
        return tables
    
    @validator("format")
    def validate_format(cls, format_type):
        """验证格式"""
        valid_formats = ["markdown", "text", "html"]
        if format_type not in valid_formats:
            raise ValueError(f"不支持的格式: {format_type}，有效的格式为: {', '.join(valid_formats)}")
        return format_type

# 格式化函数
def format_response_content(content, format_type):
    """格式化响应内容"""
    if format_type == "markdown":
        # 已经是Markdown格式，不需要特殊处理
        return content
    elif format_type == "text":
        # 移除Markdown标记
        text = content
        # 移除标题标记
        text = re.sub(r'#+\s+', '', text)
        # 移除粗体和斜体
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        # 移除链接，保留文本
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        # 移除代码块
        text = re.sub(r'```.*?\n(.*?)```', r'\1', text, flags=re.DOTALL)
        # 移除行内代码
        text = re.sub(r'`(.*?)`', r'\1', text)
        return text
    elif format_type == "html":
        # 将Markdown转换为HTML（简化转换）
        html = content
        # 标题转换
        html = re.sub(r'### (.*?)(\n|$)', r'<h3>\1</h3>\2', html)
        html = re.sub(r'## (.*?)(\n|$)', r'<h2>\1</h2>\2', html)
        html = re.sub(r'# (.*?)(\n|$)', r'<h1>\1</h1>\2', html)
        # 粗体和斜体
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        # 链接
        html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html)
        # 代码块
        html = re.sub(r'```(.*?)\n(.*?)```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)
        # 行内代码
        html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
        # 段落
        html = re.sub(r'([^\n])\n([^\n])', r'\1<br>\2', html)
        return html
    
    return content

async def stream_response(generator, format_type="markdown"):
    """生成流式响应"""
    try:
        for chunk in generator:
            # 格式化每个块
            formatted_chunk = format_response_content(chunk, format_type)
            yield f"data: {json.dumps({'content': formatted_chunk})}\n\n"
    except Exception as e:
        logger.error(f"Stream response error: {str(e)}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

# 检索数据库中的内容
def retrieve_from_mysql(query: str, tables: List[str], max_results: int = 5) -> List[Dict]:
    """从MySQL中检索与查询相关的内容"""
    retrieved_items = []
    
    # 为每个表搜索相关内容
    for table in tables:
        if table == "wxapp_posts":
            # 使用全文检索提高搜索质量
            try:
                # 构建带权重的查询条件
                sql = f"""
                SELECT id, title, content, nick_name as author, post_type as type, 
                       DATE_FORMAT(create_time, '%Y-%m-%d %H:%i:%s') as create_time,
                       view_count, like_count, comment_count, tags,
                       (MATCH(title) AGAINST('{query}' IN NATURAL LANGUAGE MODE) * 3 +
                        MATCH(content) AGAINST('{query}' IN NATURAL LANGUAGE MODE)) as relevance_score
                FROM {table}
                WHERE (MATCH(title, content) AGAINST('{query}' IN NATURAL LANGUAGE MODE)
                       OR title LIKE '%{query}%' 
                       OR content LIKE '%{query}%')
                      AND status = 1 
                      AND is_deleted = 0
                ORDER BY relevance_score DESC, create_time DESC
                LIMIT {max_results}
                """
                
                # 尝试执行全文检索查询
                results = execute_custom_query(sql)
                
                # 如果全文检索失败或结果为空，回退到普通模糊查询
                if not results:
                    fallback_sql = f"""
                    SELECT id, title, content, nick_name as author, post_type as type, 
                           DATE_FORMAT(create_time, '%Y-%m-%d %H:%i:%s') as create_time,
                           view_count, like_count, comment_count, tags
                    FROM {table}
                    WHERE (title LIKE '%{query}%' OR content LIKE '%{query}%')
                          AND status = 1 
                          AND is_deleted = 0
                    ORDER BY 
                        CASE 
                            WHEN title LIKE '%{query}%' THEN 5
                            WHEN content LIKE '%{query}%' THEN 2
                            ELSE 1
                        END DESC,
                        create_time DESC
                    LIMIT {max_results}
                    """
                    results = execute_custom_query(fallback_sql)
            except Exception as e:
                # 如果发生错误（可能是全文索引不存在），使用基本查询
                logging.warning(f"全文检索查询失败，使用基本查询: {str(e)}")
                sql = f"""
                SELECT id, title, content, nick_name as author, post_type as type, 
                       DATE_FORMAT(create_time, '%Y-%m-%d %H:%i:%s') as create_time,
                       view_count, like_count, comment_count, tags
                FROM {table}
                WHERE (title LIKE '%{query}%' OR content LIKE '%{query}%')
                      AND status = 1 
                      AND is_deleted = 0
                ORDER BY 
                    CASE 
                        WHEN title LIKE '%{query}%' THEN 5
                        WHEN content LIKE '%{query}%' THEN 2
                        ELSE 1
                    END DESC,
                    create_time DESC
                LIMIT {max_results}
                """
                results = execute_custom_query(sql)
                
            for result in results:
                # 处理JSON字段
                if 'tags' in result and result['tags']:
                    try:
                        tags_data = json.loads(result['tags'])
                        # 提取标签文本构建标签文本
                        tag_names = [tag.get("name", "") for tag in tags_data if tag.get("name")]
                        tags_text = "标签: " + ", ".join(tag_names) + "\n" if tag_names else ""
                        result['tags'] = tags_text
                    except json.JSONDecodeError:
                        result['tags'] = ""
                else:
                    result['tags'] = ""
                
                # 计算相关度分数（如果未由全文索引提供）
                if 'relevance_score' not in result:
                    relevance_score = 0
                    if query.lower() in (result.get('title') or '').lower():
                        relevance_score += 3
                    if query.lower() in (result.get('content') or '').lower():
                        relevance_score += 1
                else:
                    relevance_score = result['relevance_score']
                    
                retrieved_items.append({
                    "type": result.get('type', '文章'),
                    "id": result.get('id', ''),
                    "title": result.get('title', ''),
                    "content": result.get('content', ''),
                    "author": result.get('author', ''),
                    "create_time": result.get('create_time', ''),
                    "view_count": result.get('view_count', 0),
                    "like_count": result.get('like_count', 0),
                    "comment_count": result.get('comment_count', 0),
                    "tags": result.get('tags', ''),
                    "relevance": relevance_score
                })
        
        elif table == "wxapp_comments":
            # 评论搜索优化
            sql = """
            SELECT c.id, c.post_id, c.content, c.nick_name as author, 
                  DATE_FORMAT(c.create_time, '%Y-%m-%d %H:%i:%s') as create_time,
                  p.title as post_title
            FROM wxapp_comments c
            LEFT JOIN wxapp_posts p ON c.post_id = p.id
            WHERE c.content LIKE '%{}%'
            AND c.is_deleted = 0
            ORDER BY 
                CASE 
                    WHEN c.content LIKE '%{}%' THEN 3
                    ELSE 1
                END DESC,
                c.create_time DESC
            LIMIT {}
            """.format(query, query, max_results)
            
            try:
                results = execute_custom_query(sql)
                for result in results:
                    # 计算相关度分数
                    relevance_score = 0
                    if query.lower() in (result.get('content') or '').lower():
                        relevance_score += 2
                        
                    retrieved_items.append({
                        "type": "评论",
                        "id": result.get('id', ''),
                        "post_id": result.get('post_id', ''),
                        "post_title": result.get('post_title', ''),
                        "content": result.get('content', ''),
                        "author": result.get('author', ''),
                        "create_time": result.get('create_time', ''),
                        "relevance": relevance_score
                    })
            except Exception as e:
                logging.error(f"查询评论表出错: {str(e)}")
        
        elif table == "wxapp_users":
            # 用户搜索优化
            sql = """
            SELECT id, openid, nick_name, avatar, bio, real_name,
                  DATE_FORMAT(create_time, '%Y-%m-%d %H:%i:%s') as create_time
            FROM wxapp_users
            WHERE nick_name LIKE '%{}%' OR real_name LIKE '%{}%' OR bio LIKE '%{}%'
            ORDER BY 
                CASE 
                    WHEN nick_name LIKE '%{}%' THEN 4
                    WHEN real_name LIKE '%{}%' THEN 3
                    WHEN bio LIKE '%{}%' THEN 2
                    ELSE 1
                END DESC
            LIMIT {}
            """.format(query, query, query, query, query, query, max_results)
            
            try:
                results = execute_custom_query(sql)
                for result in results:
                    # 计算相关度分数
                    relevance_score = 0
                    if query.lower() in (result.get('nick_name') or '').lower():
                        relevance_score += 3
                    if query.lower() in (result.get('real_name') or '').lower():
                        relevance_score += 2
                    if query.lower() in (result.get('bio') or '').lower():
                        relevance_score += 1
                        
                    retrieved_items.append({
                        "type": "用户",
                        "id": result.get('id', ''),
                        "nick_name": result.get('nick_name', ''),
                        "real_name": result.get('real_name', ''),
                        "bio": result.get('bio', ''),
                        "avatar": result.get('avatar', ''),
                        "create_time": result.get('create_time', ''),
                        "relevance": relevance_score
                    })
            except Exception as e:
                logging.error(f"查询用户表出错: {str(e)}")
        
        elif table in ["wechat_nku", "website_nku", "market_nku"]:
            # 处理其他平台数据
            table_type_map = {
                "wechat_nku": "微信公众号文章",
                "website_nku": "南开网站文章",
                "market_nku": "校园集市帖子"
            }
            
            platform_name = table_type_map.get(table, table)
            
            try:
                sql = f"""
                SELECT id, title, content, author, url, 
                       DATE_FORMAT(create_time, '%Y-%m-%d %H:%i:%s') as create_time,
                       platform
                FROM {table}
                WHERE (title LIKE '%{query}%' OR content LIKE '%{query}%')
                ORDER BY 
                    CASE 
                        WHEN title LIKE '%{query}%' THEN 3
                        WHEN content LIKE '%{query}%' THEN 1
                        ELSE 0
                    END DESC,
                    create_time DESC
                LIMIT {max_results}
                """
                results = execute_custom_query(sql)
                
                for result in results:
                    # 计算相关度分数
                    relevance_score = 0
                    if query.lower() in (result.get('title') or '').lower():
                        relevance_score += 3
                    if query.lower() in (result.get('content') or '').lower():
                        relevance_score += 1
                        
                    retrieved_items.append({
                        "type": platform_name,
                        "id": result.get('id', ''),
                        "title": result.get('title', ''),
                        "content": result.get('content', ''),
                        "author": result.get('author', ''),
                        "create_time": result.get('create_time', ''),
                        "url": result.get('url', ''),
                        "platform": result.get('platform', platform_name),
                        "relevance": relevance_score
                    })
            except Exception as e:
                logging.error(f"查询{platform_name}表出错: {str(e)}")
    
    # 按相关度和创建时间排序
    retrieved_items.sort(key=lambda x: (x.get('relevance', 0), x.get('create_time', '')), reverse=True)
    
    # 限制结果数量
    return retrieved_items[:max_results]

# 构建RAG上下文
def build_rag_context(query, retrieved_items):
    """构建RAG上下文字符串，以便于生成Wiki风格回答"""
    if not retrieved_items:
        return f"未找到与\"{query}\"相关的信息。请尝试使用其他关键词或回答用户这可能是因为什么原因。"
    
    # 开始构建上下文
    context_parts = [f"以下是与\"{query}\"相关的信息：\n"]
    
    # 为检索到的结果添加编号引用
    for i, item in enumerate(retrieved_items, 1):
        context_parts.append(f"\n## [引用{i}] ")
        
        if "title" in item and item["title"]:
            context_parts.append(f"{item['title']}\n")
        else:
            context_parts.append(f"{item['type']}内容\n")
        
        # 根据不同类型添加详细信息
        if item["type"] in ["文章", "帖子"]:
            author_info = f"作者: {item['author']} | 时间: {item['create_time']}\n"
            if "view_count" in item:
                author_info += f"浏览量: {item['view_count']} | 点赞量: {item['like_count']} | 评论量: {item['comment_count']}\n"
            context_parts.append(author_info)
            
            if item.get("tags"):
                context_parts.append(f"{item['tags']}\n")
            
            # 处理内容，对长内容进行摘要
            content = item.get("content", "")
            if len(content) > 1000:
                context_parts.append(f"内容摘要: {content[:1000]}... (内容较长，已截断)\n\n")
            else:
                context_parts.append(f"内容: {content}\n\n")
        
        elif item["type"] == "评论":
            context_parts.append(f"作者: {item['author']} | 时间: {item['create_time']}\n")
            context_parts.append(f"评论于帖子: {item.get('post_title', '未知帖子')}\n")
            context_parts.append(f"内容: {item.get('content', '')}\n\n")
        
        elif item["type"] == "用户":
            context_parts.append(f"用户名: {item.get('nick_name', '')}")
            if item.get('real_name'):
                context_parts.append(f" | 真实姓名: {item['real_name']}")
            context_parts.append(f"\n个人简介: {item.get('bio', '暂无简介')}\n\n")
        
        elif item["type"] in ["微信公众号文章", "南开网站文章", "校园集市帖子"]:
            context_parts.append(f"作者: {item['author']} | 平台: {item.get('platform', item['type'])} | 时间: {item['create_time']}\n")
            
            # 处理内容，对长内容进行摘要
            content = item.get("content", "")
            if len(content) > 1000:
                context_parts.append(f"内容摘要: {content[:1000]}... (内容较长，已截断)\n")
            else:
                context_parts.append(f"内容: {content}\n")
                
            if "url" in item and item["url"]:
                context_parts.append(f"链接: {item['url']}\n\n")
    
    # 添加如何引用来源的说明
    context_parts.append("\n## 引用指南\n")
    context_parts.append("在回答中，请用[引用X]格式（如[引用1]、[引用2]）标注信息的来源。\n")
    context_parts.append("如果多个来源支持同一观点，可以组合引用，例如：[引用1][引用3]。\n")
    context_parts.append("对于没有信息支持的内容，请明确说明：'根据现有信息无法回答'。\n")
    
    return "".join(context_parts)

# API端点
@router.post("/chat")
@handle_api_errors("Agent对话")
async def chat_with_agent(
    request: ChatRequest,
    api_logger=Depends(get_api_logger)
):
    """与Agent进行对话"""
    # 延迟导入CozeAgent，避免循环导入
    try:
        from core.agent.coze.coze_agent import CozeAgent
        from core.bridge.context import Context, ContextType
        
        # 创建CozeAgent实例
        agent = CozeAgent()
        
        # 创建上下文对象
        context = Context()
        context.type = ContextType.TEXT
        context["session_id"] = "api_session_" + str(hash(request.query))
        context["stream"] = request.stream  # 添加stream参数
        context["format"] = request.format  # 添加format参数
        context["openid"] = request.openid  # 添加openid参数
        
        api_logger.debug(f"处理聊天请求：query={request.query}, openid={request.openid}")
        
        # 发送请求并获取回复
        reply = agent.reply(request.query, context)
        
        if reply is None:
            raise HTTPException(status_code=500, detail="Agent响应失败")
        
        # 如果是流式响应
        if request.stream and reply.type == ReplyType.STREAM:
            return StreamingResponse(
                stream_response(reply.content, request.format),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        
        # 非流式响应
        if reply.type != ReplyType.TEXT:
            raise HTTPException(status_code=500, detail="Agent响应类型错误")
        
        # 格式化内容    
        formatted_content = format_response_content(reply.content, request.format)
        
        return {
            "response": formatted_content,
            "sources": [],  # 目前CozeAgent不提供知识来源
            "format": request.format
        }
    except Exception as e:
        logger.error(f"Chat with agent error: {str(e)}")
        raise HTTPException(status_code=500, detail="无法与Agent对话")

@router.post("/search", response_model=List[Dict[str, Any]])
@handle_api_errors("知识搜索")
async def search_knowledge(
    request: SearchRequest,
    api_logger=Depends(get_api_logger)
):
    """搜索知识库"""
    # TODO: 实现知识搜索逻辑
    results = []
    return results

@router.post("/rag", response_model=Dict[str, Any])
@handle_api_errors("RAG检索增强生成")
async def rag_generation(
    request: RAGRequest,
    api_logger=Depends(get_api_logger)
):
    """
    检索增强生成（RAG）接口，从MySQL数据中检索相关内容，然后使用智能体生成回答
    """
    start_time = time.time()
    
    try:
        from core.agent.coze.coze_agent import CozeAgent
        from core.bridge.context import Context, ContextType
        
        # 记录请求详情
        api_logger.debug(f"处理RAG请求：query={request.query}, tables={request.tables}, openid={request.openid}")
        
        # 从MySQL中检索相关内容
        retrieved_items = retrieve_from_mysql(
            query=request.query,
            tables=request.tables,
            max_results=request.max_results
        )
        
        # 构建RAG上下文
        context_str = build_rag_context(request.query, retrieved_items)
        
        # 构建提示词
        prompt = f"""
你是南开大学知识助手，基于南开Wiki知识库回答用户问题。
根据以下检索到的信息，请用中文回答用户问题"{request.query}"。

要求：
1. 用简洁、专业、友好的语气回答
2. 如实引用来源，使用[引用X]格式标注信息来源
3. 如果提供的信息不足，诚实说明，但尽量基于检索内容给出有用回应
4. 不要编造不在检索内容中的信息
5. 结构清晰，使用适当的Markdown格式美化回答
6. 在回答后，生成3个相关的后续问题建议，以"你可能还想了解："开头

检索到的信息:
{context_str}

回答:
"""
        
        # 创建CozeAgent实例
        agent = CozeAgent()
        
        # 创建上下文对象
        context = Context()
        context.type = ContextType.TEXT
        context["session_id"] = "rag_session_" + str(hash(request.query))
        context["stream"] = request.stream
        context["format"] = request.format
        context["openid"] = request.openid
        
        # 发送请求并获取回复
        reply = agent.reply(prompt, context)
        
        if reply is None:
            raise HTTPException(status_code=500, detail="Agent响应失败")
        
        # 如果是流式响应
        if request.stream and reply.type == ReplyType.STREAM:
            return StreamingResponse(
                stream_response(reply.content, request.format),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        
        # 非流式响应
        if reply.type != ReplyType.TEXT:
            raise HTTPException(status_code=500, detail="Agent响应类型错误")
        
        # 格式化内容
        formatted_content = format_response_content(reply.content, request.format)
        
        # 构建简化的资源列表
        sources = []
        for i, item in enumerate(retrieved_items, 1):
            source = {
                "id": str(i),
                "type": item["type"],
                "title": item.get("title", ""),
                "author": item.get("author", "")
            }
            
            # 根据不同类型添加特定字段
            if item["type"] in ["微信公众号文章", "南开网站文章", "校园集市帖子"]:
                source["url"] = item.get("url", "")
                source["platform"] = item.get("platform", "")
            
            sources.append(source)
        
        # 尝试从回答中提取建议的问题
        suggested_questions = []
        try:
            # 查找"你可能还想了解："部分
            suggested_section = re.search(r"你可能还想了解：([\s\S]+)$", formatted_content)
            if suggested_section:
                # 提取建议问题部分
                suggestions_text = suggested_section.group(1).strip()
                # 分割成单独的问题（匹配数字+点、-或*开头的行）
                questions = re.findall(r'(?:^\d+\.|\-|\*)\s*(.*?)(?:\n|$)', suggestions_text, re.MULTILINE)
                if questions:
                    suggested_questions = [q.strip() for q in questions if q.strip()]
                    # 如果没有匹配到格式化的问题，尝试按行分割
                    if not suggested_questions:
                        suggested_questions = [q.strip() for q in suggestions_text.split('\n') if q.strip()]
        except Exception as e:
            api_logger.warning(f"提取建议问题失败: {str(e)}")
        
        # 确保最多有3个建议问题
        suggested_questions = suggested_questions[:3]
        
        # 如果没有提取到建议问题，使用默认问题
        if not suggested_questions and retrieved_items:
            for item in retrieved_items[:3]:
                if "title" in item and item["title"]:
                    suggested_questions.append(f"能详细介绍一下{item['title']}吗？")
        
        # 计算响应时间
        response_time = time.time() - start_time
        
        # 构建响应
        response = {
            "response": formatted_content,
            "sources": sources,
            "suggested_questions": suggested_questions,
            "format": request.format,
            "retrieved_count": len(retrieved_items),
            "response_time": round(response_time, 3)
        }
        
        return response
        
    except Exception as e:
        api_logger.error(f"RAG生成错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAG生成失败: {str(e)}")

@router.get("/status")
@handle_api_errors("获取Agent状态")
async def get_agent_status(
    api_logger=Depends(get_api_logger)
):
    """获取Agent状态"""
    return {
        "status": "running",
        "version": "1.0.0",
        "capabilities": ["chat", "search", "rag"],
        "formats": ["markdown", "text", "html"]
    }

# 标准上下文模型和RAG相关模型
class RAGContext(BaseModel):
    """RAG处理的标准上下文模型"""
    original_query: str = Field(..., description="用户原始查询")
    rewritten_query: str = Field("", description="改写后的查询")
    retrieved_items: List[Dict] = Field(default=[], description="检索到的项目")
    context_str: str = Field("", description="用于生成的上下文文本")
    sources: List[Dict] = Field(default=[], description="引用的知识来源")
    response: str = Field("", description="生成的回答")
    response_time: float = Field(0.0, description="响应时间(秒)")
    query_bot_id: str = Field("", description="查询改写机器人ID")
    flash_bot_id: str = Field("", description="回答生成机器人ID")
    format: str = Field("markdown", description="响应格式")
    
    class Config:
        arbitrary_types_allowed = True

class EnhancedRAGRequest(BaseModel):
    """增强版RAG请求模型"""
    query: str = Field(..., description="用户查询")
    tables: List[str] = Field(["wxapp_posts"], description="要检索的表名列表")
    max_results: int = Field(5, description="每个表返回的最大结果数")
    stream: bool = Field(False, description="是否流式返回")
    format: str = Field("markdown", description="回复格式: markdown|text|html")
    openid: Optional[str] = None
    query_bot_id: Optional[str] = Field("rewriter", description="查询改写机器人ID")
    flash_bot_id: Optional[str] = Field("flash", description="回答生成机器人ID")
    
    @validator("tables")
    def validate_tables(cls, tables):
        """验证表名"""
        valid_tables = ["wxapp_posts", "wxapp_comments", "wxapp_users", "wechat_nku", "website_nku", "market_nku"]
        for table in tables:
            if table not in valid_tables:
                raise ValueError(f"不支持的表: {table}，有效的表为: {', '.join(valid_tables)}")
        return tables
    
    @validator("format")
    def validate_format(cls, format_type):
        """验证格式"""
        valid_formats = ["markdown", "text", "html"]
        if format_type not in valid_formats:
            raise ValueError(f"不支持的格式: {format_type}，有效的格式为: {', '.join(valid_formats)}")
        return format_type

# 查询改写函数
async def rewrite_query(query: str, bot_id: str, openid: str = None) -> str:
    """使用指定的bot_id改写查询"""
    try:
        # 创建Agent实例
        agent = AgentFactory.get_agent(bot_id)
        if not agent:
            logger.warning(f"找不到指定的查询改写Agent: {bot_id}，使用默认Agent")
            agent = CozeAgent()
        
        # 创建上下文对象
        context = Context()
        context.type = ContextType.TEXT
        context["session_id"] = f"query_rewrite_{openid}_{hash(query)}"
        
        # 构建提示词
        prompt = f"""
你是一个专业的查询改写专家。请分析用户的原始查询，将其改写为更适合检索系统的形式。
保留原始查询的核心语义，但添加必要的关键词以提高检索质量。

原始查询: {query}

改写后的查询:"""
        
        # 发送请求并获取回复
        reply = agent.reply(prompt, context)
        
        if reply and reply.type == ReplyType.TEXT and reply.content:
            # 清理回复，获取实际的查询
            rewritten = reply.content.strip()
            # 移除可能的引号、多余的空格和换行
            rewritten = re.sub(r'["""\'\']', '', rewritten)
            rewritten = re.sub(r'\s+', ' ', rewritten)
            
            logger.debug(f"查询改写: '{query}' -> '{rewritten}'")
            return rewritten
        
        # 如果改写失败，返回原始查询
        logger.warning(f"查询改写失败，使用原始查询: {query}")
        return query
    
    except Exception as e:
        logger.error(f"查询改写异常: {str(e)}")
        return query  # 出错时返回原始查询

# 用检索到的内容生成回答
async def generate_answer(rag_context: RAGContext) -> str:
    """使用检索到的内容生成回答"""
    try:
        # 创建Agent实例
        agent = AgentFactory.get_agent(rag_context.flash_bot_id)
        if not agent:
            logger.warning(f"找不到指定的生成Agent: {rag_context.flash_bot_id}，使用默认Agent")
            agent = CozeAgent()
        
        # 创建上下文对象
        context = Context()
        context.type = ContextType.TEXT
        session_id = f"rag_flash_{hash(rag_context.original_query)}"
        context["session_id"] = session_id
        context["format"] = rag_context.format
        
        # 构建提示词
        prompt = f"""
基于以下检索到的信息，回答用户的问题"{rag_context.original_query}"。
如果提供的信息不足以回答用户的问题，请如实说明，但尽量基于检索到的内容给出有用的回应。
不要编造不在检索内容中的信息。请在回答后标明信息来源的编号，格式为[来源1][来源2]等。

检索到的信息:
{rag_context.context_str}

问题: {rag_context.original_query}

回答:
"""
        
        # 发送请求并获取回复
        reply = agent.reply(prompt, context)
        
        if reply and reply.type == ReplyType.TEXT and reply.content:
            formatted_content = format_response_content(reply.content, rag_context.format)
            return formatted_content
        
        # 如果生成失败，返回默认回复
        logger.warning(f"回答生成失败，返回默认回复")
        return "抱歉，我无法基于检索到的信息回答这个问题。请尝试用其他方式提问或查询其他信息。"
    
    except Exception as e:
        logger.error(f"生成回答异常: {str(e)}")
        return f"生成回答时发生错误: {str(e)}"

@router.post("/rag2", response_model=Dict[str, Any])
@handle_api_errors("增强版RAG检索增强生成")
async def enhanced_rag_generation(
    request: EnhancedRAGRequest,
    api_logger=Depends(get_api_logger)
):
    """
    增强版检索增强生成（RAG）接口，使用查询改写和生成两阶段处理
    """
    start_time = time.time()
    
    try:
        # 创建RAG上下文
        rag_context = RAGContext(
            original_query=request.query,
            query_bot_id=request.query_bot_id,
            flash_bot_id=request.flash_bot_id,
            format=request.format
        )
        
        # 记录请求详情
        api_logger.debug(f"处理增强RAG请求：query={request.query}, tables={request.tables}, openid={request.openid}")
        
        # 第一阶段：查询改写
        rag_context.rewritten_query = await rewrite_query(
            query=request.query,
            bot_id=request.query_bot_id, 
            openid=request.openid
        )
        
        # 第二阶段：检索
        rag_context.retrieved_items = retrieve_from_mysql(
            query=rag_context.rewritten_query,
            tables=request.tables,
            max_results=request.max_results
        )
        
        # 构建上下文字符串
        rag_context.context_str = build_rag_context(rag_context.rewritten_query, rag_context.retrieved_items)
        
        # 提取来源信息
        if rag_context.retrieved_items:
            for i, item in enumerate(rag_context.retrieved_items, 1):
                source = {
                    "id": str(i),
                    "type": item["type"],
                    "title": item.get("title", ""),
                    "item_id": item["id"],
                    "author": item.get("author", "")
                }
                
                if item["type"] in ["微信公众号文章", "南开网站文章", "校园集市帖子"]:
                    source["url"] = item.get("url", "")
                    source["platform"] = item.get("platform", "")
                
                rag_context.sources.append(source)
        
        # 第三阶段：生成回答，使用更新后的自定义提示词
        prompt = f"""
你是南开大学知识助手，基于南开Wiki知识库回答用户问题。
根据以下检索到的信息，请用中文回答用户问题"{rag_context.original_query}"。

要求：
1. 用简洁、专业、友好的语气回答
2. 如实引用来源，使用[引用X]格式标注信息来源
3. 如果提供的信息不足，诚实说明，但尽量基于检索内容给出有用回应
4. 不要编造不在检索内容中的信息
5. 结构清晰，使用适当的Markdown格式美化回答
6. 在回答后，生成3个相关的后续问题建议，以"你可能还想了解："开头

检索到的信息:
{rag_context.context_str}

回答:
"""
        
        # 创建Agent和上下文
        agent = AgentFactory.get_agent(rag_context.flash_bot_id)
        if not agent:
            agent = CozeAgent()
            
        context = Context()
        context.type = ContextType.TEXT
        context["session_id"] = f"rag2_session_{hash(request.query)}"
        context["format"] = request.format
        context["stream"] = request.stream
        
        # 发送请求并获取回复
        reply = agent.reply(prompt, context)
        
        if reply is None:
            raise HTTPException(status_code=500, detail="Agent响应失败")
            
        # 如果是流式响应
        if request.stream and reply.type == ReplyType.STREAM:
            return StreamingResponse(
                stream_response(reply.content, request.format),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        
        # 非流式响应
        if reply.type != ReplyType.TEXT:
            raise HTTPException(status_code=500, detail="Agent响应类型错误")
            
        # 格式化内容
        rag_context.response = format_response_content(reply.content, request.format)
        
        # 记录响应时间
        rag_context.response_time = time.time() - start_time
        
        # 尝试从回答中提取建议的问题
        suggested_questions = []
        try:
            # 查找"你可能还想了解："部分
            suggested_section = re.search(r"你可能还想了解：([\s\S]+)$", rag_context.response)
            if suggested_section:
                # 提取建议问题部分
                suggestions_text = suggested_section.group(1).strip()
                # 分割成单独的问题（匹配数字+点、-或*开头的行）
                questions = re.findall(r'(?:^\d+\.|\-|\*)\s*(.*?)(?:\n|$)', suggestions_text, re.MULTILINE)
                if questions:
                    suggested_questions = [q.strip() for q in questions if q.strip()]
                    # 如果没有匹配到格式化的问题，尝试按行分割
                    if not suggested_questions:
                        suggested_questions = [q.strip() for q in suggestions_text.split('\n') if q.strip()]
        except Exception as e:
            api_logger.warning(f"提取建议问题失败: {str(e)}")
        
        # 确保最多有3个建议问题
        suggested_questions = suggested_questions[:3]
        
        # 如果没有提取到建议问题，使用默认问题
        if not suggested_questions and rag_context.retrieved_items:
            for item in rag_context.retrieved_items[:3]:
                if "title" in item and item["title"]:
                    suggested_questions.append(f"能详细介绍一下{item['title']}吗？")
        
        # 构建响应
        response = {
            "response": rag_context.response,
            "sources": rag_context.sources,
            "suggested_questions": suggested_questions,
            "format": request.format,
            "retrieved_count": len(rag_context.retrieved_items),
            "original_query": rag_context.original_query,
            "rewritten_query": rag_context.rewritten_query,
            "response_time": round(rag_context.response_time, 3)
        }
        
        return response
        
    except Exception as e:
        api_logger.error(f"增强RAG生成错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"增强RAG生成失败: {str(e)}") 