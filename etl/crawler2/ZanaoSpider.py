import requests
import time
import execjs

# 定义API的URL地址
urls1 = {
    "list": "https://api.x.zanao.com/thread/v2/list",  # 获取列表的API地址
    "comment": "https://c.zanao.com/sc-api/comment/post", # 发送评论的API地址
    "search":"https://c.zanao.com/thread/v2/search",
    "hot":"https://c.zanao.com/thread/hot"
    
}
urls2 = {   "hot":"https://c.zanao.com/thread/hot",
         "comment": "https://c.zanao.com/sc-api/comment/post",
         "search":"https://c.zanao.com/thread/v2/search"}

# 存储用户认证信息的cookies
cookies = {
    'user_token': "YOUR_USER_TOKEN"
}

# 从本地文件读取JavaScript代码
with open("zanao1.js", "r", encoding="utf-8") as f:
    js = f.read()

def get_JS_result():
    """
    执行JavaScript代码并获取结果。

    使用execjs库编译并执行在 'zanao.js' 文件中的JavaScript代码，
    并调用 'get_result' 函数获取结果。

    返回:
        dict: 包含多个由JavaScript代码生成的键值对。
    """
    result = execjs.compile(js).call("get_result")
    return result

def get_headers():
    """
    生成并返回请求头。

    使用JavaScript函数生成特定的请求头参数。

    返回:
        dict: 包含HTTP请求所需的头部信息。
    """
    result = get_JS_result()
    headers = {
        'Accept': 'application/json, text/plain, */*',
        "X-Sc-Nd": result["X-Sc-Nd"],
        "X-Sc-Od": result["X-Sc-Od"],
        "X-Sc-Ah": result["X-Sc-Ah"],
        "X-Sc-Td": str(result["X-Sc-Td"]),
        'X-Sc-Alias': result["X-Sc-Alias"],
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090819) XWEB/8519 Flue'
    }
    return headers

def get_params(timestamp):
    """
    根据提供的时间戳生成并返回请求参数。

    参数:
        timestamp (int): 时间戳。

    返回:
        dict: 包含HTTP请求所需的参数。
    """
    params = {
        "from_time": str(timestamp),
        "hot": "1"
    }
    return params

def get_hot_list():
    """
    获取热门列表。

    通过发送HTTP POST请求到API端点，并处理响应数据，
    以获取热门话题列表。

    返回:
        list: 包含热门话题的列表，每个话题是一个字典。
    """
    url = urls1["list"]
    headers = get_headers()
    params = get_params(round(time.time()))
    responses = requests.post(url, headers=headers, params=params)
    list = responses.json()["data"]["list"]
    result = []
    for i in list:
        tmp = {
            "id": i["thread_id"],
            "title": i["title"],
            "content": i["content"],
            'finish_status': i['finish_status'],
            "nickname": i["nickname"]
        }
        result.append(tmp)
    return result

def post_comment(id, comment):
    """
    向指定ID的帖子发表评论。

    参数:
        id: 帖子ID。
        comment: 要发布的评论内容。

    返回:
        response: 服务器的响应对象。
    """
    url = urls1["comment"]
    headers = get_headers()
    data = {
        "id": id,
        "content": comment,
        "reply_comment_id": "0",
        "root_comment_id": "0",
        "cert_show": "0",
        "isIOS": "false"
    }
    response = requests.post(url, headers=headers, data=data,cookies=cookies)
    return response
def search_posts(query):
    """
    根据查询关键词搜索帖子。

    参数:
        query (str): 搜索关键词。

    返回:
        list: 包含搜索结果的列表，每个结果是一个字典。
    """
    url = urls1["search"]
    headers = get_headers()
    data = {
        "keyword": query,
        "page": 1,
        "page_size": 10
    }
    responses = requests.post(url, headers=headers, data=data)
    list = responses.json()["data"]["list"]
    result = []
    for i in list:
        tmp = {
            "id": i["thread_id"],
            "title": i["title"],
            "content": i["content"],
            'finish_status': i['finish_status'],
            "nickname": i["nickname"]
        }
        result.append(tmp)
    return result
# 从本地文件读取JavaScript代码
with open("zanao2.js", "r", encoding="utf-8") as f:
    js = f.read()

def get_JS_result():
 
    result = execjs.compile(js).call("get_result")
    return result

def get_headers():
   
    result = get_JS_result()
    headers = {
        'Accept': 'application/json, text/plain, */*',
        "X-Sc-Nd": result["X-Sc-Nd"],
        "X-Sc-Od": result["X-Sc-Od"],
        "X-Sc-Ah": result["X-Sc-Ah"],
        "X-Sc-Td": str(result["X-Sc-Td"]),
        'X-Sc-Alias': result["X-Sc-Alias"],
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090819) XWEB/8519 Flue'
    }
    return headers

def get_params(timestamp):
   
    params = {
        "from_time": str(timestamp),
        "hot": "1"
    }
    return params

def get_hot_list():
    """
    获取热门列表。

    通过发送HTTP POST请求到API端点，并处理响应数据，
    以获取热门话题列表。

    返回:
        list: 包含热门话题的列表，每个话题是一个字典。
    """
    url = urls2["list"]
    headers = get_headers()
    params = get_params(round(time.time()))
    responses = requests.post(url, headers=headers, params=params)
    list = responses.json()["data"]["list"]
    result = []
    for i in list:
        tmp = {
            "id": i["thread_id"],
            "title": i["title"],
            "content": i["content"],
            'finish_status': i['finish_status'],
            "nickname": i["nickname"]
        }
        result.append(tmp)
    return result

def post_comment(id, comment):
    """
    向指定ID的帖子发表评论。

    参数:
        id: 帖子ID。
        comment: 要发布的评论内容。

    返回:
        response: 服务器的响应对象。
    """
    url = urls2["comment"]
    headers = get_headers()
    data = {
        "id": id,
        "content": comment,
        "reply_comment_id": "0",
        "root_comment_id": "0",
        "cert_show": "0",
        "isIOS": "false"
    }
    response = requests.post(url, headers=headers, data=data,cookies=cookies)
    return response
# 从本地文件读取JavaScript代码
with open("zanao2.js", "r", encoding="utf-8") as f:
    js = f.read()

def get_JS_result():
    """
    执行JavaScript代码并获取结果。

    使用execjs库编译并执行在 'zanao.js' 文件中的JavaScript代码，
    并调用 'get_result' 函数获取结果。

    返回:
        dict: 包含多个由JavaScript代码生成的键值对。
    """
    result = execjs.compile(js).call("get_result")
    return result

def get_headers():
    """
    生成并返回请求头。

    使用JavaScript函数生成特定的请求头参数。

    返回:
        dict: 包含HTTP请求所需的头部信息。
    """
    result = get_JS_result()
    headers = {
        'Accept': 'application/json, text/plain, */*',
        "X-Sc-Nd": result["X-Sc-Nd"],
        "X-Sc-Od": result["X-Sc-Od"],
        "X-Sc-Ah": result["X-Sc-Ah"],
        "X-Sc-Td": str(result["X-Sc-Td"]),
        'X-Sc-Alias': result["X-Sc-Alias"],
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090819) XWEB/8519 Flue'
    }
    return headers

def get_params(timestamp):
    """
    根据提供的时间戳生成并返回请求参数。

    参数:
        timestamp (int): 时间戳。

    返回:
        dict: 包含HTTP请求所需的参数。
    """
    params = {
        "from_time": str(timestamp),
        "hot": "1"
    }
    return params

def get_hot_list():
    """
    获取热门列表。

    通过发送HTTP POST请求到API端点，并处理响应数据，
    以获取热门话题列表。

    返回:
        list: 包含热门话题的列表，每个话题是一个字典。
    """
    url = urls2["list"]
    headers = get_headers()
    params = get_params(round(time.time()))
    responses = requests.post(url, headers=headers, params=params)
    list = responses.json()["data"]["list"]
    result = []
    for i in list:
        tmp = {
            "id": i["thread_id"],
            "title": i["title"],
            "content": i["content"],
            'finish_status': i['finish_status'],
            "nickname": i["nickname"]
        }
        result.append(tmp)
    return result

def post_comment(id, comment):
    """
    向指定ID的帖子发表评论。

    参数:
        id: 帖子ID。
        comment: 要发布的评论内容。

    返回:
        response: 服务器的响应对象。
    """
    url = urls2["comment"]
    headers = get_headers()
    data = {
        "id": id,
        "content": comment,
        "reply_comment_id": "0",
        "root_comment_id": "0",
        "cert_show": "0",
        "isIOS": "false"
    }
    response = requests.post(url, headers=headers, data=data,cookies=cookies)
    return response
def search_posts(query):
    """
    根据查询关键词搜索帖子。

    参数:
        query (str): 搜索关键词。

    返回:
        list: 包含搜索结果的列表，每个结果是一个字典。
    """
    url = urls2["search"]
    headers = get_headers()
    data = {
        "keyword": query,
        "page": 1,
        "page_size": 10
    }
    responses = requests.post(url, headers=headers, data=data)
    list = responses.json()["data"]["list"]
    result = []
    for i in list:
        tmp = {
            "id": i["thread_id"],
            "title": i["title"],
            "content": i["content"],
            'finish_status': i['finish_status'],
            "nickname": i["nickname"]
        }
        result.append(tmp)
    return result