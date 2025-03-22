import sys
from pathlib import Path
import json
import time
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from etl import *
from config import Config

# 创建Blueprint
wxapp_export = Blueprint('wxapp_export', __name__)

# 获取配置
config = Config()
API_SECRET_KEY = config.get('etl.api.wxapp_export.secret_key', 'your_secret_key')

@wxapp_export.route('/export_data', methods=['POST'])
def export_data():
    """
    导出微信小程序数据的API接口
    
    请求参数:
    - collection: 集合名称 (posts, users)
    - api_key: API密钥
    - start_time: [可选] 开始时间，格式为ISO8601，用于增量导出
    
    返回:
    - success: 是否成功
    - message: 消息
    - data: 导出的数据
    """
    try:
        # 获取请求数据
        req_data = request.get_json()
        
        # 验证必要参数
        if not req_data:
            return jsonify({"success": False, "message": "缺少请求数据"}), 400
            
        collection = req_data.get('collection')
        api_key = req_data.get('api_key')
        start_time = req_data.get('start_time')
        
        if not collection:
            return jsonify({"success": False, "message": "缺少collection参数"}), 400
            
        if not api_key:
            return jsonify({"success": False, "message": "缺少api_key参数"}), 400
            
        # 验证API密钥
        if api_key != API_SECRET_KEY:
            logger.warning(f"API密钥验证失败: {api_key}")
            return jsonify({"success": False, "message": "API密钥无效"}), 401
        
        # 根据集合名称选择对应的数据处理方法
        if collection == 'posts':
            data = export_posts(start_time)
        elif collection == 'users':
            data = export_users(start_time)
        else:
            return jsonify({"success": False, "message": f"不支持的集合: {collection}"}), 400
            
        return jsonify({
            "success": True,
            "message": f"成功导出{len(data)}条{collection}数据",
            "data": data
        })
            
    except Exception as e:
        logger.error(f"导出数据时出错: {str(e)}")
        return jsonify({"success": False, "message": f"服务器错误: {str(e)}"}), 500

def export_posts(start_time=None):
    """
    导出帖子数据
    
    Args:
        start_time: 开始时间，格式为ISO8601
        
    Returns:
        List[Dict]: 帖子数据列表
    """
    from etl.load.py_mysql import execute_custom_query
    
    try:
        # 构建SQL查询
        query = """
            SELECT
                wxapp_id as _id,
                author_id as authorId,
                author_name as authorName,
                author_avatar as authorAvatar,
                content,
                title,
                likes,
                JSON_EXTRACT(liked_users, '$') as likedUsers,
                JSON_EXTRACT(favorite_users, '$') as favoriteUsers,
                comment_count as commentCount,
                JSON_EXTRACT(images, '$') as images,
                JSON_EXTRACT(tags, '$') as tags,
                create_time as createTime,
                update_time as updateTime,
                platform,
                status
            FROM wxapp_posts
            WHERE is_deleted = 0
        """
        
        params = []
        
        # 添加时间筛选条件
        if start_time:
            query += " AND create_time >= %s"
            # 解析ISO8601时间字符串
            try:
                start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                params.append(start_datetime)
            except ValueError:
                logger.error(f"无效的开始时间格式: {start_time}")
                return []
                
        # 添加排序
        query += " ORDER BY create_time DESC"
        
        # 执行查询
        results = execute_custom_query(query, params)
        if not results:
            return []
            
        # 处理查询结果
        posts = []
        for row in results:
            # 处理JSON字段
            post = dict(row)
            
            # 将JSON字符串转换为Python对象
            for json_field in ['likedUsers', 'favoriteUsers', 'images', 'tags']:
                if post.get(json_field):
                    try:
                        if isinstance(post[json_field], str):
                            post[json_field] = json.loads(post[json_field])
                    except json.JSONDecodeError:
                        post[json_field] = []
                else:
                    post[json_field] = []
                    
            # 处理时间字段
            for time_field in ['createTime', 'updateTime']:
                if isinstance(post.get(time_field), datetime):
                    post[time_field] = post[time_field].isoformat()
                    
            # 获取评论数据
            post['comments'] = get_comments_by_post_id(post['_id'])
            
            posts.append(post)
            
        return posts
        
    except Exception as e:
        logger.error(f"导出帖子数据时出错: {str(e)}")
        return []

def get_comments_by_post_id(post_id):
    """
    获取帖子的评论
    
    Args:
        post_id: 帖子ID
        
    Returns:
        List[Dict]: 评论数据列表
    """
    from etl.load.py_mysql import execute_custom_query
    
    try:
        # 构建SQL查询
        query = """
            SELECT
                wxapp_id as _id,
                post_id as postId,
                author_id as authorId,
                author_name as authorName,
                author_avatar as authorAvatar,
                content,
                JSON_EXTRACT(images, '$') as images,
                likes,
                JSON_EXTRACT(liked_users, '$') as likedUsers,
                create_time as createTime,
                update_time as updateTime,
                status
            FROM wxapp_comments
            WHERE post_id = %s AND is_deleted = 0
            ORDER BY create_time ASC
        """
        
        # 执行查询
        results = execute_custom_query(query, [post_id])
        if not results:
            return []
            
        # 处理查询结果
        comments = []
        for row in results:
            # 处理JSON字段
            comment = dict(row)
            
            # 将JSON字符串转换为Python对象
            for json_field in ['images', 'likedUsers']:
                if comment.get(json_field):
                    try:
                        if isinstance(comment[json_field], str):
                            comment[json_field] = json.loads(comment[json_field])
                    except json.JSONDecodeError:
                        comment[json_field] = []
                else:
                    comment[json_field] = []
                    
            # 处理时间字段
            for time_field in ['createTime', 'updateTime']:
                if isinstance(comment.get(time_field), datetime):
                    comment[time_field] = comment[time_field].isoformat()
                    
            comments.append(comment)
            
        return comments
        
    except Exception as e:
        logger.error(f"获取评论数据时出错: {str(e)}")
        return []

def export_users(start_time=None):
    """
    导出用户数据
    
    Args:
        start_time: 开始时间，格式为ISO8601
        
    Returns:
        List[Dict]: 用户数据列表
    """
    from etl.load.py_mysql import execute_custom_query
    
    try:
        # 构建SQL查询
        query = """
            SELECT
                wxapp_id as _id,
                openid,
                unionid,
                nickname as nickName,
                avatar_url as avatarUrl,
                gender,
                country,
                province,
                city,
                language,
                create_time as createTime,
                update_time as updateTime,
                last_login as lastLogin,
                status
            FROM wxapp_users
            WHERE is_deleted = 0
        """
        
        params = []
        
        # 添加时间筛选条件
        if start_time:
            query += " AND create_time >= %s"
            # 解析ISO8601时间字符串
            try:
                start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                params.append(start_datetime)
            except ValueError:
                logger.error(f"无效的开始时间格式: {start_time}")
                return []
                
        # 添加排序
        query += " ORDER BY create_time DESC"
        
        # 执行查询
        results = execute_custom_query(query, params)
        if not results:
            return []
            
        # 处理查询结果
        users = []
        for row in results:
            user = dict(row)
            
            # 处理时间字段
            for time_field in ['createTime', 'updateTime', 'lastLogin']:
                if isinstance(user.get(time_field), datetime):
                    user[time_field] = user[time_field].isoformat()
                    
            users.append(user)
            
        return users
        
    except Exception as e:
        logger.error(f"导出用户数据时出错: {str(e)}")
        return []

# API注册函数
def register_api(app):
    """
    将Blueprint注册到Flask应用
    
    Args:
        app: Flask应用实例
    """
    app.register_blueprint(wxapp_export, url_prefix='/api/wxapp')
    logger.debug("已注册微信小程序数据导出API: /api/wxapp/export_data")

# 当直接运行此文件时，启动一个简单的Flask服务器
if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    register_api(app)
    
    # 设置调试信息
    logger.info("启动微信小程序数据导出API服务...")
    logger.info(f"API密钥: {API_SECRET_KEY}")
    logger.info("请求示例: POST /api/wxapp/export_data")
    logger.info("请求体: {\"collection\": \"posts\", \"api_key\": \"your_secret_key\"}")
    
    # 启动服务器
    app.run(host="0.0.0.0", port=5000, debug=True) 