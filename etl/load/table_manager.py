#!/usr/bin/env python3
"""
统一表管理模块
整合所有数据库表管理功能，包括创建、删除、导出、修复等操作
"""
import os
import sys
import glob
import json
import time
import argparse
import re
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from tqdm import tqdm
import asyncio

# 调整导入路径，确保可以从项目根目录导入
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from etl.load import db_core
from core.utils.logger import register_logger
from config import Config
from etl.load.db_pool_manager import init_db_pool, close_db_pool

# 创建模块专用日志记录器
logger = register_logger('etl.load.table_manager')

class TableManager:
    """统一数据库表管理器"""
    
    def __init__(self):
        """初始化表管理器"""
        self.sql_dir = Path(__file__).parent / "mysql_tables"
        self.logger = logger
        self.config = Config()
        
    def get_table_name_from_file(self, file_path: Union[str, Path]) -> str:
        """从SQL文件名提取表名"""
        return Path(file_path).stem
    
    def read_sql_file(self, file_path: Union[str, Path]) -> Optional[str]:
        """读取SQL文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"读取SQL文件{file_path}失败: {str(e)}")
            return None
    
    def validate_table_name(self, table_name: str) -> bool:
        """验证表名是否合法"""
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name))
    
    async def drop_table(self, table_name: str) -> bool:
        """删除表"""
        if not self.validate_table_name(table_name):
            self.logger.error(f"非法表名: {table_name}")
            return False
            
        try:
            drop_sql = f"DROP TABLE IF EXISTS {table_name}"
            await db_core.execute_custom_query(drop_sql, fetch=False)
            self.logger.debug(f"表{table_name}已删除或不存在")
            return True
        except Exception as e:
            self.logger.error(f"删除表{table_name}失败: {str(e)}")
            return False
    
    async def create_table(self, table_name: str, sql_content: str = None) -> bool:
        """创建表"""
        if not self.validate_table_name(table_name):
            self.logger.error(f"非法表名: {table_name}")
            return False
            
        if not sql_content:
            # 从SQL文件读取内容
            sql_file = self.sql_dir / f"{table_name}.sql"
            if not sql_file.exists():
                self.logger.error(f"表{table_name}的SQL文件不存在: {sql_file}")
                return False
            sql_content = self.read_sql_file(sql_file)
            
        if not sql_content:
            self.logger.error(f"无法获取表{table_name}的SQL内容")
            return False
            
        try:
            await db_core.execute_custom_query(sql_content, fetch=False)
            self.logger.debug(f"表{table_name}创建成功")
            return True
        except Exception as e:
            self.logger.error(f"创建表{table_name}失败: {str(e)}")
            return False
    
    async def table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        try:
            sql = "SELECT COUNT(*) as count FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = %s"
            result = await db_core.execute_custom_query(sql, [table_name])
            return result[0]['count'] > 0 if result else False
        except Exception as e:
            self.logger.error(f"检查表{table_name}是否存在失败: {str(e)}")
            return False
    
    async def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """获取表的详细信息"""
        if not await self.table_exists(table_name):
            return None
            
        try:
            # 获取表结构
            fields_sql = f"DESCRIBE {table_name}"
            fields = await db_core.execute_custom_query(fields_sql)
            
            # 获取记录数
            count_sql = f"SELECT COUNT(*) as total FROM {table_name}"
            count_result = await db_core.execute_custom_query(count_sql)
            total_count = count_result[0]['total'] if count_result else 0
            
            # 获取表状态信息
            status_sql = "SELECT * FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = %s"
            status = await db_core.execute_custom_query(status_sql, [table_name])
            
            return {
                "name": table_name,
                "fields": fields,
                "record_count": total_count,
                "status": status[0] if status else None
            }
        except Exception as e:
            self.logger.error(f"获取表{table_name}信息失败: {str(e)}")
            return None
    
    async def list_all_tables(self) -> List[str]:
        """列出所有表"""
        try:
            return await db_core.get_all_tables()
        except Exception as e:
            self.logger.error(f"获取表列表失败: {str(e)}")
            return []
    
    def get_available_table_definitions(self) -> List[str]:
        """获取可用的表定义文件"""
        sql_files = list(self.sql_dir.glob("*.sql"))
        return [self.get_table_name_from_file(f) for f in sql_files]
    
    def apply_config_defaults(self, sql_content: str, table_name: str) -> str:
        """应用配置文件中的默认值到SQL建表语句"""
        if table_name == 'weapp_config':
            admin_openid = self.config.get("weapp.admin_openid", "default_admin_openid")
            sql_content = sql_content.replace("'{{ADMIN_OPENID}}'", f"'{admin_openid}'")
            self.logger.debug(f"已将weapp_config的默认管理员OPENID设置为: {admin_openid}")
        return sql_content
    
    async def recreate_tables(self, table_names: List[str] = None, force: bool = False, apply_defaults: bool = True) -> Dict[str, Any]:
        """重新创建表"""
        results = {"success": [], "failed": []}

        # 确定要处理的表定义
        if table_names:
            defined_sql_files = []
            for name in table_names:
                sql_file = self.sql_dir / f"{name}.sql"
                if sql_file.exists():
                    defined_sql_files.append(sql_file)
                else:
                    self.logger.warning(f"表 {name} 的SQL文件不存在，已跳过。")
                    results["failed"].append(name) # 记录为失败，因为它无法被创建
        else:
            defined_sql_files = list(self.sql_dir.glob("*.sql"))

        if not defined_sql_files:
            self.logger.warning("未找到可用的SQL文件进行操作。")
            return results

        defined_tables = {self.get_table_name_from_file(f) for f in defined_sql_files}
        self.logger.info(f"计划对以下 {len(defined_tables)} 个表进行重建操作: {', '.join(sorted(list(defined_tables)))}")

        if not force:
            self.logger.warning("此操作是破坏性的，将删除并重新创建表，所有现有数据都将丢失！")
            self.logger.warning("要执行此操作，请提供 --force 参数。")
            self.logger.info("操作已取消以防止意外数据丢失。")
            return results

        try:
            await db_core.execute_custom_query("SET FOREIGN_KEY_CHECKS=0;", fetch=False)
            self.logger.debug("已禁用外键检查")

            # 1. 删除已存在的表
            existing_tables = set(await self.list_all_tables())
            tables_to_drop = list(defined_tables.intersection(existing_tables))

            if tables_to_drop:
                self.logger.info(f"准备删除 {len(tables_to_drop)} 个已存在的表: {', '.join(sorted(tables_to_drop))}")
                drop_sql = f"DROP TABLE IF EXISTS {', '.join(f'`{t}`' for t in tables_to_drop)}"
                try:
                    await db_core.execute_custom_query(drop_sql, fetch=False)
                    self.logger.info("批量删除操作执行成功。")
                except Exception as e:
                    self.logger.error(f"批量删除表时发生错误: {e}。将尝试逐个删除。")
                    for table_name in tqdm(tables_to_drop, desc="回退：逐个删除旧表", unit="个"):
                        await self.drop_table(table_name) # drop_table 内部有日志记录
            else:
                self.logger.info("没有需要删除的已存在表。")

            # 2. 创建所有定义的表
            self.logger.info(f"准备创建 {len(defined_sql_files)} 个表...")
            for sql_file in tqdm(defined_sql_files, desc="创建新表", unit="个"):
                table_name = self.get_table_name_from_file(sql_file)
                try:
                    sql_content = self.read_sql_file(sql_file)
                    if not sql_content:
                        results["failed"].append(table_name)
                        continue

                    if apply_defaults:
                        sql_content = self.apply_config_defaults(sql_content, table_name)

                    if await self.create_table(table_name, sql_content):
                        results["success"].append(table_name)
                    else:
                        results["failed"].append(table_name)
                except Exception as e:
                    self.logger.error(f"创建表 {table_name} 时发生异常: {e}")
                    results["failed"].append(table_name)

        
        finally:
            # 无论如何，最后都要重新启用外键检查
            await db_core.execute_custom_query("SET FOREIGN_KEY_CHECKS=1;", fetch=False)
            self.logger.debug("已恢复外键检查")
            
        return results
    
    async def export_table_structure(self, output_file: str = None) -> bool:
        """导出所有表结构信息"""
        try:
            tables = await self.list_all_tables()
            if not tables:
                self.logger.warning("没有找到任何表")
                return False
            
            export_data = {
                "export_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_tables": len(tables),
                "tables": {}
            }
            
            for table_name in tqdm(tables, desc="导出表结构", unit="个"):
                table_info = await self.get_table_info(table_name)
                if table_info:
                    export_data["tables"][table_name] = table_info
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
                self.logger.info(f"表结构已导出到: {output_file}")
            else:
                # 输出到控制台
                print(json.dumps(export_data, ensure_ascii=False, indent=2, default=str))
            
            return True
        except Exception as e:
            self.logger.error(f"导出表结构失败: {e}")
            return False

    async def print_table_summary(self) -> None:
        """打印所有表的摘要信息"""
        try:
            tables = await self.list_all_tables()
            if not tables:
                self.logger.warning("数据库中没有找到任何表。")
                return

            self.logger.info(f"数据库摘要 (共 {len(tables)} 个表):")
            
            summaries = []
            for table_name in tqdm(tables, desc="获取表摘要", unit="个"):
                info = await self.get_table_info(table_name)
                if info:
                    summaries.append({
                        "name": info['name'],
                        "records": info['record_count'],
                        "create_time": info['status'].get('CREATE_TIME', 'N/A'),
                        "engine": info['status'].get('ENGINE', 'N/A'),
                    })
            
            # 格式化输出
            print("\n" + "="*80)
            print(f"{'表名':<30} {'记录数':>15} {'创建时间':>20} {'引擎':>10}")
            print("-" * 80)
            for s in summaries:
                create_time_str = str(s['create_time']) if s['create_time'] is not None else 'N/A'
                print(f"{s['name']:<30} {s['records']:>15} {create_time_str:>20} {s['engine']:>10}")
            print("=" * 80 + "\n")

        except Exception as e:
            self.logger.error(f"打印表摘要失败: {e}")

    async def check_table_health(self) -> Dict[str, Any]:
        """检查表健康状况"""
        health_status = {"healthy": [], "needs_attention": []}
        try:
            sql = "CHECK TABLE " + ", ".join(await self.list_all_tables())
            results = await db_core.execute_custom_query(sql)
            
            for row in results:
                if row['Msg_type'] == 'status' and row['Msg_text'] == 'OK':
                    health_status["healthy"].append(row['Table'])
                else:
                    health_status["needs_attention"].append({
                        "table": row['Table'],
                        "status": row
                    })
            
            self.logger.info(f"表健康检查完成: {len(health_status['healthy'])} 个健康, {len(health_status['needs_attention'])} 个需要关注")
            return health_status
        except Exception as e:
            self.logger.error(f"检查表健康状况失败: {e}")
            return health_status

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="NKUWiki 数据库表管理工具")
    parser.add_argument("--action", type=str, required=True, 
                        choices=["recreate", "summary", "export", "health"], 
                        help="要执行的操作")
    parser.add_argument("--tables", type=str, nargs='*', help="要操作的表名列表，不指定则为所有表")
    parser.add_argument("--force", action="store_true", help="强制执行，无需确认 (用于 'recreate')")
    parser.add_argument("--output-file", type=str, help="导出文件的路径 (用于 'export')")
    parser.add_argument("--apply-defaults", action="store_true", default=False, help="应用配置中的默认值到SQL")
    return parser.parse_args()


async def main():
    """主函数，处理命令行参数和执行相应操作"""
    args = parse_args()
    
    # 初始化数据库连接池
    await init_db_pool()
    manager = TableManager()
    
    start_time = time.time()
    
    if args.action == "recreate":
        results = await manager.recreate_tables(
            table_names=args.tables, 
            force=args.force, 
            apply_defaults=args.apply_defaults
        )
        logger.info(f"成功: {len(results['success'])} - {results['success']}")
        logger.info(f"失败: {len(results['failed'])} - {results['failed']}")
    elif args.action == "summary":
        await manager.print_table_summary()
    elif args.action == "export":
        await manager.export_table_structure(args.output_file)
    elif args.action == "health":
        await manager.check_table_health()
    else:
        logger.warning(f"未知操作: {args.action}")

    # 关闭连接池
    await close_db_pool()
    
    end_time = time.time()
    logger.info(f"操作 '{args.action}' 完成, 耗时: {end_time - start_time:.2f} 秒")


if __name__ == "__main__":
    asyncio.run(main())