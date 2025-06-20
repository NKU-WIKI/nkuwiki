#!/usr/bin/env python3
"""
ETL增量处理管道

该脚本负责执行增量ETL流程的第二和第三阶段：
1.  **扫描与节点化 (Scan & Nodify)**: 扫描 `/data/raw` 目录，找出指定时间窗口内的新增/修改文件，并将其转换为LlamaIndex的`TextNode`对象。
2.  **建立索引 (Indexing)**: 将新生成的`TextNode`对象送入Qdrant建立向量索引。
3.  **生成洞察 (Insight Generation)**: (可选) 基于新增节点，按来源分类（官方、社区、集市）后，分别调用`text_generator`生成分析洞察并存入数据库。
"""
import sys
from pathlib import Path

# 将项目根目录添加到Python路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

import argparse
import asyncio
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Literal, Any
from collections import defaultdict

import aiofiles
from llama_index.core.schema import Document, TextNode
from tqdm.asyncio import tqdm as aio_tqdm

from config import Config
from core.agent.text_generator import generate_structured_json
from core.utils.logger import register_logger
from etl.indexing.qdrant_indexer import QdrantIndexer
from etl.load import db_core
from etl.processors.chunk_cache import ChunkCacheManager
from etl.utils.const import (
    university_official_accounts,
    school_official_accounts,
    club_official_accounts,
    unofficial_accounts,
)

logger = register_logger("etl.daily_pipeline")

# 定义洞察分类
InsightCategory = Literal["官方", "社区", "集市"]

# 定义官方和社区来源
OFFICIAL_WECHAT_SOURCES = set(university_official_accounts + school_official_accounts)
COMMUNITY_WECHAT_SOURCES = set(club_official_accounts + unofficial_accounts)


def parse_datetime_utc(time_str: str) -> Optional[datetime]:
    """将字符串稳健地解析为带UTC时区的时间对象"""
    if not time_str or not isinstance(time_str, str):
        return None
    try:
        # 尝试ISO 8601格式（带或不带'Z'）
        if time_str.endswith("Z"):
            time_str = time_str[:-1] + "+00:00"
        dt = datetime.fromisoformat(time_str)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        pass

    # 尝试其他常见格式
    formats_to_try = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]
    for fmt in formats_to_try:
        try:
            dt = datetime.strptime(time_str, fmt)
            # 假定为本地时区并转换为UTC
            return dt.astimezone().astimezone(timezone.utc)
        except ValueError:
            continue
    logger.debug(f"无法解析的时间格式: '{time_str}'")
    return None


async def find_new_files_in_timespan(
    data_dir: Path, start_time: datetime, end_time: datetime, platform_filter: Optional[str] = None
) -> List[Path]:
    """在/data/raw目录中高效查找指定时间窗口内发布的JSON文件"""
    logger.info(f"开始扫描目录 '{data_dir}'，时间范围: {start_time.isoformat()} to {end_time.isoformat()}")
    if platform_filter:
        logger.info(f"仅扫描平台: '{platform_filter}'")
    
    # 1. 根据时间范围，确定需要扫描的年月目录
    target_months = set()
    current_date = start_time.date()
    while current_date <= end_time.date():
        target_months.add(current_date.strftime("%Y%m"))
        # 移动到下一个月
        # (这种方式可以稳健地处理月份天数不同的情况)
        next_month_start = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        current_date = next_month_start

    logger.info(f"将目标扫描范围限定于以下年月目录: {sorted(list(target_months))}")

    # 2. 遍历所有 platform/tag 组合，查找匹配的年月目录，收集文件
    files_to_check = []
    if not data_dir.is_dir():
        logger.warning(f"数据源目录 {data_dir} 不存在。")
        return []

    for platform_dir in data_dir.iterdir():
        if not platform_dir.is_dir():
            continue
        if platform_filter and platform_dir.name != platform_filter:
            continue
        for tag_dir in platform_dir.iterdir():
            if not tag_dir.is_dir():
                continue
            for month_str in target_months:
                month_dir = tag_dir / month_str
                if month_dir.is_dir():
                    files_to_check.extend(month_dir.rglob("*.json"))
    
    logger.info(f"在目标年月目录中共找到 {len(files_to_check)} 个 .json 文件待精确检查。")

    # 3. 对筛选后的文件进行精确时间检查
    tasks = [is_file_in_timespan(file_path, start_time, end_time) for file_path in files_to_check]
    
    results = await aio_tqdm.gather(
        *tasks, desc="精确扫描文件", unit="个"
    )

    new_files = [path for path in results if path is not None]
    logger.info(f"精确扫描完成，在时间范围内找到 {len(new_files)} 个新文件。")
    return new_files


async def is_file_in_timespan(
    file_path: Path, start_time: datetime, end_time: datetime
) -> Optional[Path]:
    """检查单个文件的发布时间是否在指定范围内"""
    try:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read()
            data = json.loads(content)
        
        publish_time_str = data.get("publish_time")
        publish_time = parse_datetime_utc(publish_time_str)
        
        if publish_time and start_time <= publish_time <= end_time:
            return file_path
    except Exception:
        # 忽略JSON解析失败或缺少时间字段的文件
        return None
    return None


async def process_files_to_nodes(file_paths: List[Path]) -> List[TextNode]:
    """读取文件，处理并转换为TextNode列表"""
    if not file_paths:
        return []
    
    chunk_manager = ChunkCacheManager()
    all_nodes = []

    async def process_single_file(path: Path) -> List[TextNode]:
        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content)
            
            # 使用Document对象来承载内容和元数据
            doc = Document(
                text=data.get("content", ""),
                metadata={
                    "doc_id": data.get("id"),
                    "title": data.get("title"),
                    "url": data.get("url"),
                    "platform": data.get("platform"),
                    "tag": data.get("tag"),  # 确保tag字段被提取
                    "publish_time": data.get("publish_time"),
                    "file_path": str(path),
                },
            )
            return await chunk_manager.chunk_documents_with_cache([doc], show_progress=False)
        except Exception as e:
            logger.warning(f"处理文件 {path} 失败: {e}")
            return []

    tasks = [process_single_file(path) for path in file_paths]
    results = await aio_tqdm.gather(*tasks, desc="处理并转换节点", unit="个")
    
    for node_list in results:
        all_nodes.extend(node_list)
        
    logger.info(f"成功将 {len(file_paths)} 个文件转换为 {len(all_nodes)} 个TextNode。")
    return all_nodes


async def build_qdrant_indexes(nodes: List[TextNode], config: Config):
    """为新节点建立Qdrant索引"""
    if not nodes:
        logger.warning("没有节点需要索引，跳过此步骤。")
        return
        
    collection_name = config.get("qdrant.collection_name")
    qdrant_indexer = QdrantIndexer(collection_name)
    logger.info(f"开始向Qdrant集合 '{collection_name}' 中添加 {len(nodes)} 个节点...")
    await qdrant_indexer.build_from_nodes(nodes)
    logger.info("Qdrant索引建立完成。")


async def read_raw_documents(file_paths: List[Path]) -> List[Dict[str, Any]]:
    """
    异步读取一组JSON文件路径，并返回其内容字典的列表。
    每个返回的字典中会额外添加一个 `_file_path` 键，用于追踪源文件。
    """
    async def _read_file(path: Path) -> Optional[Dict[str, Any]]:
        try:
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)
                data["_file_path"] = str(path)  # 注入文件路径
                return data
        except Exception as e:
            logger.error(f"读取或解析文件失败: {path}, 错误: {e}")
            return None

    tasks = [_read_file(path) for path in file_paths]
    results = await aio_tqdm.gather(*tasks, desc="读取原始文档")
    return [doc for doc in results if doc]  # 过滤掉读取失败的None


def build_insight_prompt(docs: List[Dict[str, Any]], category: InsightCategory, char_limit: Optional[int] = None) -> str:
    """
    根据原始文档字典列表和分类构建用于生成洞察的Prompt。
    会对输入内容进行截断，以确保最终的Prompt不超过指定的字符限制。
    """
    # 1. 定义提示词的头部和尾部
    prompt_header = f"""
作为一名校园信息分析专家，请对以下新发布的 **{category}** 相关校园动态进行分析、总结和归类，并提取核心洞察。

**分析任务:**
1.  **总结要点**: 对所有动态进行概括，形成一段100字以内的总体摘要。
2.  **提取洞察**: 识别出3-5个最重要或最有趣的主题/趋势。对于每个主题，你必须提供：
    - **一个简短的标题**
    - **一段详尽的分析描述，要求内容充实，字数不得少于1000字**。简短的描述是不可接受的。

**近期动态全文列表:**
"""

    prompt_footer = """

请严格按照以下JSON格式返回结果，不要添加任何额外的解释或注释：
```json
{{
    "summary": "总体摘要内容（100字以内）...",
    "insights": [
        {{
            "title": "洞察主题1",
            "content": "关于主题1的详尽分析（不少于1000字）..."
        }},
        {{
            "title": "洞察主题2",
            "content": "关于主题2的详尽分析（不少于1000字）..."
        }}
    ]
}}
```
"""

    # 2. 计算文档部分可用的字符限制
    docs_char_limit = None
    if char_limit:
        template_overhead = len(prompt_header) + len(prompt_footer)
        docs_char_limit = char_limit - template_overhead

        # 如果限制太小，无法容纳模板本身，则记录错误并返回空
        if docs_char_limit <= 0:
            logger.error(
                f"总字符限制({char_limit})太小，不足以容纳Prompt模板的固定内容({template_overhead})。"
            )
            return ""

    # 3. 填充文档内容，确保不超过 docs_char_limit
    doc_details = []
    current_docs_len = 0
    separator = "\n\n---\n\n"

    for doc in docs:
        title = doc.get("title", "无标题")
        publish_time = doc.get("publish_time", "未知时间")
        tag = doc.get("tag", "未知来源")
        full_content = doc.get("content", "")
        
        detail_str = (
            f"来源: {tag}\n"
            f"标题: {title}\n"
            f"发布时间: {publish_time}\n"
            f"内容:\n{full_content}"
        )

        # 计算新文档加入后会增加的长度（包括分隔符）
        added_len = len(detail_str) + (len(separator) if doc_details else 0)

        if docs_char_limit and (current_docs_len + added_len > docs_char_limit):
            logger.warning(
                f"文档内容部分已达到限制({docs_char_limit}字符)，停止添加更多文档。 "
                f"总字符限制: {char_limit}, 模板开销: {template_overhead}. "
                f"总文档数: {len(docs)}, 实际处理: {len(doc_details)}."
            )
            break
        
        doc_details.append(detail_str)
        current_docs_len += added_len
    
    # 4. 组装最终的Prompt
    docs_str = separator.join(doc_details)
    prompt = f"{prompt_header}{docs_str}{prompt_footer}"

    logger.info(f"为分类 '{category}' 生成洞察的Prompt，输入总字符数: {len(prompt)}")
    logger.debug(f"Prompt for '{category}': \n{prompt[:500]}...")
    return prompt


async def generate_and_save_insights(
    docs: List[Dict[str, Any]],
    config: Config,
    end_time: datetime,
    insight_char_limit: Optional[int] = None,
):
    """
    基于原始文档列表生成洞察，并将其分类存入数据库。
    """
    if not docs:
        logger.info("没有新的文档可供生成洞察。")
        return

    # 0. 按发布时间倒序排序文档，优先处理最新的内容
    docs.sort(key=lambda d: parse_datetime_utc(d.get("publish_time")) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    # 1. 定义官方来源
    official_wechat_sources = set(university_official_accounts + school_official_accounts)
    community_wechat_sources = set(club_official_accounts + unofficial_accounts)

    # 2. 将文档分类
    categorized_docs = defaultdict(list)
    for doc in docs:
        platform = doc.get("platform")
        author = doc.get("author") # 使用 author 字段进行分类
        category = None

        if platform == "website" or (platform == "wechat" and author in official_wechat_sources):
            category = "官方"
        elif platform == "wechat" and author in community_wechat_sources:
            category = "社区"
        elif platform == "market":
            category = "集市"

        if category:
            categorized_docs[category].append(doc)

    logger.info(
        f"文档分类完成：官方({len(categorized_docs['官方'])}), "
        f"社区({len(categorized_docs['社区'])}), "
        f"集市({len(categorized_docs['集市'])})"
    )

    # 3. 为每个分类生成并存储洞察
    for category, doc_list in categorized_docs.items():
        if not doc_list:
            logger.info(f"分类 '{category}' 中没有新文档，跳过洞察生成。")
            continue

        logger.info(f"开始为分类 '{category}' 生成洞察 (基于 {len(doc_list)} 个文档)...")
        try:
            prompt = build_insight_prompt(
                doc_list, category, char_limit=insight_char_limit
            )
            generated_data = await generate_structured_json(prompt)

            if not generated_data or "insights" not in generated_data:
                logger.warning(
                    f"从LLM返回的数据格式不正确或为空，缺少'insights'，跳过分类 '{category}' 的存储。"
                )
                # 记录可能导致问题的文档路径
                problematic_files = [doc.get("_file_path", "未知路径") for doc in doc_list]
                logger.warning(f"触发问题的文档列表 (共 {len(problematic_files)} 个): {problematic_files}")
                continue

            # 准备存入数据库的数据
            db_records = []
            for insight in generated_data.get("insights", []):
                db_records.append({
                    "title": insight.get("title"),
                    "content": insight.get("content"),
                    "category": category,
                    "insight_date": end_time.date(),
                })

            if db_records:
                inserted_count = await db_core.batch_insert("insights", db_records)
                logger.info(f"成功为分类 '{category}' 插入 {inserted_count} 条洞察到数据库。")

        except Exception as e:
            logger.error(f"为分类 '{category}' 生成或存储洞察失败: {e}", exc_info=True)


def get_time_window(args: argparse.Namespace) -> Tuple[datetime, datetime]:
    """
    根据命令行参数计算并返回UTC时间窗口。
    如果只提供了日期 (YYYY-MM-DD)，则将开始时间设为当天00:00:00，结束时间设为当天23:59:59。
    """
    # 确定结束时间
    if args.end_time:
        end_time_utc = parse_datetime_utc(args.end_time)
        # 如果是纯日期格式，则扩展到当天结束
        if end_time_utc and re.match(r"^\d{4}-\d{2}-\d{2}$", args.end_time):
            end_time_utc = end_time_utc.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        # --hours 参数增强: 如果未提供 end_time，则 end_time 默认为当前时刻
        end_time_utc = datetime.now(timezone.utc)

    # 确定开始时间
    if args.start_time:
        start_time_utc = parse_datetime_utc(args.start_time)
        # 如果是纯日期格式，确保为当天开始 (尽管 parse_datetime_utc 已处理，但为清晰起见)
        if start_time_utc and re.match(r"^\d{4}-\d{2}-\d{2}$", args.start_time):
            start_time_utc = start_time_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start_time_utc = end_time_utc - timedelta(hours=args.hours)

    if not start_time_utc or not end_time_utc:
        raise ValueError("无法解析开始或结束时间，请检查输入格式。")

    return start_time_utc, end_time_utc


async def main(args: argparse.Namespace):
    """主执行函数"""
    try:
        start_time, end_time = get_time_window(args)
    except ValueError as e:
        logger.error(e)
        return

    steps = {s.strip() for s in args.steps.lower().split(",")}
    run_all = "all" in steps

    logger.info("=" * 60)
    logger.info(f"🚀 启动增量ETL管道，时间窗口: {start_time.isoformat()} -> {end_time.isoformat()}")
    logger.info(f"🔩 执行步骤: {', '.join(sorted(list(steps)))}")
    logger.info(f"📚 数据源目录: {args.data_dir}")
    logger.info("=" * 60)

    config = Config()
    nodes: List[TextNode] = []
    
    # 步骤 1: 扫描文件
    if run_all or "scan" in steps:
        logger.info("========== 步骤 1: 扫描文件 ==========")
        file_paths = await find_new_files_in_timespan(
            Path(args.data_dir), start_time, end_time, platform_filter=args.platform
        )

    # --- 步骤 2: 读取原始文件 (洞察步骤需要) ---
    if "insight" in steps:
        if not file_paths and "scan" not in steps:
            logger.warning("未执行'scan'步骤，且未提供文件，'insight'步骤将被跳过。")
        else:
            logger.info(f"========== 步骤 2 (洞察): 读取 {len(file_paths)} 个原始文件 ==========")
            docs = await read_raw_documents(file_paths)
            
            logger.info(f"========== 步骤 3 (洞察): 生成洞察 ==========")
            await generate_and_save_insights(
                docs, config, end_time, insight_char_limit=args.insight_char_limit
            )

    # --- 步骤 3: 转换和索引 (索引步骤需要) ---
    if "index" in steps:
        if not file_paths and "scan" not in steps:
            logger.warning("未执行'scan'步骤，且未提供文件，'index'步骤将被跳过。")
        else:
            logger.info(f"========== 步骤 2 (索引): 转换 {len(file_paths)} 个文件为节点 ==========")
            nodes = await process_files_to_nodes(file_paths)
            
            logger.info(f"========== 步骤 3 (索引): 建立Qdrant索引 ==========")
            await build_qdrant_indexes(nodes, config)

    logger.info("✅ ETL管道执行完毕。")

# /opt/venv/bin/python etl/daily_pipeline.py --hours 24 --steps scan,index,insight
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NKUWiki增量ETL管道")
    parser.add_argument(
        "--data_dir",
        type=str,
        default="/data/raw",
        help="原始数据存储目录",
    )
    parser.add_argument(
        "--steps",
        type=str,
        default="all",
        help="要执行的步骤，用逗号分隔 (scan, index, insight, all)",
    )
    parser.add_argument(
        "--start_time",
        type=str,
        help="处理的开始时间 (支持 'YYYY-MM-DD' 或 ISO格式, e.g., '2023-10-27T00:00:00+08:00')",
    )
    parser.add_argument(
        "--end_time",
        type=str,
        help="处理的结束时间 (支持 'YYYY-MM-DD' 或 ISO格式, e.g., '2023-10-28T00:00:00+08:00')",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="如果未提供start_time，则从end_time回溯的小时数",
    )
    parser.add_argument(
        "--platform",
        type=str,
        default=None,
        help="只处理特定平台的数据 (e.g., 'wechat')",
    )
    parser.add_argument(
        "--insight-char-limit",
        type=int,
        default=58000,
        help="生成洞察时输入给大语言模型的最大字符数限制。默认为60000，以适配常见的大模型上下文窗口。",
    )

    args = parser.parse_args()
    asyncio.run(main(args))

