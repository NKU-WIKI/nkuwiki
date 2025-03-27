"""
微信小程序数据访问对象包
"""
from api.database.wxapp.post_dao import *
from api.database.wxapp.user_dao import *
from api.database.wxapp.notification_dao import *
from api.database.wxapp.follow_dao import *
from api.database.wxapp.comment_dao import *
from api.database.wxapp.feedback_dao import *

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
    'get_users',
    'update_user',
    'upsert_user',
    'update_user_counter',
    'increment_user_likes_count',
    'decrement_user_likes_count',
    'increment_user_favorites_count',
    'decrement_user_favorites_count',
    'increment_user_posts_count',
    'decrement_user_posts_count',
    
    # 通知相关
    'create_notification',
    'get_notification_by_id',
    'get_user_notifications',
    'mark_notification_read',
    'mark_notifications_read',
    'mark_notification_deleted',
    'get_unread_notification_count',
    
    # 关注相关
    'follow_user',
    'unfollow_user',
    'check_follow_status',
    'get_user_followings',
    'get_user_followers',
    'update_following_count',
    'update_followers_count',
    'init_follow_table',
    
    # 评论相关
    'create_comment',
    'get_comment_by_id',
    'get_post_comments',
    'update_comment',
    'mark_comment_deleted',
    'like_comment',
    'unlike_comment',
    
    # 反馈相关
    'create_feedback',
    'get_feedback_by_id',
    'get_user_feedback',
    'update_feedback',
    'mark_feedback_deleted'
] 