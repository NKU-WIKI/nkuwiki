"""
微信小程序数据访问对象包
"""
from api.database.wxapp.post_dao import *
from api.database.wxapp.user_dao import *
from api.database.wxapp.notification_dao import *
from api.database.wxapp.follow_dao import *

__all__ = [
    # 帖子相关
    'create_post',
    'get_post_by_id',
    'get_posts',
    'update_post',
    'mark_post_deleted',
    'update_post_view_count',
    'like_post',
    'unlike_post',
    'favorite_post',
    'unfavorite_post',
    
    # 用户相关
    'get_user_by_openid',
    'create_user',
    'update_user',
    'update_user_login_time',
    'increment_user_likes_count',
    'decrement_user_likes_count',
    'increment_user_favorites_count',
    'decrement_user_favorites_count',
    
    # 通知相关
    'create_notification',
    'get_notification_by_id',
    'get_user_notifications',
    'mark_notification_read',
    'mark_notifications_read',
    'delete_notification',
    'get_unread_notification_count'
] 