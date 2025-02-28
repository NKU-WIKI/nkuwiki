import json
import re, os
from urllib.parse import urlparse
import lxml.etree as etree
import requests
from bs4 import BeautifulSoup

url_maps = {
    '文学院': 'http://wxy.nankai.edu.cn/', '历史学院': 'http://history.nankai.edu.cn/',
    '哲学院': 'http://phil.nankai.edu.cn/', '外国语学院': 'https://sfs.nankai.edu.cn/',
    '法学院': 'http://law.nankai.edu.cn/', '周恩来政府管理学院': 'http://zfxy.nankai.edu.cn/',
    '马克思主义学院': 'http://cz.nankai.edu.cn/', '汉语言文化学院': 'http://hyxy.nankai.edu.cn/',
    '经济学院': 'http://economics.nankai.edu.cn/', '商学院': 'http://bs.nankai.edu.cn/',
    '旅游与服务学院': 'http://tas.nankai.edu.cn/', '金融学院': 'http://finance.nankai.edu.cn/',
    '数学科学学院': 'http://math.nankai.edu.cn/', '物理科学学院': 'http://physics.nankai.edu.cn/',
    '化学学院': 'http://chem.nankai.edu.cn/', '生命科学学院': 'http://sky.nankai.edu.cn/',
    '环境科学与工程学院': 'http://env.nankai.edu.cn/', '医学院': 'http://medical.nankai.edu.cn/',
    '药学院': 'http://pharmacy.nankai.edu.cn/', '电子信息与光学工程学院': 'http://ceo.nankai.edu.cn/',
    '材料科学与工程学院': 'http://mse.nankai.edu.cn/', '计算机学院': 'http://cc.nankai.edu.cn/',
    '密码与网络空间安全学院': 'http://cyber.nankai.edu.cn/', '人工智能学院': 'http://ai.nankai.edu.cn/',
    '软件学院': 'http://cs.nankai.edu.cn/', '统计与数据科学学院': 'http://stat.nankai.edu.cn/',
    '新闻与传播学院': 'https://jc.nankai.edu.cn/', '社会学院': 'https://shxy.nankai.edu.cn/',
    '南开大学新闻网': 'https://news.nankai.edu.cn/', '南开大学': 'https://www.nankai.edu.cn/',
    '陈省身数学研究所': 'http://www.cim.nankai.edu.cn/', '组合数学中心': 'https://cfc.nankai.edu.cn/',
    '生物质资源化利用国家地方联合工程研究中心': 'https://nrcb.nankai.edu.cn/',
    '学生就业指导中心': 'https://career.nankai.edu.cn/', '南开大学教务部': 'https://jwc.nankai.edu.cn/',
    '南开大学研究生院': 'https://graduate.nankai.edu.cn/', '南开大学科学技术研究部': 'https://std.nankai.edu.cn/',
    '南开大学人事处': 'https://rsc.nankai.edu.cn/',
    '南开大学高校思想政治理论课马克思主义基本原理概论教材研究基地': 'https://jcjd.nankai.edu.cn/',
    '南开大学21世纪马克思主义研究院': 'https://21cnmarx.nankai.edu.cn/',
    '南开大学旅游与服务学院旅游实验教学中心': 'https://taslab.nankai.edu.cn/',
    '南开大学现代旅游业发展协同创新中心': 'https://tourism2011.nankai.edu.cn/',
    '南开大学元素有机化学国家重点实验室': 'http://skleoc.nankai.edu.cn/',
    '药物化学生物学国家重点实验室': 'https://sklmcb.nankai.edu.cn/',
    '南开大学化学实验教学中心': 'https://cec.nankai.edu.cn/',
    '功能高分子材料教育部重点实验室': 'https://klfpm.nankai.edu.cn/',
    '先进能源材料化学教育部重点实验室': 'https://aemc.nankai.edu.cn/',
    '化学化工学院': 'https://chem.lzu.edu.cn/',
}


def parse_metadata(file_path):
    dict_pattern = r"metadata\s*=\s*\{(.*?)\}"
    # 定义正则表达式匹配字典中的键值对
    pair_pattern = r"'(.*?)':\s*'([^']*)'"
    try:
        with open(file_path, 'r', encoding='utf8') as file:
            content = file.read()
            # 首先匹配整个字典
            dict_match = re.search(dict_pattern, content, re.DOTALL)
            if dict_match:
                dict_content = dict_match.group(1)
                # 在字典内容中匹配键值对
                pairs = re.findall(pair_pattern, dict_content)
                metadata = {key.strip(): value.strip() for key, value in pairs}
                return metadata
            else:
                print("未找到字典 'metadata'。")
                return None
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到，请检查文件路径是否正确。")
        return None
    except Exception as e:
        print(f"读取文件时发生错误：{e}")
        return None


def parse_func(file_path):
    pattern = r"def\s+_parse_one_url\([^)]*\):[^#]*?(?:(?:\n|\r|\r\n)[\s\S]*?(?=\ndef\s+)|\Z)"
    try:
        with open(file_path, 'r', encoding='utf8') as file:
            content = file.read()

            dict_match = re.search(pattern, content, re.DOTALL)
            if dict_match:
                # print("匹配到的函数内容：")
                return dict_match.group()
            else:
                print("未匹配到函数")
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到，请检查文件路径是否正确。")
        return None
    except Exception as e:
        print(f"读取文件时发生错误：{e}")
        return None


def urls(url):
    a = re.split('/', url)
    for j in a:
        if 'nankai.edu.cn' in j:
            return j
    return -1


data = {}


def main():
    msg = ''
    for key, value in data.items():
        parsed_url = urlparse(value)
        netloc = parsed_url.netloc
        print('=' * 50)
        print('url:', value)
        while True:
            test_url = input('test_url:')
            if 'http' in test_url:
                break
        ans = requests.get(test_url)
        content = ans.content.decode()
        tree = etree.HTML(content)
        title = None
        while title is None:
            title_xpath = input('title:')
            title = tree.xpath(f'{title_xpath}/text()')
            title = title[0].strip() if title else None
            print('获取的title:', title)
        pushtime = None
        while pushtime is None:
            pushtime_xpath = input('pushtime:')
            pushtime = tree.xpath(f'{pushtime_xpath}/text()')
            pushtime = pushtime[0].strip() if pushtime else None
            print('获取的pushtime:', pushtime)
            if pushtime == '':
                print('此处为空字符串，需要另行修改代码。')

        msg += fr"""
elif '{netloc}' in url:
# {key}\
#参考链接{test_url}
    tree = etree.HTML(ans)

    # 提取标题
    title = tree.xpath('{title_xpath}/text()')
    title = title[0].strip() if title else None

    # 提取发布时间
    pushtime = tree.xpath('{pushtime_xpath}/text()')
    pushtime = pushtime[0].strip() if pushtime else None

    # 提取内容
    b = BeautifulSoup(ans, 'lxml')
    t = b.find('div', attrs={{'class':'wp_articlecontent'}})
    content = t.text if t else ''

    img = tree.xpath('//img[@data-layer="photo"]')
    img = img[0].get('src') if img else None
    if img:
        if 'http' not in img:
            img = '{value}' + img

    if (img is None) and (content.replace('\xa0', '') == ''):
        pdf = b.find('div', attrs={{'class': "wp_pdf_player"}})
        if pdf is not None:
            pdf = '{value}' + pdf.get('pdfsrc')
        img = pdf
    return title, pushtime, content, img"""
        with open('尝试输出.py', 'w', encoding='utf8') as e:
            e.write(msg)


def check_occurrence(A, B):
    return A.count(B) == 1


def download_database():
    import requests
    from tqdm import tqdm

    url = 'http://120.26.224.151:2233/data/database'
    headers = {'auth': 'your_expected_auth_token'}

    response = requests.get(url, headers=headers, stream=True)
    total_size_in_bytes = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 Kibibyte

    with open('nk_database.db', 'wb') as file, tqdm(
            desc='Downloading nk_database.db',
            total=total_size_in_bytes,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(block_size):
            bar.update(len(data))
            file.write(data)


def from_database_to_csv():
    import sqlite3
    import csv

    # 连接到SQLite数据库
    conn = sqlite3.connect('nk_database.db')
    cursor = conn.cursor()

    # 查询数据表entries中的所有数据
    cursor.execute("SELECT * FROM entries")
    rows = cursor.fetchall()

    # 获取列名
    column_names = [description[0] for description in cursor.description]
    column_names.remove('content')
    print(column_names)

    # 每5000行保存为一个文件
    chunk_size = 3000
    num_chunks = (len(rows) + chunk_size - 1) // chunk_size  # 计算需要的文件数量

    for i in range(num_chunks):
        start = i * chunk_size
        end = start + chunk_size
        chunk = rows[start:end]

        # 构建文件名
        filename = f'./data_csv/entries_{i + 1}.csv'

        # 将数据写入CSV文件
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            csvwriter = csv.writer(csvfile)
            # 写入列名
            csvwriter.writerow(column_names)
            # 写入数据行
            csvwriter.writerows(chunk)

    # 关闭数据库连接
    conn.close()


def initialize_database():
    import sqlite3
    conn = sqlite3.connect('nk_2_update.db')
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


def from_database_to_txt():
    import sqlite3

    # 连接到SQLite数据库
    conn = sqlite3.connect('nk_database.db')
    cursor = conn.cursor()

    # 查询数据表entries中的所有数据
    cursor.execute("SELECT * FROM entries")
    rows = cursor.fetchall()

    # 打开一个文件以写入数据
    with open('output.txt', 'w', encoding='utf-8') as file:
        for row in rows:
            row_str = ""

            # 检查每个字段是否存在且不为空字符串，并添加到row_str中
            if row[1]:
                row_str += f"title: {row[1]}\n"
            if row[3]:
                row_str += f"url: {row[3]}\n"
            if row[2]:
                row_str += f"push_time: {row[2]}\n"
            if row[5]:
                row_str += f"file_url: {row[5]}\n"
            if row[6]:
                row_str += f"source: {row[6]}\n"

            # 如果row_str不为空，则写入文件
            if row_str:
                file.write(row_str + "\n")

    # 关闭数据库连接
    conn.close()

def from_database_to_json(dbpath):
    import sqlite3
    from tqdm import tqdm
    if not os.path.exists('./data_json'):
        os.mkdir('./data_json')
    for page_number in tqdm(range(46)):
        page_size = 1000 # 确保最小页码    # 计算ID范围（假设id从0开始）
        offset = (page_number - 1) * page_size
        # 连接到SQLite数据库
        conn = sqlite3.connect(dbpath)
        cursor = conn.cursor()
        # 获取表的列名
        cursor.execute("PRAGMA table_info(entries)")
        columns = [column[1] for column in cursor.fetchall()]
        # 带分页条件的查询（假设有id字段）
        cursor.execute("SELECT * FROM entries ORDER BY id LIMIT ? OFFSET ?", (page_size, offset))
        rows = cursor.fetchall()
        conn.close()
        data = [dict(zip(columns, row)) for row in rows]
        for d in data:
            # content = d['content'].replace(' ', '')
            # if len(content) > 1000:
            #     content = content[:1000] + '...'
            # d['content'] = content
            del d['content']
        with open(f'./data_json/data_{dbpath}_{page_number}.json','w',encoding='utf8') as e:
            e.write(json.dumps(data))


import sqlite3


def get_total_pages(database_path, table_name, page_size=1000):
    # 连接到SQLite数据库
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # 获取表中的总记录数
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_records = cursor.fetchone()[0]

    # 计算总页数
    total_pages = (total_records + page_size - 1) // page_size

    # 检查最后一页是否不满1000条数据
    last_page_records = total_records % page_size
    is_last_page_full = (last_page_records == page_size)

    # 关闭数据库连接
    cursor.close()
    conn.close()

    return total_pages, is_last_page_full


# 示例调用
# database_path = 'nk_2_update.db'
# table_name = 'entries'
# total_pages, is_last_page_full = get_total_pages(database_path, table_name)
# print(f"总页数: {total_pages}")
# print(f"最后一页是否满1000条数据: {'是' if is_last_page_full else '否'}")

def extract_date(text):
    from datetime import datetime
    # 定义正则表达式匹配日期
    pattern = r'\d{4}[-/]\d{1,2}[-/]\d{1,2}'

    # 搜索匹配的日期字符串
    match = re.search(pattern, text)

    if match:
        # 提取匹配的日期字符串
        date_str = match.group(0)

        # 将日期字符串转换为 datetime.date
        # 尝试不同的日期格式
        for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        # 如果无法匹配任何日期格式，返回 None
        return None
    else:
        return None

def get_title(url):
    ans = requests.get(url,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36 HBPC/12.1.4.300'})
    b = BeautifulSoup(ans.content.decode(),'lxml')
    title = b.find('title')
    if not title:
        return ''
    return title.text

def get_datestr_from_url(url:str):
    date_match = re.search(r"(\d{4}/\d{2}/\d{2})", url)

    if date_match:
        # 提取日期字符串并转换为 datetime.date 格式
        date_str = date_match.group(1).replace("/", "-")  # 将斜杠替换为短横线
        return date_str
    else:
        date_match = re.search(r"(\d{4}/\d{2}\d{2})", url)
        if date_match:
            # 提取日期字符串并转换为 datetime.date 格式
            date_str = date_match.group(1).replace("/", "-")  # 将斜杠替换为短横线
            date_str = date_str[:7]+'-'+date_str[7:]
            return date_str
        return ''

def update_date_by_parse(content,url):
    from parse_different_college import parse_function
    title, pushtime, content, img = parse_function(content,url)
    if not pushtime:
        pushtime=''
    if pushtime == '':
        print('发布时间为空，url:',url)
    return pushtime
def update_sqlite_data(dbpath):
    from tqdm import tqdm
    conn = sqlite3.connect(dbpath, check_same_thread=False)
    cursor = conn.cursor()
    # 查询 push_time 为空字符串的数据
    cursor.execute("SELECT id,url FROM entries WHERE push_time = ''")
    push_time_results = cursor.fetchall()

    # 查询 title 为空字符串的数据
    cursor.execute("SELECT id, url FROM entries WHERE title = ''")
    title_results = cursor.fetchall()

    session = requests.Session()
    session.headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36 HBPC/12.1.4.300'}
    # 处理 push_time 为空的记录
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False, slow_mo=1500)
        context = browser.new_context()
        page = context.new_page()
        for record_id, url in tqdm(push_time_results):
            if '/list' in url or 'page.psp' in url:
                cursor.execute("DELETE FROM entries WHERE id = ?", (record_id,))
                continue
            new_push_time = get_datestr_from_url(url)  # 调用函数获取新的 push_time
            if new_push_time == '':
                page.goto(url)
                content = page.content()
                new_push_time =update_date_by_parse(content,url)
                # page.wait_for_timeout(1000)
            cursor.execute("UPDATE entries SET push_time = ? WHERE id = ?", (new_push_time, record_id))
        context.close()
        browser.close()
    # 处理 title 为空的记录
    for record_id, url in tqdm(title_results):
        new_title = get_title(url)  # 调用函数获取新的 title
        # print(new_title)
        cursor.execute("UPDATE entries SET title = ? WHERE id = ?", (new_title, record_id))
    # 提交更改并关闭连接
    conn.commit()
    cursor.close()
    conn.close()



def create_col(cursor):
    table_name='entries'
    column_name = 'push_time_date'
    def column_exists(cursor, table_name, column_name):
        cursor.execute(f"PRAGMA table_info({table_name})")
        for column in cursor.fetchall():
            if column[1].lower() == column_name.lower():
                return True
        return False
    if not column_exists(cursor, table_name, column_name):
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} DATE NULL;")
        print("Column added.")
    else:
        print("Column already exists.")
def make_new_col_date_obj(dbpath):
    from tqdm import tqdm
    conn = sqlite3.connect(dbpath, check_same_thread=False)
    cursor = conn.cursor()
    create_col(cursor)
    # 查询 push_time 不为空字符串的数据
    cursor.execute("SELECT id,push_time FROM entries WHERE push_time != ''")
    push_time_results = cursor.fetchall()
    for record_id,pu in tqdm(push_time_results):
        date_ = extract_date(pu)
        cursor.execute("UPDATE entries SET push_time_date = ? WHERE id = ?", (date_, record_id))
    conn.commit()
    cursor.close()
    conn.close()
# update_sqlite_data('./nk_database.db')
# update_sqlite_data('./nk_2_update.db')
# # make_new_col_date_obj('./nk_database.db')
# make_new_col_date_obj('./nk_2_update.db')
# # from_database_to_json('nk_database.db')
# from_database_to_json('nk_2_update.db')

def update_mathcol(dbpath):
    from tqdm import tqdm
    conn = sqlite3.connect(dbpath, check_same_thread=False)
    cursor = conn.cursor()
    create_col(cursor)
    cursor.execute("SELECT id FROM entries WHERE url like '%//math.nankai.edu.cn%'")
    push_time_results = cursor.fetchall()
    for reid in tqdm(push_time_results):
        cursor.execute("UPDATE entries SET source = '数学科学学院' WHERE id = ?", (reid[0],))
    conn.commit()
    cursor.close()
    conn.close()
update_mathcol('./nk_database.db')
update_mathcol('./nk_2_update.db')