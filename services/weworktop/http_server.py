"""
企业微信自建应用HTTP服务器
"""
import json
import asyncio
from fastapi import FastAPI, Request, Depends
from fastapi.responses import PlainTextResponse
import uvicorn
from core.utils.logger import register_logger

logger = register_logger("services.weworktop.http")

class WeWorkTopServer:
    """企业微信自建应用HTTP服务器"""
    
    def __init__(self, port, token, aes_key, channel):
        """
        初始化服务器
        
        参数:
        - port: 监听端口
        - token: 企业微信校验Token
        - aes_key: 消息加解密密钥
        - channel: 消息通道实例
        """
        self.port = port
        self.token = token
        self.aes_key = aes_key
        self.channel = channel
        self.app = FastAPI()
        
        # 注册路由
        self._register_routes()
    
    def _register_routes(self):
        """注册路由"""
        @self.app.post("/wework_callback")
        async def wework_callback(request: Request):
            """企业微信回调接口"""
            try:
                # 获取请求体
                body = await request.body()
                body_str = body.decode('utf-8')
                
                # 解析JSON
                msg_data = json.loads(body_str)
                logger.debug(f"收到企业微信回调: {msg_data}")
                
                # 处理消息
                loop = asyncio.get_event_loop()
                loop.create_task(self.channel.handle_message(msg_data))
                
                # 返回成功响应
                return PlainTextResponse("success")
            except Exception as e:
                logger.error(f"处理企业微信回调异常: {str(e)}")
                return PlainTextResponse("success")  # 即使出错也返回success，避免企业微信重试
                
        @self.app.get("/wework_callback")
        async def wework_verify(request: Request):
            """企业微信服务器验证接口"""
            try:
                # 获取请求参数
                msg_signature = request.query_params.get("msg_signature", "")
                timestamp = request.query_params.get("timestamp", "")
                nonce = request.query_params.get("nonce", "")
                echostr = request.query_params.get("echostr", "")
                
                logger.info(f"企业微信服务器验证: {msg_signature}, {timestamp}, {nonce}")
                
                # TODO: 实现真正的签名验证逻辑
                # 现在简单返回echostr完成验证
                return PlainTextResponse(echostr)
            except Exception as e:
                logger.error(f"企业微信服务器验证异常: {str(e)}")
                return PlainTextResponse("fail")
    
    def run(self):
        """运行服务器"""
        uvicorn.run(
            self.app, 
            host="0.0.0.0", 
            port=self.port,
            log_level="error"  # 使用loguru记录日志，关闭uvicorn的默认日志
        ) 