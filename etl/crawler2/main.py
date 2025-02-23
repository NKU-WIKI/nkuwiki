import json,time,os
import Logger
import ZanaoSpider
import ZanaoRobot

DATA_PATH = "data/Data.json"

def load_data(file_name):
    if os.path.exists(file_name):
        with open(file_name.format(file_name), "r", encoding="utf-8") as f:
            data = json.loads(f.read())
    else:
        data = []
    return data

def dump_data(file_name, data):
    with open(file_name.format(file_name), "w", encoding="utf-8") as f:
        f.write(json.dumps(data))

def get_uncommented_post(data):
    result = []
    hot_list = ZanaoSpider.get_hot_list()
    for hot in hot_list:
        if not (hot["id"] in data or hot['finish_status'] != "10"):
            result.append(hot)
        else:
            data.append(hot["id"])
    dump_data(DATA_PATH,data)
    return result

logger = Logger.Logger("log/log.txt")


while True:
    try:
        data = load_data(DATA_PATH)

        posts = get_uncommented_post(data)

        data = load_data(DATA_PATH)

        for hot in posts:
            question = ("发帖人网名；{{{}}} 帖子标题：{{{}}} 帖子内容：{{{}}}".format(
                hot["nickname"],hot["title"],hot["content"])).replace("\r\n", " ")

            msg = ZanaoRobot.ask(question)
            # comment_response = ZanaoSpider.post_comment(hot["id"],"{}".format(msg))
            data.append(hot["id"])
            logger.log("帖子ID:{} 帖子标题:{} 帖子内容:{} 回复内容:{}".format(hot["id"], hot["title"],
                                                                              hot["content"], msg)
                       .replace("\r\n", ""))
            time.sleep(10)
        dump_data(DATA_PATH, data)
        time.sleep(3600)
    except Exception as e:
        logger.log("发生错误...{}".format(e))
        dump_data(DATA_PATH, data)
        exit(-1)

