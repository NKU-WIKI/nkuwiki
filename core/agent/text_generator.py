#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量级文本生成模块

该模块提供了一个直接调用大语言模型（LLM）进行文本生成的功能，
专注于从给定的提示（Prompt）生成结构化的JSON输出。
它绕过了完整的RAG管道，避免了不必要的索引和检索组件的初始化开销。
"""
import asyncio
import json
import sys
import re
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from core.agent.agent_factory import create_agent
from core.utils.logger import register_logger
from core.bridge.context import Context

logger = register_logger(module_name="core.agent.text_generator")

async def generate_structured_json(prompt: str, max_retries: int = 2) -> Dict[str, Any]:
    """
    使用LLM从给定的提示生成结构化的JSON数据。

    该函数会直接初始化一个用于生成的Agent，并向其发送提示。
    它包含了重试逻辑和JSON解析，以确保输出的健壮性。

    Args:
        prompt (str): 发送给LLM的完整提示。
        max_retries (int): 最大重试次数。

    Returns:
        Dict[str, Any]: 从LLM返回的解析后的JSON数据。
        如果失败，则返回一个包含错误信息的字典。
    """
    # 使用Agent工厂模式创建一个用于文本生成的LLM实例（例如Coze）
    generator_agent = create_agent(agent_type='coze',tag='dkv3')

    raw_result_dict = None
    for attempt in range(max_retries):
        try:
            # 记录发送给LLM的完整Prompt
            logger.debug(f"发送给LLM的完整Prompt: \n{prompt}")

            # 参考 api/routes/agent/rag.py 的用法，使用 run_in_executor 调用同步方法
            loop = asyncio.get_event_loop()
            raw_result_dict = await loop.run_in_executor(
                None,
                lambda: generator_agent.chat_with_new_conversation(
                    prompt,
                    stream=False,
                    openid="daily_pipeline_user"
                )
            )

            # 记录从LLM收到的原始响应
            logger.debug(f"从LLM收到的原始响应: \n{raw_result_dict}")

            # chat_with_new_conversation 返回的是一个字典
            if not isinstance(raw_result_dict, dict) or "response" not in raw_result_dict:
                 logger.warning(f"LLM返回了非预期的格式: {raw_result_dict}")
                 continue

            raw_result = raw_result_dict.get("response", "")

            if not isinstance(raw_result, str):
                logger.warning(f"LLM返回的response字段不是字符串: {raw_result}")
                continue

            # 增强的JSON解析逻辑
            parsed_json = None
            try:
                # 优先尝试直接解析整个响应
                parsed_json = json.loads(raw_result)
                logger.info("成功将LLM响应直接解析为JSON。")
            except json.JSONDecodeError:
                # 如果直接解析失败，则尝试从Markdown代码块中提取
                logger.debug("直接解析JSON失败，尝试从Markdown代码块中提取...")
                match = re.search(r"```(json)?\n([\s\S]*?)\n```", raw_result)
                if match:
                    json_str = match.group(2)
                    try:
                        parsed_json = json.loads(json_str)
                        logger.info("成功从Markdown代码块中提取并解析了JSON。")
                    except json.JSONDecodeError as e:
                        logger.warning(f"无法解析Markdown代码块中的JSON: {e}")
                else:
                    logger.warning("LLM响应中既不是有效JSON，也未找到JSON代码块。")

            if parsed_json:
                return parsed_json
            else:
                # 如果两种方式都失败，则继续重试
                continue

        except Exception as e:
            logger.warning(f"处理LLM响应时出错，尝试次数 {attempt + 1}/{max_retries}。错误: {e}\n原始输出: {raw_result_dict}")
            if attempt < max_retries - 1:
                logger.info(f"将在2秒后重试...")
                await asyncio.sleep(2)
    
    logger.error(f"在尝试 {max_retries} 次后，仍无法从LLM获取有效的JSON响应。")
    raise ValueError("Failed to generate structured JSON from LLM.")

async def main():
    """用于测试的函数"""
    test_prompt = """
    请分析以下文本，并返回一个JSON对象。
    文本：南开大学今天宣布启动了新的AI研究项目。
    JSON格式: {"event": "事件描述", "tags": ["标签1", "标签2"]}
    """
    result = await generate_structured_json(test_prompt)
    print("生成结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    asyncio.run(main()) 