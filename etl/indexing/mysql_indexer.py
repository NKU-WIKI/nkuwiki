"""
MySQL索引构建器

负责将原始数据导入MySQL数据库，包括PageRank分数整合。
使用异步操作提高性能。
"""

import os
import sys
import json
import logging
import asyncio
import re
import networkx as nx
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from tqdm import tqdm
from datetime import datetime
import sqlite3
import aiofiles

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config import Config
from etl import RAW_PATH
from etl.load import db_core
from etl.processors.document import DocumentProcessor

logger = logging.getLogger(__name__)

def _truncate_content(content: str) -> str:
    """按字节数安全截断内容
    
    MySQL TEXT类型最大65535字节，为安全起见设置为60000字节
    """
    if not content:
        return ""
    
    MAX_BYTES = 60000  # 60KB，为TEXT类型留出安全边距
    
    # 如果内容的UTF-8编码长度超过限制，则需要截断
    content_bytes = content.encode('utf-8')
    if len(content_bytes) <= MAX_BYTES:
        return content
    
    # 按字节截断，但要确保不破坏UTF-8字符
    truncated_bytes = content_bytes[:MAX_BYTES]
    
    # 找到最后一个完整的UTF-8字符边界
    while len(truncated_bytes) > 0:
        try:
            return truncated_bytes.decode('utf-8')
        except UnicodeDecodeError:
            # 如果解码失败，说明截断位置在字符中间，往前退一个字节
            truncated_bytes = truncated_bytes[:-1]
    
    return ""  # 如果无法解码，返回空字符串

def _truncate_title(title: str) -> str:
    """截断标题字段以适配数据库限制
    
    VARCHAR(500)约等于1500字节（UTF-8），为安全起见设置为1200字节
    """
    if not title:
        return ""
    
    MAX_BYTES = 1200  # 为VARCHAR(500)留出安全边距
    
    # 如果标题的UTF-8编码长度超过限制，则需要截断
    title_bytes = title.encode('utf-8')
    if len(title_bytes) <= MAX_BYTES:
        return title
    
    # 按字节截断，但要确保不破坏UTF-8字符
    truncated_bytes = title_bytes[:MAX_BYTES]
    
    # 找到最后一个完整的UTF-8字符边界
    while len(truncated_bytes) > 0:
        try:
            return truncated_bytes.decode('utf-8')
        except UnicodeDecodeError:
            # 如果解码失败，说明截断位置在字符中间，往前退一个字节
            truncated_bytes = truncated_bytes[:-1]
    
    return ""  # 如果无法解码，返回空字符串

class MySQLIndexer:
    """MySQL数据库索引构建器
    
    负责将爬取的数据导入到MySQL数据库中，构建主要的数据索引。
    支持两阶段构建：基础数据导入 + PageRank分数更新。
    使用异步操作提高性能。
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.document_parser = DocumentProcessor()
        
    async def create_tables(self) -> bool:
        """异步创建所需的数据库表"""
        try:
            # 读取并执行所有建表SQL
            tables_dir = Path(__file__).parent.parent / "load" / "mysql_tables"
            
            for sql_file in tables_dir.glob("*.sql"):
                self.logger.info(f"创建表: {sql_file.name}")
                async with aiofiles.open(sql_file, 'r', encoding='utf-8') as f:
                    sql_content = await f.read()
                    await db_core.execute_query(sql_content, fetch=False)
                    
            self.logger.info("数据库表创建完成")
            return True
            
        except Exception as e:
            self.logger.error(f"创建数据库表失败: {e}")
            return False
    
    async def import_crawler_data(self, data_dir: str, include_pagerank: bool = False) -> bool:
        """异步导入爬虫数据到MySQL数据库
        
        Args:
            data_dir: 爬虫数据目录
            include_pagerank: 是否包含PageRank分数（第二阶段）
        """
        try:
            data_path = Path(data_dir)
            if not data_path.exists():
                self.logger.error(f"数据目录不存在: {data_dir}")
                return False
            
            # 获取PageRank分数映射（如果需要）
            pagerank_scores = {}
            if include_pagerank:
                pagerank_scores = await self._get_pagerank_scores()
                self.logger.info(f"加载了 {len(pagerank_scores)} 个PageRank分数")
            
            # 导入网站数据
            success_count = 0
            error_count = 0
            
            # 获取所有JSON文件
            json_files = list(data_path.rglob("*.json"))
            self.logger.info(f"找到 {len(json_files)} 个JSON文件")
            
            # 批量处理文件 - 减少并发数量避免死锁
            batch_size = 10  # 减少批次大小避免数据库死锁
            total_batches = (len(json_files) + batch_size - 1) // batch_size
            
            with tqdm(total=len(json_files), desc="导入MySQL数据", unit="files") as pbar:
                for i in range(0, len(json_files), batch_size):
                    batch_files = json_files[i:i+batch_size]
                    tasks = [
                        self._import_single_file(
                            json_file, 
                            pagerank_scores if include_pagerank else {}
                        ) for json_file in batch_files
                    ]
                    
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in batch_results:
                        if isinstance(result, Exception):
                            error_count += 1
                            self.logger.error(f"批量处理出错: {result}")
                        elif result:
                            success_count += 1
                        else:
                            error_count += 1
                        
                        # 更新进度条
                        pbar.update(1)
                        pbar.set_postfix({
                            '成功': success_count,
                            '失败': error_count,
                            '成功率': f'{success_count/(success_count+error_count)*100:.1f}%' if (success_count+error_count) > 0 else '0%'
                        })
                    
                    # 批量处理间添加短暂延迟，减少数据库压力
                    await asyncio.sleep(0.05)
            
            self.logger.info(f"数据导入完成: 成功={success_count}, 失败={error_count}")
            return error_count == 0
            
        except Exception as e:
            self.logger.error(f"导入爬虫数据失败: {e}")
            return False
    
    async def calculate_pagerank(self, alpha: float = 0.85, max_iter: int = 100) -> bool:
        """计算并保存PageRank分数"""
        try:
            self.logger.info("开始计算PageRank分数...")
            
            # 1. 从link_graph表加载链接数据
            links = await self._load_link_graph()
            if not links:
                self.logger.warning("没有链接数据，跳过PageRank计算")
                return True
            
            # 2. 计算PageRank分数
            pagerank_scores = await self._compute_pagerank(links, alpha, max_iter)
            if not pagerank_scores:
                self.logger.error("PageRank计算失败")
                return False
            
            # 3. 保存到pagerank_scores表
            if not await self._save_pagerank_scores(pagerank_scores):
                self.logger.error("保存PageRank分数失败")
                return False
            
            # 4. 更新website_nku表
            if not await self.update_pagerank_scores():
                self.logger.error("更新website_nku表失败")
                return False
            
            self.logger.info("PageRank计算和更新完成")
            return True
            
        except Exception as e:
            self.logger.error(f"计算PageRank失败: {e}")
            return False
    
    async def _load_link_graph(self) -> List[Tuple[str, str]]:
        """从MySQL的link_graph表加载链接关系"""
        try:
            self.logger.info("从link_graph表加载链接数据...")
            
            query = "SELECT source_url, target_url FROM link_graph"
            records = await db_core.execute_query(query, fetch=True)
            
            if not records:
                self.logger.warning("link_graph表中没有数据")
                return []
            
            links = [(record['source_url'], record['target_url']) for record in records]
            self.logger.info(f"成功加载 {len(links)} 条链接关系")
            
            return links
            
        except Exception as e:
            self.logger.error(f"加载链接图数据失败: {e}")
            return []
    
    async def _compute_pagerank(self, links: List[Tuple[str, str]], alpha: float = 0.85, max_iter: int = 100) -> Dict[str, float]:
        """使用NetworkX计算PageRank分数（异步包装）"""
        if not links:
            return {}
        
        def _calculate():
            """在线程池中运行的同步计算函数"""
            self.logger.info("构建有向图...")
            G = nx.DiGraph()
            
            # 添加边
            for source, target in tqdm(links, desc="构建图", unit="链接"):
                G.add_edge(source, target)
            
            self.logger.info(f"图构建完成: {G.number_of_nodes()} 个节点, {G.number_of_edges()} 条边")
            
            # 计算PageRank
            self.logger.info(f"开始计算PageRank (alpha={alpha}, max_iter={max_iter})...")
            pagerank_scores = nx.pagerank(G, alpha=alpha, max_iter=max_iter)
            
            # 显示分数统计
            scores = list(pagerank_scores.values())
            self.logger.info(f"PageRank计算完成: {len(pagerank_scores)} 个节点")
            self.logger.info(f"分数统计 - 最大: {max(scores):.6f}, 最小: {min(scores):.6f}, 平均: {sum(scores)/len(scores):.6f}")
            
            return pagerank_scores
        
        # 在线程池中运行计算
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _calculate)
    
    async def _save_pagerank_scores(self, pagerank_scores: Dict[str, float]) -> bool:
        """将PageRank分数保存到pagerank_scores表"""
        if not pagerank_scores:
            return False
        
        try:
            self.logger.info("清空现有的pagerank_scores表...")
            await db_core.execute_query("DELETE FROM pagerank_scores", fetch=False)
            
            self.logger.info("保存PageRank分数到MySQL...")
            
            # 批量插入数据
            batch_size = 1000
            data_list = list(pagerank_scores.items())
            
            with tqdm(total=len(data_list), desc="保存PageRank分数", unit="记录") as pbar:
                for i in range(0, len(data_list), batch_size):
                    batch = data_list[i:i + batch_size]
                    
                    # 准备批量插入语句
                    placeholders = ",".join(["(%s, %s)"] * len(batch))
                    query = f"""INSERT INTO pagerank_scores (url, pagerank_score) VALUES {placeholders}
                               ON DUPLICATE KEY UPDATE 
                               pagerank_score = VALUES(pagerank_score),
                               calculation_date = CURRENT_TIMESTAMP"""
                    
                    # 展平数据
                    values = []
                    for url, score in batch:
                        values.extend([url, float(score)])
                    
                    # 执行插入
                    await db_core.execute_query(query, values, fetch=False)
                    pbar.update(len(batch))
            
            self.logger.info(f"成功保存 {len(pagerank_scores)} 个PageRank分数")
            return True
            
        except Exception as e:
            self.logger.error(f"保存PageRank分数失败: {e}")
            return False

    async def update_pagerank_scores(self) -> bool:
        """异步更新PageRank分数（第二阶段）"""
        try:
            self.logger.info("更新website_nku表中的PageRank分数...")
            
            # 执行联合更新
            query = """
            UPDATE website_nku w 
            JOIN pagerank_scores p ON w.original_url = p.url 
            SET w.pagerank_score = p.pagerank_score
            """
            
            await db_core.execute_query(query, fetch=False)
            
            # 统计更新结果
            stats_query = """
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN pagerank_score > 0 THEN 1 END) as updated,
                MAX(pagerank_score) as max_score,
                AVG(pagerank_score) as avg_score
            FROM website_nku
            """
            
            stats = await db_core.execute_query(stats_query, fetch=True)
            if stats:
                stat = stats[0]
                self.logger.info(f"更新统计: 总记录={stat['total']}, 已更新={stat['updated']}, "
                               f"最大分数={stat['max_score']:.6f}, 平均分数={stat['avg_score']:.6f}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"更新website_nku表失败: {e}")
            return False
    
    async def _get_pagerank_scores(self) -> Dict[str, float]:
        """异步获取PageRank分数映射"""
        try:
            scores_data = await db_core.execute_query(
                "SELECT url, pagerank_score FROM pagerank_scores",
                fetch=True
            )
            return {item['url']: float(item['pagerank_score']) for item in scores_data} if scores_data else {}
        except Exception as e:
            self.logger.warning(f"获取PageRank分数失败: {e}")
            return {}
    
    def _determine_table_by_path(self, json_file: Path) -> str:
        """根据文件路径确定数据表
        
        路径格式: /data/raw/{platform}/{tag}/...
        例如: /data/raw/wechat/nku/... -> wechat_nku
        """
        try:
            # 获取相对于RAW_PATH的路径部分
            rel_path = json_file.relative_to(RAW_PATH)
            path_parts = rel_path.parts
            
            if len(path_parts) >= 2:
                platform = path_parts[0].lower()  # wechat, website, wxapp
                tag = path_parts[1].lower()       # nku
                
                # 根据平台和标签确定表名
                if platform == 'wechat' and tag == 'nku':
                    return 'wechat_nku'
                elif platform == 'website' and tag == 'nku':
                    return 'website_nku'
                elif platform == 'wxapp':
                    return 'wxapp_post'  # wxapp使用特殊表名
                else:
                    # 其他情况使用 platform_tag 格式
                    return f"{platform}_{tag}"
            
            # 如果无法解析路径，使用fallback逻辑
            file_path_str = str(json_file).lower()
            if '/wechat/' in file_path_str:
                return 'wechat_nku'
            elif '/wxapp/' in file_path_str:
                return 'wxapp_post'
            elif '/website/' in file_path_str:
                return 'website_nku'
            else:
                return 'website_nku'  # 默认
                
        except (ValueError, IndexError):
            # 路径解析失败，使用默认表
            self.logger.debug(f"无法解析路径格式: {json_file}，使用默认表")
            return 'website_nku'

    async def _import_single_file(self, json_file: Path, pagerank_scores: Dict[str, float]) -> bool:
        """异步导入单个JSON文件"""
        try:
            # 根据文件路径确定目标表
            target_table = self._determine_table_by_path(json_file)
            
            # 异步读取文件
            async with aiofiles.open(json_file, 'r', encoding='utf-8') as f:
                content_str = await f.read()
            data = json.loads(content_str)
            
            # 增加对数据类型的检查，确保为字典
            if not isinstance(data, dict):
                # 降级为debug日志，这只是一种正常的数据情况
                self.logger.debug(f"跳过文件 {json_file}：期望的数据类型为dict，实际为{type(data)}")
                return False

            # 提取基本字段
            original_url = data.get('original_url', '')
            title = data.get('title', '')
            content = data.get('content', '')

            if not original_url or not title:
                return False
            
            # 解析文档内容（如果是文档URL）
            file_url = data.get('file_url')
            if file_url and not content.strip():
                try:
                    # 异步解析文档
                    loop = asyncio.get_event_loop()
                    parsed_content = await loop.run_in_executor(
                        None, 
                        self.document_parser.parse_from_url, 
                        file_url
                    )
                    if parsed_content:
                        content = parsed_content
                        self.logger.debug(f"解析文档内容: {file_url}")
                except Exception as e:
                    self.logger.warning(f"文档解析失败 {file_url}: {e}")
            
            # 内容和标题长度限制（必须在文档解析后进行）
            content = self._truncate_content(content)
            title = _truncate_title(title)
            
            # 准备插入数据
            pagerank_score = pagerank_scores.get(original_url, 0.0)
            
            # 解析发布时间
            publish_time = self._parse_publish_time(data.get('publish_time'))
            scrape_time = self._parse_scrape_time(data.get('scrape_time'))
            
            # 根据不同的表选择不同的插入逻辑
            success = await self._insert_to_table(
                target_table, data, original_url, title, content, 
                publish_time, scrape_time, pagerank_score
            )
            
            return success
            
        except Exception as e:
            self.logger.error(f"导入文件失败 {json_file}: {e}")
            return False
    
    async def _insert_to_table(self, table_name: str, data: dict, original_url: str, 
                              title: str, content: str, publish_time, scrape_time, 
                              pagerank_score: float) -> bool:
        """根据表名插入数据到对应表"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                if table_name == 'website_nku':
                    await db_core.execute_query("""
                        INSERT INTO website_nku (
                            original_url, title, content, author, publish_time, 
                            scrape_time, platform, pagerank_score, is_official
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            title = VALUES(title),
                            content = VALUES(content),
                            author = VALUES(author),
                            publish_time = VALUES(publish_time),
                            scrape_time = VALUES(scrape_time),
                            pagerank_score = VALUES(pagerank_score),
                            update_time = CURRENT_TIMESTAMP
                    """, [
                        original_url,
                        title,
                        content,
                        data.get('source', ''),
                        publish_time,
                        scrape_time,
                        data.get('platform', 'website'),
                        pagerank_score,
                        1 if 'nankai.edu.cn' in original_url else 0
                    ], fetch=False)
                
                elif table_name == 'wechat_nku':
                    await db_core.execute_query("""
                        INSERT INTO wechat_nku (
                            original_url, title, content, author, publish_time, 
                            scrape_time, platform, view_count, like_count, is_official
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            title = VALUES(title),
                            content = VALUES(content),
                            author = VALUES(author),
                            publish_time = VALUES(publish_time),
                            scrape_time = VALUES(scrape_time),
                            view_count = VALUES(view_count),
                            like_count = VALUES(like_count),
                            update_time = CURRENT_TIMESTAMP
                    """, [
                        original_url,
                        title,
                        content,
                        data.get('source', ''),
                        publish_time,
                        scrape_time,
                        data.get('platform', 'wechat'),
                        data.get('view_count', 0),
                        data.get('like_count', 0),
                        1 if 'nankai' in title.lower() or 'nankai' in content.lower() else 0
                    ], fetch=False)
                
                elif table_name == 'wxapp_post':
                    await db_core.execute_query("""
                        INSERT INTO wxapp_post (
                            title, content, nickname, avatar_url, location, 
                            category, source, status, view_count, like_count, comment_count
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            title = VALUES(title),
                            content = VALUES(content),
                            nickname = VALUES(nickname),
                            location = VALUES(location),
                            category = VALUES(category),
                            view_count = VALUES(view_count),
                            like_count = VALUES(like_count),
                            comment_count = VALUES(comment_count),
                            update_time = CURRENT_TIMESTAMP
                    """, [
                        title,
                        content,
                        data.get('nickname', data.get('author', '')),
                        data.get('avatar_url', ''),
                        data.get('location', ''),
                        data.get('category', ''),
                        data.get('source', 'wxapp'),
                        1,  # status = 1 (active)
                        data.get('view_count', 0),
                        data.get('like_count', 0),
                        data.get('comment_count', 0)
                    ], fetch=False)
                
                return True  # 成功则跳出重试循环
                
            except Exception as e:
                if "Deadlock" in str(e) and attempt < max_retries - 1:
                    # 死锁错误且还有重试机会，等待后重试
                    await asyncio.sleep(0.1 * (attempt + 1))  # 递增等待时间
                    continue
                else:
                    # 非死锁错误或已达最大重试次数，抛出异常
                    raise e
        
        return False
    
    def _parse_publish_time(self, time_str: str) -> Optional[datetime]:
        """解析发布时间"""
        if not time_str:
            return None
            
        try:
            # 尝试多种时间格式
            for fmt in [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y-%m-%d',
                '%Y年%m月%d日 %H:%M',
                '%Y年%m月%d日',
            ]:
                try:
                    return datetime.strptime(time_str, fmt)
                except ValueError:
                    continue
            self.logger.debug(f"无法解析发布时间: {time_str}")
            return None
        except Exception:
            return None
    
    def _parse_scrape_time(self, time_str: str) -> Optional[datetime]:
        """解析爬取时间"""
        if not time_str:
            return datetime.now()
        try:
            return datetime.fromisoformat(time_str)
        except (ValueError, TypeError):
            self.logger.debug(f"无法解析爬取时间: {time_str}")
            return datetime.now()
    
    def _truncate_content(self, content: str) -> str:
        """按字节数安全截断内容（调用全局函数）"""
        return _truncate_content(content)
    
    async def build_indexes(self, data_dir: str = None, dry_run: bool = False) -> bool:
        """
        异步构建或更新MySQL索引。
        此方法封装了数据导入和PageRank更新的完整流程。

        Args:
            data_dir (str, optional): 包含JSON数据文件的目录。
                                      如果为None，将导入所有数据源。
                                      Defaults to None.
            dry_run (bool, optional): 如果为True，则不执行实际的数据库写入操作。
                                      Defaults to False.

        Returns:
            bool: 索引构建是否成功。
        """
        self.logger.info("开始构建MySQL数据库索引...")
        if dry_run:
            self.logger.info("以试运行模式执行，不会写入数据库。")

        try:
            # 1. 创建表（如果不存在）
            if not dry_run:
                await self.create_tables()

            # 2. 确定要处理的数据源目录
            data_sources = []
            if data_dir is None:
                # 如果未指定目录，处理所有数据源
                data_sources = [
                    str(RAW_PATH / 'website'),
                    str(RAW_PATH / 'wechat'), 
                    str(RAW_PATH / 'wxapp')
                ]
                self.logger.info("将导入所有数据源的数据")
            else:
                data_sources = [data_dir]
                self.logger.info(f"将导入指定目录的数据: {data_dir}")

            # 3. 逐个处理数据源目录
            overall_success = True
            for source_dir in data_sources:
                if Path(source_dir).exists():
                    self.logger.info(f"开始处理数据源: {source_dir}")
                    import_success = await self.import_crawler_data(source_dir)
                    if not import_success:
                        self.logger.error(f"导入数据源 {source_dir} 失败")
                        overall_success = False
                    else:
                        self.logger.info(f"数据源 {source_dir} 导入成功")
                else:
                    self.logger.warning(f"数据源目录不存在，跳过: {source_dir}")

            # 4. 计算并更新PageRank分数
            if not dry_run:
                pagerank_success = await self.calculate_pagerank()
                if not pagerank_success:
                    self.logger.warning("PageRank计算阶段失败，但这不阻塞整体流程。")

            if overall_success:
                self.logger.info("MySQL索引构建流程成功完成。")
            else:
                self.logger.warning("部分数据源导入失败，但流程已完成。")
            
            return overall_success

        except Exception as e:
            self.logger.error(f"构建MySQL索引过程中发生未预料的错误: {e}", exc_info=True)
            return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """异步获取索引统计信息"""
        try:
            stats = {}
            
            # 获取各数据表的记录数
            data_tables = ['website_nku', 'wechat_nku', 'wxapp_post']
            total_records = 0
            
            for table in data_tables:
                try:
                    count = await db_core.count_records(table)
                    stats[f"{table}_count"] = count
                    total_records += count
                    
                    # 获取有内容的记录数
                    if table == 'wxapp_post':
                        # wxapp_post表没有original_url字段
                        content_count_result = await db_core.execute_query(
                            f"SELECT COUNT(*) as count FROM {table} WHERE content IS NOT NULL AND content != ''",
                            fetch=True
                        )
                    else:
                        content_count_result = await db_core.execute_query(
                            f"SELECT COUNT(*) as count FROM {table} WHERE content IS NOT NULL AND content != ''",
                            fetch=True
                        )
                    
                    content_count = content_count_result[0]['count'] if content_count_result else 0
                    stats[f"{table}_content_count"] = content_count
                    
                except Exception as e:
                    self.logger.warning(f"获取表 {table} 统计失败: {e}")
                    stats[f"{table}_count"] = 0
                    stats[f"{table}_content_count"] = 0
            
            stats['total_records'] = total_records
            
            # 获取辅助表的记录数
            aux_tables = ['link_graph', 'pagerank_scores']
            for table in aux_tables:
                try:
                    count = await db_core.count_records(table)
                    stats[f"{table}_count"] = count
                except Exception:
                    stats[f"{table}_count"] = 0
            
            # 获取PageRank分数统计
            try:
                result = await db_core.execute_query(
                    "SELECT AVG(pagerank_score), MAX(pagerank_score), MIN(pagerank_score) FROM website_nku WHERE pagerank_score > 0",
                    fetch=True
                )
                if result and result[0]:
                    row = result[0]
                    avg_val = row.get('AVG(pagerank_score)')
                    max_val = row.get('MAX(pagerank_score)')
                    min_val = row.get('MIN(pagerank_score)')
                    
                    if avg_val is not None:
                        stats['pagerank_avg'] = float(avg_val)
                        stats['pagerank_max'] = float(max_val)
                        stats['pagerank_min'] = float(min_val)
            except Exception:
                pass
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {}

async def build_mysql_index(
    data_dir: str = None,
    include_documents: bool = True,
    batch_size: int = 100,
    pagerank_db_path: str = None
) -> Dict[str, Any]:
    """
    构建MySQL全文索引。
    从JSON文件中读取数据，并批量插入到MySQL的website_nku表中。
    这是一个更底层的、面向过程的实现，适合脚本调用。
        
        Args:
        data_dir (str): 包含JSON数据文件的目录。
        include_documents (bool): 是否解析和索引文档内容。
        batch_size (int): 批量插入数据库的大小。
        pagerank_db_path (str): PageRank得分的SQLite数据库路径。

        Returns:
        Dict[str, Any]: 索引构建的统计结果。
    """
    logger.info("开始构建MySQL索引...")
    start_time = datetime.now()
    
    # 默认数据目录
    if data_dir is None:
        data_dir = Config.get_path('etl.data.cleaned_data_dir')

    # 加载PageRank分数
    pagerank_scores = {}
    if pagerank_db_path:
        logger.info(f"从 {pagerank_db_path} 加载PageRank分数...")
        pagerank_scores = await _load_pagerank_scores_async(pagerank_db_path)
        logger.info(f"加载了 {len(pagerank_scores)} 个PageRank分数")

    # 初始化文档解析器
    doc_parser = DocumentProcessor() if include_documents else None

    # 发现所有JSON文件
    json_files = list(Path(data_dir).rglob("*.json"))
    total_files = len(json_files)
    logger.info(f"在 {data_dir} 中找到 {total_files} 个JSON文件。")

    # 并行处理文件
    tasks = [_process_file_async(file, pagerank_scores, doc_parser) for file in json_files]
    
    processed_count = 0
    success_count = 0
    failed_count = 0
    batch_data = []

    # 使用tqdm显示进度
    for future in tqdm(asyncio.as_completed(tasks), total=total_files, desc="Processing files"):
        record = await future
        processed_count += 1
        if record:
            batch_data.append(record)
            if len(batch_data) >= batch_size:
                inserted_count = await _insert_batch_async(batch_data)
                success_count += inserted_count
                failed_count += len(batch_data) - inserted_count
                batch_data = []
    
    # 插入剩余数据
    if batch_data:
        inserted_count = await _insert_batch_async(batch_data)
        success_count += inserted_count
        failed_count += len(batch_data) - inserted_count

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    stats = {
        "total_files": total_files,
        "processed_files": processed_count,
        "successfully_inserted": success_count,
        "failed_insertions": failed_count,
        "duration_seconds": duration,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }
    logger.info(f"MySQL索引构建完成。耗时: {duration:.2f}秒。结果: {stats}")
    return stats

async def _load_pagerank_scores_async(pagerank_db_path: str) -> Dict[str, float]:
    """异步从SQLite数据库加载PageRank分数。"""
    def _load_scores():
        """在线程池中运行的同步函数。"""
        try:
            conn = sqlite3.connect(pagerank_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT url, score FROM pagerank")
            scores = {row[0]: float(row[1]) for row in cursor.fetchall()}
            conn.close()
            return scores
        except sqlite3.Error as e:
            logger.error(f"从SQLite加载PageRank分数时出错: {e}")
            return {}
            
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _load_scores)

async def _process_file_async(
    json_file: Path, 
    pagerank_scores: Dict[str, float], 
    doc_parser: Optional[DocumentProcessor]
) -> Optional[Dict[str, Any]]:
    """异步处理单个JSON文件，提取和转换数据。"""
    try:
        async with aiofiles.open(json_file, 'r', encoding='utf-8') as f:
            content_str = await f.read()
        data = json.loads(content_str)

        original_url = data.get("original_url")
        if not original_url:
            logger.warning(f"文件 {json_file} 缺少 'original_url'，跳过。")
            return None

        content = data.get("content", "")
        # 如果是文档链接且内容为空，则解析文档
        if doc_parser and data.get("file_url") and not content.strip():
            try:
                loop = asyncio.get_running_loop()
                parsed_content = await loop.run_in_executor(
                    None, doc_parser.parse_from_url, data["file_url"]
                )
                if parsed_content:
                    content = parsed_content
            except Exception as e:
                logger.warning(f"文档解析失败 {data['file_url']}: {e}")
        
        # 内容和标题长度限制（必须在文档解析后进行）
        content = _truncate_content(content)
        title = _truncate_title(data.get("title", "无标题"))

        # 验证发布日期
        publish_time_str = data.get("publish_time")
        if not _is_valid_date(publish_time_str):
            publish_time_str = None

        return {
            "original_url": original_url,
            "title": title,
            "content": content,
            "author": data.get("source"),
            "publish_time": publish_time_str,
            "scrape_time": data.get("scrape_time", datetime.now().isoformat()),
            "platform": data.get("platform", "website"),
            "pagerank_score": pagerank_scores.get(original_url, 0.0),
            "is_official": 1 if "nankai.edu.cn" in original_url else 0,
        }
    except json.JSONDecodeError:
        logger.error(f"JSON解析失败: {json_file}")
        return None
    except Exception as e:
        logger.error(f"处理文件失败 {json_file}: {e}")
        return None

def _is_valid_date(date_str: str) -> bool:
    """检查日期字符串是否有效。"""
    if not date_str or not isinstance(date_str, str):
        return False
    try:
        # 尝试匹配几种常见格式
        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        if re.match(r'\d{4}年\d{2}月\d{2}日', date_str):
            datetime.strptime(date_str, '%Y年%m月%d日')
            return True
        # 可以根据需要添加更多格式
        return False
    except ValueError:
        return False

async def _insert_batch_async(batch_data: List[Dict[str, Any]]) -> int:
    """异步批量插入数据到MySQL。"""
    if not batch_data:
        return 0
    try:
        # db_core.batch_insert 应该是异步的
        inserted_count = await db_core.batch_insert("website_nku", batch_data)
        logger.debug(f"成功批量插入 {inserted_count} 条记录。")
        return inserted_count
    except Exception as e:
        logger.error(f"批量插入失败: {e}")
        return 0

# ... 可以在此添加主函数入口，用于脚本执行
# if __name__ == '__main__':
#     # 配置日志
#     logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
#     # 获取配置
#     config_loader = Config()
#     config = config_loader.get_config()
    
#     # 创建索引器实例
#     indexer = MySQLIndexer(config=config)
    
#     async def main():
#         # 1. 创建表（如果需要）
#         await indexer.create_tables()
        
#         # 2. 导入爬虫数据
#         data_dir = config['etl']['data']['cleaned_data_dir']
#         await indexer.import_crawler_data(data_dir, include_pagerank=False)
        
#         # 3. 更新PageRank分数
#         await indexer.update_pagerank_scores()
        
#         # 4. 获取统计信息
#         stats = await indexer.get_statistics()
#         logger.info(f"数据库统计信息: {stats}")

#     # 运行主异步函数
#     asyncio.run(main())

#     # 或者使用面向过程的构建函数
#     # asyncio.run(build_mysql_index(pagerank_db_path=config['etl']['pagerank']['db_path'])) 