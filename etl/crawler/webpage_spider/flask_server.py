import json
import os.path
from dotenv import load_dotenv
import shutil
from datetime import datetime, date, timedelta
from flask_cors import CORS
from apscheduler.triggers.interval import IntervalTrigger
from flask import Flask, request, send_file, abort, jsonify
from flask_apscheduler import APScheduler
from gevent import pywsgi
import sqlite3
import subprocess
import argparse
import logging


class Config:
    SCHEDULER_API_ENABLED = True
    SCHEDULER_API_PREFIX = '/apscheduler'


app = Flask(__name__)
app.config.from_object(Config)
scheduler = APScheduler()
scheduler.init_app(app)
load_dotenv()
header_key = load_dotenv()
logging.basicConfig(
    level=logging.INFO,  # 设置日志级别为 INFO
    format="%(asctime)s - %(levelname)s - %(message)s",  # 设置日志格式
    datefmt="%Y-%m-%d %H:%M:%S",  # 设置时间格式
    handlers=[logging.StreamHandler()]  # 指定日志输出到控制台
)

# 全局启用CORS并设置Access-Control-Max-Age
CORS(app, resources={
    r"/data/info": {
        "origins": ["*"],  # 替换为允许访问的域名
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "auth"],
        "max_age": 86400  # 设置Access-Control-Max-Age为86400秒
    },
    r"/data/search": {
        "origins": ["*"],  # 替换为允许访问的域名
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "auth"],
        "max_age": 86400  # 设置Access-Control-Max-Age为86400秒
    }
})


# cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
# cache.init_app(app)


# 添加 before_request 路由，验证 auth 字段
@app.before_request
def check_auth():
    auth_token = request.headers.get('auth')
    if request.method == 'OPTIONS':
        return '', 200
    if auth_token != header_key:  # 请替换为实际的认证令牌
        abort(404)  # 如果认证失败，返回 401 Unauthorized


# 添加 /data/log 路由，返回 ./counselor/scrapy.txt 文件
@app.route('/data/log')
def get_log():
    date_arg = request.args.get('date', f'{date.today().strftime("%Y-%m-%d")}')
    filename = f"./counselor/log/{date_arg}.txt"
    if not os.path.exists(filename):
        return jsonify({'msg': 'file did not exist.'})
    try:
        return send_file(filename)
    except FileNotFoundError:
        abort(404)  # 如果文件不存在，返回 404 Not Found





@app.route('/data/info', methods=['GET', 'OPTIONS'])
def get_data_for_html():
    return '等待适配',404
    # if request.method == "OPTIONS":
    #     # 处理预检请求
    #     return '', 200
    # page_size = 10
    # try:
    #     page_num = int(request.args.get('page_num'))
    # except:
    #     return '参数传递错误', 400
    # if not page_num:
    #     return '缺少参数', 400
    # offset = (page_num - 1) * page_size
    # conn = sqlite3.connect('./counselor/nk_2_update.db')
    # cursor = conn.cursor()
    # cursor.execute("SELECT title,content,url,push_time_date,source FROM entries ORDER BY push_time_date DESC LIMIT ? "
    #                "OFFSET ?",
    #                (page_size, offset))
    # # 获取列名并转换结果
    # results2 = []
    # for title, content, url, push_time_date, source in cursor.fetchall():
    #     results2.append({
    #         'title': title,
    #         'summary': content.replace(' ', '').replace('\n', '')[:50] + '...',
    #         'link': url,
    #         'date': push_time_date,
    #         'source': source
    #     })
    # conn.close()
    # return jsonify(results2)

@app.route('/data/search', methods=['POST'])
def search_data():
    return '等待适配',404
    # if request.method == "OPTIONS":
    #     # 处理预检请求
    #     return '', 200
    # query = request.json.get('query')
    # source =request.json.get('source')
    # if query:
    #     results2 = []
    #     conn = sqlite3.connect('./counselor/nk_2_update.db')
    #     cursor = conn.cursor()
    #     if source:
    #         cursor.execute(
    #             "SELECT title,content,url,push_time_date,source FROM entries WHERE source = ? AND title LIKE ? "
    #             " ORDER BY push_time_date DESC LIMIT 10",
    #             (source, '%' + query + '%'))
    #     else:
    #         cursor.execute(
    #             "SELECT title,content,url,push_time_date,source FROM entries WHERE title LIKE ? "
    #             "ORDER BY push_time_date DESC LIMIT 10",
    #             ('%' + query + '%', ))
    #
    #     for title, content, url, push_time_date, source in cursor.fetchall():
    #         results2.append({
    #             'title': title,
    #             'summary': content.replace(' ', '').replace('\n', '')[:50] + '...',
    #             'link': url,
    #             'date': push_time_date,
    #             'source': source
    #         })
    #     conn.close()
    #     conn = sqlite3.connect('./counselor/nk_database.db')
    #     cursor = conn.cursor()
    #     if source:
    #         cursor.execute(
    #             "SELECT title,content,url,push_time_date,source FROM entries WHERE source = ? AND title LIKE ? "
    #             "ORDER BY push_time_date DESC LIMIT 10",
    #             (source, '%' + query + '%' ))
    #     else:
    #         cursor.execute(
    #             "SELECT title,content,url,push_time_date,source FROM entries WHERE title LIKE ? "
    #             "ORDER BY push_time_date DESC LIMIT 10",
    #             ('%' + query + '%', ))
    #
    #     for title, content, url, push_time_date, source in cursor.fetchall():
    #         results2.append({
    #             'title': title,
    #             'summary': content.replace(' ', '').replace('\n', '')[:50] + '...',
    #             'link': url,
    #             'date': push_time_date,
    #             'source': source
    #         })
    #     conn.close()
    #     return jsonify(results2)
    # else:
    #     return jsonify([])


@scheduler.task('interval', name="使用scrapy获取数据", id='update_data', hours=6)
def run_counselor_script():
    import os,sqlite3
    path1 = 'nk_2_update.db'
    if 'counselor' not in os.getcwd():
        path1 = './counselor/' + path1
    print(path1)
    conn = sqlite3.connect(path1)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            push_time TEXT NOT NULL,
            url TEXT NOT NULL,
            content TEXT NOT NULL,
            file_url TEXT,
            source TEXT NOT NULL,
            push_time_date DATE NULL
        )
    ''')
    conn.commit()
    conn.close()
    # 使用 subprocess 模块运行外部脚本
    project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'counselor'))
    subprocess.run(['python', 'main.py'], cwd=project_path)
    from from_sqlite_to_mysql import export_web_to_mysql
    export_web_to_mysql(logger=logging)
    # 获取当前任务
    job = scheduler.get_job('update_data')
    if job:
        # 计算新的运行时间
        new_run_time = datetime.now() + timedelta(hours=6)
        # 更新任务的触发器为新的运行时间
        job.reschedule(IntervalTrigger(hours=6), next_run_time=new_run_time)








if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=2233)
    server = pywsgi.WSGIServer(('0.0.0.0', 2233), app)
    parser = argparse.ArgumentParser(description='Flask Server')
    parser.add_argument('-run', action='store_true', help='Run counselor script')
    args = parser.parse_args()
    try:
        if args.run:
            run_counselor_script()
        logging.info('启动服务器。')
        scheduler.start()
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down server and scheduler...")
        server.stop(timeout=60)  # 停止服务器
        scheduler.shutdown()  # 停止调度器
        print("Server and scheduler have been shut down.")
