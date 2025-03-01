def run_counselor_script():
    """
        一个定时任务，为后续的cron使用。注意工作目录为/webpage_spider文件夹下
    Returns:

    """
    import os,sqlite3,subprocess,logging
    logging.basicConfig(
        level=logging.INFO,  # 设置日志级别为 INFO
        format="%(asctime)s - %(levelname)s - %(message)s",  # 设置日志格式
        datefmt="%Y-%m-%d %H:%M:%S",  # 设置时间格式
        handlers=[logging.StreamHandler()]  # 指定日志输出到控制台
    )

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

if __name__ == '__main__':
    run_counselor_script()