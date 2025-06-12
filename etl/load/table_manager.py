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

# 添加项目根目录到Python路径
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

from etl.load import db_core
from core.utils.logger import register_logger
from etl import config

# 创建模块专用日志记录器
logger = register_logger('etl.load.table_manager')

class TableManager:
    """统一数据库表管理器"""
    
    def __init__(self):
        """初始化表管理器"""
        self.sql_dir = Path(__file__).parent / "mysql_tables"
        self.logger = logger
        
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
        """应用配置文件中的默认值到SQL语句"""
        try:
            # 对微信小程序相关表应用特殊配置
            if table_name.startswith('wxapp_'):
                # 硬编码默认头像URL
                default_avatar = "cloud://cloud1-7gu881ir0a233c29.636c-cloud1-7gu881ir0a233c29-1352978573/avatar1.png"
                
                if "`avatar`" in sql_content:
                    # 查找avatar字段定义
                    start_idx = sql_content.find("`avatar`")
                    end_idx = sql_content.find(",", start_idx)
                    if end_idx == -1:
                        end_idx = sql_content.find(")", start_idx)
                    
                    if end_idx > start_idx:
                        avatar_def = sql_content[start_idx:end_idx]
                        
                        if f"DEFAULT '{default_avatar}'" not in avatar_def:
                            if "DEFAULT" in avatar_def:
                                new_avatar_def = re.sub(
                                    r'DEFAULT\s+[\'\"](.*?)[\'\"]', 
                                    f"DEFAULT '{default_avatar}'", 
                                    avatar_def
                                )
                            else:
                                new_avatar_def = avatar_def + f" DEFAULT '{default_avatar}'"
                            
                            sql_content = sql_content.replace(avatar_def, new_avatar_def)
                            self.logger.debug(f"为表{table_name}应用了默认头像配置")
            
            return sql_content
        except Exception as e:
            self.logger.error(f"应用配置默认值失败: {str(e)}")
            return sql_content
    
    async def recreate_tables(self, table_names: List[str] = None, force: bool = False, apply_defaults: bool = True) -> Dict[str, Any]:
        """重新创建表"""
        results = {"success": [], "failed": []}
        
        if table_names:
            # 验证指定的表
            sql_files = []
            for table_name in table_names:
                sql_file = self.sql_dir / f"{table_name}.sql"
                if sql_file.exists():
                    sql_files.append(sql_file)
                else:
                    self.logger.warning(f"表{table_name}的SQL文件不存在")
                    results["failed"].append(table_name)
        else:
            # 获取所有SQL文件
            sql_files = list(self.sql_dir.glob("*.sql"))
        
        if not sql_files:
            self.logger.warning("未找到可用的SQL文件")
            return results
        
        tables = [self.get_table_name_from_file(f) for f in sql_files]
        self.logger.info(f"将重新创建以下{len(tables)}个表: {', '.join(tables)}")
        
        if not force:
            confirm = input("此操作将删除并重新创建上述表，所有数据将丢失！确定继续吗？(y/n): ")
            if confirm.lower() != 'y':
                self.logger.info("操作已取消")
                return results
        
        # 删除并重新创建每个表
        for sql_file in tqdm(sql_files, desc="重建表", unit="个"):
            table_name = self.get_table_name_from_file(sql_file)
            
            try:
                # 删除表
                if not await self.drop_table(table_name):
                    results["failed"].append(table_name)
                    continue
                
                # 读取SQL内容
                sql_content = self.read_sql_file(sql_file)
                if not sql_content:
                    results["failed"].append(table_name)
                    continue
                
                # 应用配置默认值
                if apply_defaults:
                    sql_content = self.apply_config_defaults(sql_content, table_name)
                
                # 创建表
                if await self.create_table(table_name, sql_content):
                    results["success"].append(table_name)
                    self.logger.info(f"表{table_name}重新创建成功")
                else:
                    results["failed"].append(table_name)
                    
            except Exception as e:
                self.logger.error(f"重建表{table_name}时发生异常: {str(e)}")
                results["failed"].append(table_name)
        
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
            self.logger.error(f"导出表结构失败: {str(e)}")
            return False
    
    async def print_table_summary(self) -> None:
        """打印数据库表摘要信息"""
        try:
            tables = await self.list_all_tables()
            if not tables:
                print("数据库中没有表")
                return
            
            print('数据库表结构信息：')
            print('=' * 100)
            print(f'总计: {len(tables)} 个表')
            print('=' * 100)
            
            for table_name in tables:
                table_info = await self.get_table_info(table_name)
                if not table_info:
                    continue
                    
                print(f'\n表名: {table_name} (记录数: {table_info["record_count"]})')
                print('-' * 100)
                
                fields = table_info["fields"]
                print(f'{"字段名":<25}{"类型":<25}{"允许为空":<12}{"键":<10}{"默认值":<20}')
                print(f'{"-"*25:<25}{"-"*25:<25}{"-"*12:<12}{"-"*10:<10}{"-"*20:<20}')
                
                for field in fields:
                    field_name = field.get('Field', '')
                    field_type = field.get('Type', '')
                    nullable = field.get('Null', '')
                    key = field.get('Key', '')
                    default = str(field.get('Default', ''))
                    
                    print(f'{field_name:<25}{field_type:<25}{nullable:<12}{key:<10}{default:<20}')
                
        except Exception as e:
            self.logger.error(f"打印表摘要失败: {str(e)}")
    
    async def check_table_health(self) -> Dict[str, Any]:
        """检查数据库表健康状况"""
        health_report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tables": 0,
            "healthy_tables": 0,
            "issues": []
        }
        
        try:
            tables = await self.list_all_tables()
            health_report["total_tables"] = len(tables)
            
            for table_name in tables:
                try:
                    # 检查表是否可以正常查询
                    count_result = await db_core.execute_custom_query(f"SELECT COUNT(*) as total FROM {table_name}")
                    if count_result:
                        health_report["healthy_tables"] += 1
                    else:
                        health_report["issues"].append(f"表{table_name}查询返回空结果")
                        
                except Exception as e:
                    health_report["issues"].append(f"表{table_name}查询失败: {str(e)}")
            
            return health_report
        except Exception as e:
            health_report["issues"].append(f"健康检查过程出错: {str(e)}")
            return health_report

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='统一数据库表管理工具')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 重建表命令
    recreate_parser = subparsers.add_parser('recreate', help='重新创建表')
    recreate_parser.add_argument('--tables', nargs='+', help='指定要重建的表名')
    recreate_parser.add_argument('--force', action='store_true', help='强制执行，不提示确认')
    recreate_parser.add_argument('--no-defaults', action='store_true', help='不应用配置默认值')
    recreate_parser.add_argument('--wxapp-only', action='store_true', help='只重建wxapp_开头的表')
    
    # 列表命令
    list_parser = subparsers.add_parser('list', help='列出所有表')
    list_parser.add_argument('--detail', action='store_true', help='显示详细信息')
    
    # 导出命令
    export_parser = subparsers.add_parser('export', help='导出表结构')
    export_parser.add_argument('--output', '-o', help='输出文件路径')
    
    # 健康检查命令
    subparsers.add_parser('health', help='检查表健康状况')
    
    # 信息命令
    info_parser = subparsers.add_parser('info', help='显示表信息')
    info_parser.add_argument('table_name', help='表名')
    
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细日志')
    
    return parser.parse_args()

async def main():
    """主函数"""
    args = parse_args()
    
    if args.verbose:
        import sys
        from loguru import logger as global_logger
        global_logger.remove()
        global_logger.add(sys.stderr, level="DEBUG")
    
    manager = TableManager()
    
    try:
        # 测试数据库连接
        with db_core.get_connection():
            logger.debug("数据库连接测试成功")
    except Exception as e:
        logger.error(f"无法连接到数据库: {str(e)}")
        return 1
    
    if args.command == 'recreate':
        tables_to_recreate = args.tables
        
        if args.wxapp_only:
            available_tables = manager.get_available_table_definitions()
            tables_to_recreate = [t for t in available_tables if t.startswith('wxapp_')]
            logger.info(f"wxapp模式：将重建 {len(tables_to_recreate)} 个表")
        
        results = await manager.recreate_tables(
            table_names=tables_to_recreate,
            force=args.force,
            apply_defaults=not args.no_defaults
        )
        
        print(f"\n重建结果:")
        print(f"成功: {len(results['success'])} 个表")
        if results['success']:
            print(f"  - {', '.join(results['success'])}")
        print(f"失败: {len(results['failed'])} 个表")
        if results['failed']:
            print(f"  - {', '.join(results['failed'])}")
    
    elif args.command == 'list':
        if args.detail:
            await manager.print_table_summary()
        else:
            tables = await manager.list_all_tables()
            print(f"数据库中的表 (共{len(tables)}个):")
            for table in tables:
                print(f"  - {table}")
    
    elif args.command == 'export':
        success = await manager.export_table_structure(args.output)
        return 0 if success else 1
    
    elif args.command == 'health':
        health_report = await manager.check_table_health()
        print(f"数据库健康检查报告 ({health_report['timestamp']}):")
        print(f"总表数: {health_report['total_tables']}")
        print(f"健康表数: {health_report['healthy_tables']}")
        
        if health_report['issues']:
            print(f"发现问题 ({len(health_report['issues'])}个):")
            for issue in health_report['issues']:
                print(f"  - {issue}")
        else:
            print("✅ 所有表都正常")
    
    elif args.command == 'info':
        table_info = await manager.get_table_info(args.table_name)
        if table_info:
            print(json.dumps(table_info, ensure_ascii=False, indent=2, default=str))
        else:
            print(f"表 {args.table_name} 不存在或获取信息失败")
            return 1
    
    else:
        print("请指定一个命令。使用 --help 查看帮助。")
        return 1
    
    return 0

if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main())) 