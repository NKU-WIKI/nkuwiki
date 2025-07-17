"""
数据库MCP接口
提供数据库查询工具供Cursor Claude 访问
"""
import json
from fastapi import Request, Depends, HTTPException, Response
from fastapi.responses import JSONResponse, StreamingResponse
import asyncio

from api import mcp_router
from api.common import get_api_logger_dep
from etl.load.db_core import execute_custom_query, validate_table_name, query_records, get_all_tables
from core.utils.logger import register_logger

# 创建日志记录器
mcp_logger = register_logger("api.mcp.db")

# MCP清单定义
MANIFEST = {
    "type": "manifest",
    "tools": [
        {
            "name": "execute_sql",
            "description": "执行SQL查询并返回结果，仅支持SELECT语句",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL查询语句(仅SELECT)"
                    },
                    "params": {
                        "type": "array",
                        "description": "查询参数列表",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "required": ["sql"]
            }
        },
        {
            "name": "show_tables",
            "description": "显示数据库中所有表",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "describe_table",
            "description": "显示表结构",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "表名"
                    }
                },
                "required": ["table_name"]
            }
        },
        {
            "name": "query_table",
            "description": "查询指定表的数据",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "表名"
                    },
                    "conditions": {
                        "type": "object",
                        "description": "查询条件，字段名和值的映射"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量限制，默认20"
                    },
                    "offset": {
                        "type": "integer",
                        "description": "分页偏移量，默认0"
                    },
                    "order_by": {
                        "type": "string",
                        "description": "排序方式，例如'id DESC'"
                    }
                },
                "required": ["table_name"]
            }
        }
    ]
}

# 生成SSE事件
def format_sse(event, data):
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"

async def sse_generator():
    # 发送服务器信息事件
    yield format_sse("server_info", {
        "name": "nkuwiki-db-mcp",
        "version": "1.0.0",
        "capabilities": {
            "methods": ["execute_sql", "show_tables", "describe_table", "query_table"],
            "streaming": True,
            "tools": True,
        },
        "status": "ready",
        "protocol_version": "2023-07-01"
    })
    
    # 发送会话创建事件
    import uuid
    session_id = str(uuid.uuid4())
    yield format_sse("session_created", {"session_id": session_id})
    
    # 发送工具清单
    yield format_sse("manifest", MANIFEST)
    
    # 发送心跳事件以保持连接
    while True:
        import time
        yield format_sse("heartbeat", {"timestamp": time.time()})
        await asyncio.sleep(15)  # 15秒发送一次心跳

@mcp_router.get("")
async def get_manifest():
    """返回MCP清单，使用SSE格式"""
    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@mcp_router.post("/jsonrpc")
async def handle_jsonrpc(
    request: Request,
    api_logger=Depends(get_api_logger_dep)
):
    """处理JSON-RPC调用"""
    try:
        data = await request.json()
        api_logger.debug(f"收到JSON-RPC请求: {json.dumps(data)}")
        
        response = {
            "jsonrpc": "2.0",
            "id": data.get("id", None)
        }
        
        method = data.get("method", "")
        params = data.get("params", {})
        
        if method == "execute_sql":
            sql = params.get("sql", "")
            if not sql.strip().upper().startswith("SELECT"):
                response["error"] = {"code": -32600, "message": "安全限制：只允许SELECT查询"}
            else:
                db_params = params.get("params", [])
                try:
                    result = await execute_custom_query(sql, db_params)
                    response["result"] = {"result": result, "row_count": len(result) if result else 0, "sql": sql}
                except Exception as e:
                    api_logger.error(f"执行SQL错误: {str(e)}")
                    response["error"] = {"code": -32603, "message": str(e)}
        elif method == "show_tables":
            try:
                tables = await get_all_tables()
                response["result"] = {"tables": tables, "count": len(tables)}
            except Exception as e:
                api_logger.error(f"获取表列表错误: {str(e)}")
                response["error"] = {"code": -32603, "message": str(e)}
        elif method == "describe_table":
            table_name = params.get("table_name", "")
            if not await validate_table_name(table_name):
                response["error"] = {"code": -32602, "message": f"非法表名: {table_name}"}
            else:
                try:
                    result = await execute_custom_query(f"DESCRIBE {table_name}")
                    response["result"] = {"structure": result, "table": table_name}
                except Exception as e:
                    api_logger.error(f"获取表结构错误: {str(e)}")
                    response["error"] = {"code": -32603, "message": str(e)}
        elif method == "query_table":
            table_name = params.get("table_name", "")
            if not await validate_table_name(table_name):
                response["error"] = {"code": -32602, "message": f"非法表名: {table_name}"}
            else:
                try:
                    conditions = params.get("conditions", {})
                    limit = int(params.get("limit", 20))
                    offset = int(params.get("offset", 0))
                    order_by = params.get("order_by", "id DESC")
                    
                    result_dict = await query_records(
                        table_name=table_name,
                        conditions=conditions,
                        order_by=order_by,
                        limit=limit,
                        offset=offset
                    )
                    
                    result = result_dict.get('data', [])
                    response["result"] = {"result": result, "row_count": len(result) if result else 0, "table": table_name, "limit": limit, "offset": offset}
                except Exception as e:
                    api_logger.error(f"查询表数据错误: {str(e)}")
                    response["error"] = {"code": -32603, "message": str(e)}
        else:
            response["error"] = {"code": -32601, "message": "方法未找到"}

        return JSONResponse(response)
    except Exception as e:
        api_logger.error(f"处理JSON-RPC请求失败: {str(e)}")
        return JSONResponse({"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}, status_code=500)

# 保留旧版工具调用接口以保持兼容性
@mcp_router.post("/tool")
async def handle_tool_call(
    request: Request,
    api_logger=Depends(get_api_logger_dep)
):
    """处理工具调用请求（旧版接口）"""
    try:
        data = await request.json()
        tool_name = data.get("tool", "")
        params = data.get("parameters", {})
        
        api_logger.debug(f"接收到工具调用请求: {tool_name}, 参数: {json.dumps(params)}")
        
        if tool_name == "execute_sql":
            sql = params.get("sql", "")
            # 安全检查：只允许SELECT查询
            if not sql.strip().upper().startswith("SELECT"):
                return JSONResponse(
                    status_code=400,
                    content={"error": "安全限制：只允许SELECT查询"}
                )
            
            sql_params = params.get("params", [])
            try:
                result = execute_query(sql, sql_params)
                return JSONResponse(content={
                    "result": result,
                    "row_count": len(result) if result else 0
                })
            except Exception as e:
                api_logger.error(f"执行SQL错误: {str(e)}")
                return JSONResponse(
                    status_code=500,
                    content={"error": str(e)}
                )
                
        elif tool_name == "show_tables":
            try:
                tables = get_all_tables()
                return JSONResponse(content={
                    "tables": tables,
                    "count": len(tables)
                })
            except Exception as e:
                api_logger.error(f"获取表列表错误: {str(e)}")
                return JSONResponse(
                    status_code=500,
                    content={"error": str(e)}
                )
                
        elif tool_name == "describe_table":
            table_name = params.get("table_name", "")
            if not validate_table_name(table_name):
                return JSONResponse(
                    status_code=400,
                    content={"error": f"非法表名: {table_name}"}
                )
            
            try:
                result = execute_query(f"DESCRIBE {table_name}")
                return JSONResponse(content={
                    "structure": result,
                    "table": table_name
                })
            except Exception as e:
                api_logger.error(f"获取表结构错误: {str(e)}")
                return JSONResponse(
                    status_code=500,
                    content={"error": str(e)}
                )
                
        elif tool_name == "query_table":
            table_name = params.get("table_name", "")
            if not validate_table_name(table_name):
                return JSONResponse(
                    status_code=400,
                    content={"error": f"非法表名: {table_name}"}
                )
            
            try:
                conditions = params.get("conditions", {})
                limit = int(params.get("limit", 20))
                offset = int(params.get("offset", 0))
                order_by = params.get("order_by", "id DESC")
                
                result = query_records(
                    table_name=table_name,
                    conditions=conditions,
                    order_by=order_by,
                    limit=limit,
                    offset=offset
                )
                
                return JSONResponse(content={
                    "result": result,
                    "row_count": len(result) if result else 0,
                    "table": table_name,
                    "limit": limit,
                    "offset": offset
                })
            except Exception as e:
                api_logger.error(f"查询表数据错误: {str(e)}")
                return JSONResponse(
                    status_code=500,
                    content={"error": str(e)}
                )
        else:
            return JSONResponse(
                status_code=400,
                content={"error": f"未知工具: {tool_name}"}
            )
            
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={"error": "无效的JSON请求"}
        )
    except Exception as e:
        mcp_logger.error(f"处理工具调用请求错误: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        ) 