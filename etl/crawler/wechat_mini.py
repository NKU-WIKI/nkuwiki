import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from etl import *
from etl.crawler.base_crawler import BaseCrawler
from etl.load.db_core import batch_insert, create_table, upsert_record
import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

class WeChatMiniCrawler(BaseCrawler):
    """
    微信小程序云数据库导出工具
    
    用于从微信小程序云数据库导出数据并导入到南开Wiki后端数据库
    支持全量导出和增量同步
    
    Attributes:
        db_mapping: 数据库表映射关系
    """
    
    def __init__(self, tag: str = "wxapp"):
        """
        初始化微信小程序爬虫
        
        Args:
            tag: 数据标签，默认为"wxapp"
        """
        super().__init__(tag=tag)
        self.logger = logger
        
        # 数据库表映射关系，定义微信小程序数据库表与南开Wiki数据库表的对应关系
        self.db_mapping = {
            "posts": "wxapp_posts",
            "users": "wxapp_users",
            "comments": "wxapp_comments"
        }
        
    async def async_init(self):
        """
        异步初始化，创建必要的数据库表
        """
        for _, table_name in self.db_mapping.items():
            self.logger.debug(f"确保表 {table_name} 已创建")
            create_table(table_name)
    
    async def fetch_data(self, collection: str, start_time: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        从微信小程序获取数据
        
        直接从微信小程序云数据库获取数据，不再通过API
        
        Args:
            collection: 集合名称（表名）
            start_time: 起始时间，用于增量同步，格式为ISO8601
            
        Returns:
            List[Dict[str, Any]]: 获取的数据列表
        """
        self.logger.debug(f"开始直接从云数据库获取集合 {collection} 的数据")
        
        try:
            # 这里应该改为直接从微信小程序云数据库获取数据的实现
            # 例如可以使用微信云开发的服务端SDK或者其他方式直接访问
            # 以下是一个示例实现，实际应根据具体情况修改
            
            # 为演示目的，这里返回空列表
            # 实际应该实现直接从小程序云数据库获取数据的逻辑
            return []
            
        except Exception as e:
            self.logger.error(f"获取数据时出错: {str(e)}")
            return []
            
    async def process_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        处理帖子数据，转换为南开Wiki数据库格式
        
        Args:
            posts: 原始帖子数据列表
            
        Returns:
            List[Dict[str, Any]]: 处理后的帖子数据列表
        """
        processed_posts = []
        
        for post in posts:
            # 处理字段映射和数据转换
            processed_post = {
                "wxapp_id": post.get("_id", ""),  # 保存原始ID
                "_openid": post.get("_openid", ""),  # 添加_openid字段
                "user_id": post.get("authorId", ""),
                "author_name": post.get("authorName", ""),
                "author_avatar": post.get("authorAvatar", ""),
                "content": post.get("content", ""),
                "title": post.get("title", ""),
                "likes": post.get("likes", 0),
                "liked_users": json.dumps(post.get("likedUsers", [])),
                "favorite_users": json.dumps(post.get("favoriteUsers", [])),
                "comment_count": len(post.get("comments", [])),
                "images": json.dumps(post.get("images", [])),
                "tags": json.dumps(post.get("tags", [])),
                "create_time": post.get("createTime", datetime.now().isoformat()),
                "update_time": post.get("updateTime", datetime.now().isoformat()),
                "platform": "wxapp",
                "status": post.get("status", 1),
                "is_deleted": 0
            }
            
            processed_posts.append(processed_post)
            
        return processed_posts
        
    async def process_users(self, users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        处理用户数据，转换为南开Wiki数据库格式
        
        Args:
            users: 原始用户数据列表
            
        Returns:
            List[Dict[str, Any]]: 处理后的用户数据列表
        """
        processed_users = []
        
        for user in users:
            # 处理字段映射和数据转换
            processed_user = {
                "wxapp_id": user.get("_id", ""),  # 保存原始ID
                "_openid": user.get("_openid", ""),  # 添加_openid字段
                "openid": user.get("openid", "") or user.get("_openid", ""),
                "unionid": user.get("unionid", ""),
                "nickname": user.get("nickName", ""),
                "avatar_url": user.get("avatarUrl", ""),
                "gender": user.get("gender", 0),
                "country": user.get("country", ""),
                "province": user.get("province", ""),
                "city": user.get("city", ""),
                "language": user.get("language", ""),
                "create_time": user.get("createTime", datetime.now().isoformat()),
                "update_time": user.get("updateTime", datetime.now().isoformat()),
                "last_login": user.get("lastLogin", datetime.now().isoformat()),
                "status": user.get("status", 1),
                "is_deleted": 0
            }
            
            processed_users.append(processed_user)
            
        return processed_users
    
    async def process_comments(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从帖子中提取评论数据，转换为南开Wiki数据库格式
        
        Args:
            posts: 原始帖子数据列表
            
        Returns:
            List[Dict[str, Any]]: 处理后的评论数据列表
        """
        all_comments = []
        
        for post in posts:
            post_id = post.get("_id", "")
            comments = post.get("comments", [])
            
            for comment in comments:
                processed_comment = {
                    "wxapp_id": comment.get("_id", ""),  # 保存原始ID
                    "post_id": post_id,
                    "_openid": comment.get("_openid", ""),  # 添加_openid字段
                    "user_id": comment.get("authorId", ""),
                    "author_name": comment.get("authorName", ""),
                    "author_avatar": comment.get("authorAvatar", ""),
                    "content": comment.get("content", ""),
                    "images": json.dumps(comment.get("images", [])),
                    "likes": comment.get("likes", 0),
                    "liked_users": json.dumps(comment.get("likedUsers", [])),
                    "create_time": comment.get("createTime", datetime.now().isoformat()),
                    "update_time": comment.get("updateTime", datetime.now().isoformat()),
                    "status": comment.get("status", 1),
                    "is_deleted": 0
                }
                
                all_comments.append(processed_comment)
        
        return all_comments
        
    async def import_to_database(self, collection: str, data: List[Dict[str, Any]]) -> int:
        """
        将数据导入到MySQL数据库
        
        Args:
            collection: 集合名称
            data: 处理后的数据列表
            
        Returns:
            int: 导入的记录数
        """
        if not data:
            self.logger.debug(f"没有数据需要导入到 {collection}")
            return 0
            
        table_name = self.db_mapping.get(collection)
        if not table_name:
            self.logger.error(f"未找到 {collection} 对应的数据库表")
            return 0
            
        try:
            # 使用批量插入函数导入数据
            count = batch_insert(table_name, data, batch_size=100)
            self.logger.info(f"成功导入 {count} 条记录到表 {table_name}")
            return count
        except Exception as e:
            self.logger.error(f"导入数据到表 {table_name} 时出错: {str(e)}")
            return 0
            
    async def scrape(self, full_sync: bool = False) -> Dict[str, Any]:
        """
        执行数据抓取和同步
        
        Args:
            full_sync: 是否执行全量同步，默认为增量同步
            
        Returns:
            Dict[str, Any]: 同步结果统计
        """
        self.logger.info(f"开始{'全量' if full_sync else '增量'}同步微信小程序数据")
        result = {
            "status": "success",
            "stats": {
                "posts": 0,
                "users": 0,
                "comments": 0
            },
            "errors": []
        }
        
        try:
            # 获取最后同步时间，用于增量同步
            start_time = None
            if not full_sync:
                # 这里可以从配置或数据库中获取上次同步时间
                # 暂时使用一个简单的方式，实际应用中应该改进
                last_sync_file = CACHE_PATH / f"{self.tag}_last_sync.txt"
                if last_sync_file.exists():
                    start_time = last_sync_file.read_text().strip()
            
            # 1. 获取并处理帖子数据
            posts_data = await self.fetch_data("posts", start_time)
            processed_posts = await self.process_posts(posts_data)
            posts_count = await self.import_to_database("posts", processed_posts)
            result["stats"]["posts"] = posts_count
            
            # 2. 获取并处理用户数据
            users_data = await self.fetch_data("users", start_time)
            processed_users = await self.process_users(users_data)
            users_count = await self.import_to_database("users", processed_users)
            result["stats"]["users"] = users_count
            
            # 3. 从帖子中提取并处理评论数据
            processed_comments = await self.process_comments(posts_data)
            comments_count = await self.import_to_database("comments", processed_comments)
            result["stats"]["comments"] = comments_count
            
            # 记录本次同步时间，用于下次增量同步
            current_time = datetime.now().isoformat()
            sync_file = CACHE_PATH / f"{self.tag}_last_sync.txt"
            sync_file.write_text(current_time)
            
            self.logger.info(f"同步完成，导入统计: 帖子={posts_count}, 用户={users_count}, 评论={comments_count}")
            
        except Exception as e:
            error_msg = f"同步过程中出错: {str(e)}"
            self.logger.error(error_msg)
            result["status"] = "error"
            result["errors"].append(error_msg)
            
        return result

# 测试代码
async def main():
    """测试微信小程序数据同步"""
    # 初始化爬虫，去掉API URL和密钥参数
    crawler = WeChatMiniCrawler()
    
    # 执行初始化
    await crawler.async_init()
    
    # 执行同步，默认为增量同步
    result = await crawler.scrape(full_sync=False)
    
    # 输出结果
    logger.info(f"同步结果: {result}")

if __name__ == "__main__":
    asyncio.run(main()) 