#!/usr/bin/env python3
"""
修复用户头像脚本
为所有没有头像的用户设置默认头像
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

from etl.load.db_core import execute_query
from core.utils.logger import register_logger

# 创建脚本专用日志记录器
logger = register_logger('api.test.fix_avatars')

def main():
    """修复所有没有头像的用户记录"""
    try:
        logger.info("开始修复用户头像")
        
        # 获取默认头像URL
        default_avatar = "cloud://nkuwiki-0g6bkdy9e8455d93.6e6b-nkuwiki-0g6bkdy9e8455d93-1346872102/default/default-avatar.png"
        
        # 查询所有没有头像的用户
        users_without_avatar = execute_query(
            "SELECT id, openid, nickname FROM wxapp_user WHERE avatar IS NULL OR avatar = ''",
        )
        
        logger.info(f"找到 {len(users_without_avatar)} 个没有头像的用户")
        
        if not users_without_avatar:
            logger.info("所有用户都已有头像，无需修复")
            return
        
        # 更新用户头像
        for user in users_without_avatar:
            user_id = user['id']
            openid = user['openid']
            nickname = user['nickname']
            
            logger.info(f"修复用户头像: ID={user_id}, OpenID={openid}, Nickname={nickname}")
            
            # 更新用户头像
            execute_query(
                "UPDATE wxapp_user SET avatar = %s WHERE id = %s",
                [default_avatar, user_id],
                fetch=False
            )
        
        # 验证修复结果
        users_without_avatar_after = execute_query(
            "SELECT COUNT(*) as count FROM wxapp_user WHERE avatar IS NULL OR avatar = ''",
        )
        
        count_after = users_without_avatar_after[0]['count'] if users_without_avatar_after else 0
        
        if count_after == 0:
            logger.info("所有用户头像修复完成")
        else:
            logger.warning(f"仍有 {count_after} 个用户没有头像")
            
    except Exception as e:
        logger.error(f"修复用户头像失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 