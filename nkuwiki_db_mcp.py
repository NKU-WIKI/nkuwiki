#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
南开Wiki数据库MCP服务器
为Cursor提供数据库查询能力
"""
import sys
import json
import os
from typing import Dict, List, Any, Optional, Union

# 添加项目根目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

try:
    from etl.load.db_core import execute_query, validate_table_name, query_records
    from core.utils.logger import register_logger
except ImportError:
    def execute_query(sql, params=None, fetch=True):
        return [{"error": "无法导入项目模块，请检查PYTHONPATH"}]
    
    def validate_table_name(table_name):
        import re
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name))
    
    def query_records(table_name, conditions=None, order_by=None, limit=1000, offset=0):
        return [{"error": "无法导入项目模块，请检查PYTHONPATH"}]
    
    def register_logger(name):
        import logging
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        return logger

# 创建日志记录器
mcp_logger = register_logger("cursor.mcp.db")

def main():
    """主函数，处理MCP协议请求"""
    # 输出MCP清单
    manifest = {
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
    
    try:
        print(json.dumps(manifest), flush=True)
        mcp_logger.debug("MCP服务器启动成功，已发送清单")
    except Exception as e:
        mcp_logger.error(f"发送清单失败: {str(e)}")
        sys.exit(1)
    
    # 读取并处理请求
    for line in sys.stdin:
        try:
            request = json.loads(line)
            
            if request["type"] == "tool_call":
                call_id = request["id"]
                tool_name = request["tool"]["name"]
                args = request["tool"]["parameters"]
                
                mcp_logger.debug(f"收到工具调用: {tool_name}, 参数: {json.dumps(args)}")
                
                response = {"id": call_id, "type": "tool_response"}
                
                if tool_name == "execute_sql":
                    sql = args.get("sql", "")
                    # 安全检查：只允许SELECT查询
                    if not sql.strip().upper().startswith("SELECT"):
                        response["content"] = {"error": "安全限制：只允许SELECT查询"}
                    else:
                        params = args.get("params", [])
                        try:
                            result = execute_query(sql, params)
                            response["content"] = {
                                "result": result, 
                                "row_count": len(result) if result else 0,
                                "sql": sql
                            }
                        except Exception as e:
                            mcp_logger.error(f"执行SQL错误: {str(e)}")
                            response["content"] = {"error": str(e)}
                
                elif tool_name == "show_tables":
                    try:
                        result = execute_query("SHOW TABLES")
                        tables = [list(row.values())[0] for row in result]
                        response["content"] = {"tables": tables, "count": len(tables)}
                    except Exception as e:
                        mcp_logger.error(f"获取表列表错误: {str(e)}")
                        response["content"] = {"error": str(e)}
                
                elif tool_name == "describe_table":
                    table_name = args.get("table_name", "")
                    if not validate_table_name(table_name):
                        response["content"] = {"error": f"非法表名: {table_name}"}
                    else:
                        try:
                            result = execute_query(f"DESCRIBE {table_name}")
                            response["content"] = {"structure": result, "table": table_name}
                        except Exception as e:
                            mcp_logger.error(f"获取表结构错误: {str(e)}")
                            response["content"] = {"error": str(e)}
                
                elif tool_name == "query_table":
                    table_name = args.get("table_name", "")
                    if not validate_table_name(table_name):
                        response["content"] = {"error": f"非法表名: {table_name}"}
                    else:
                        try:
                            conditions = args.get("conditions", {})
                            limit = int(args.get("limit", 20))
                            offset = int(args.get("offset", 0))
                            order_by = args.get("order_by", "id DESC")
                            
                            result = query_records(
                                table_name=table_name,
                                conditions=conditions,
                                order_by=order_by,
                                limit=limit,
                                offset=offset
                            )
                            
                            response["content"] = {
                                "result": result, 
                                "row_count": len(result) if result else 0,
                                "table": table_name,
                                "limit": limit,
                                "offset": offset
                            }
                        except Exception as e:
                            mcp_logger.error(f"查询表数据错误: {str(e)}")
                            response["content"] = {"error": str(e)}
                
                else:
                    response["content"] = {"error": f"未知工具: {tool_name}"}
                
                try:
                    print(json.dumps(response), flush=True)
                    mcp_logger.debug(f"已发送响应: {call_id}")
                except Exception as e:
                    mcp_logger.error(f"发送响应失败: {str(e)}")
                
        except json.JSONDecodeError:
            mcp_logger.error("无效的JSON请求")
            continue
        except Exception as e:
            mcp_logger.error(f"处理请求错误: {str(e)}")
            try:
                error_response = {
                    "id": request.get("id", "error"),
                    "type": "tool_response",
                    "content": {"error": str(e)}
                }
                print(json.dumps(error_response), flush=True)
            except:
                pass

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"error": f"MCP服务器崩溃: {str(e)}"}), flush=True)
        sys.exit(1) 