"""
智能体聊天API接口
处理与智能体的对话、RAG查询等功能
"""
import json
import traceback
import asyncio
from fastapi import APIRouter
from api.models.common import Response, Request, validate_params
from fastapi.responses import StreamingResponse
from api.common.utils import format_response_content
from core.utils.logger import register_logger

router = APIRouter()
logger = register_logger('api.routes.agent.chat')

@router.post("/chat")
async def chat(
    request: Request
):
    """智能体对话接口"""
    req_data = await request.json()
    required_params = ["query", "openid"]
    error_response = validate_params(req_data, required_params)
    if(error_response):
        return error_response
    try:
        query = req_data.get("query")
        bot_tag = req_data.get("bot_tag", "general") # 使用general代替default
        stream = req_data.get("stream", False)
        format = req_data.get("format", "markdown")

        # 打印接收到的参数
        logger.debug(f"Chat API请求: query={query}, bot_tag={bot_tag}, stream={stream}, format={format}")

        # 模拟Agent回复，避免调用可能未配置的CozeAgent
        mock_response = f"这是来自模拟Agent({bot_tag})的回复:\n\n{query}\n\n这个问题的答案是...模拟回复"
        
        if stream:
            async def sse_generator():
                chunks = mock_response.split()
                for chunk in chunks:
                    if chunk:
                        yield f"data: {json.dumps({'content': chunk + ' '})}\n\n"
                        await asyncio.sleep(0.1)
                yield f"data: {json.dumps({'type': 'done'})}\n\n"

            return StreamingResponse(sse_generator(), media_type="text/event-stream")

        # 返回模拟回复
        return Response.success(data={
            "message": mock_response,
            "format": format,
            "usage": {"prompt_tokens": len(query), "completion_tokens": len(mock_response), "total_tokens": len(query) + len(mock_response)},
            "finish_reason": "stop"
        }, details={"message": "模拟对话成功"})
        
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"Chat请求处理失败: {str(e)}\n{error_detail}")
        return Response.error(details={"message": f"请求处理失败: {str(e)}"})

@router.get("/status")
async def get_agent_status():
    """获取agent状态"""
    return Response.success(data={"status": "ok"},details={"message":"获取agent状态成功"}) 