import json
import requests

base_url = 'https://www.zhihu.com/api/v4/search_v3'
headers = {
    'cookie': 'z_c0=2|1:0|10:1741584017|4:z_c0|92:Mi4xVmFmR1N3QUFBQUJpOGxQYV81a2ZHaGNBQUFCZ0FsVk5rY1M3YUFDQXN5bTBOVmwyZkV6Z2J4SDl3R21lamwwWTNR|7c1d5a5f1ddea9d2feae7bedc80ded45166bd76ba1810a80df90b917960ca341,'
              'd_c0=YvJT2v-ZHxqPTgCRNSDSEe4x-WYkkFvE79o=|1741577343',  # 你的cookie
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
}

# 初始参数
params = {
    't': 'general',
    'q': '南开大学',  # 搜索关键词
    'correction': '1',
    'offset': '0',
    'limit': '20',  # 每页的数量
    'lc_idx': '0',
    'show_all_topics': '0',
}

# 获取对应页面的json数据
def get_page(params, headers):
    try:
        response = requests.get(base_url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            return None
    except requests.ConnectionError as e:
        print('Connection Error:', e)
        return None
    except requests.RequestException as e:
        print('Request Error:', e)
        return None

# 获取json数据
data = get_page(params, headers)

if data:
    # 解析数据
    for item in data.get('data', []):
        if 'object' in item:
            content = item['object']
            title = content.get('title', 'No Title')
            author = content.get('author', {}).get('name', 'Unknown')
            print(f"Title: {title}, Author: {author}")
else:
    print("No data retrieved.")

# 保存数据
if data:
    with open('recommend.json', 'w', encoding='utf-8') as file:
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        file.write(json_str)
else:
    print("No data to save.")

# 读取数据
try:
    with open('recommend.json', 'r', encoding='utf-8') as file:
        json_str = file.read()
        data = json.loads(json_str)
        if data and 'data' in data:
            data_list = data['data']
            num = len(data_list)
            # 接下来就是提取其中的信息，这需要观察json数据的格式，了解你所需要的数据的位置，然后一步步定位
            # 由于json中没有找到每条推荐对应的链接，所以需要自己根据json数据自己合成链接
            # 链接形如：https://www.zhihu.com/question/377886499/answer/1849697584
            for i in range(num):
                # 获取target字段，里面包含主要的链接信息
                target = data_list[i].get('target')
                if target:
                    id = target.get('id')
                    # 尝试获取question字段，如果失败则该条推荐不是文章类型
                    question = target.get('question', {})
                    if question:
                        question_id = question.get('id')
                        # 合成推荐内容的链接
                        url = 'https://www.zhihu.com/question/{q_id}/answer/{id}'.format(q_id=question_id, id=id)
                        title = question.get('title', 'No Title')
                        print('{title}\n{url}\n'.format(title=title, url=url))
        else:
            print("No 'data' field in JSON.")
except FileNotFoundError:
    print("File 'recommend.json' not found.")
except json.JSONDecodeError:
    print("Invalid JSON format in file.")
except KeyError as e:
    print(f"Key Error: {e}")