---
title: cozeAPI介绍
author: aokimi
---

随着字节在大模型军备竞赛中一骑绝尘，越来越多的小伙伴开始注意到扣子（COZE）这个强大的智能体工作流搭建平台。然而，不得不说，扣子的官方教程实在是出了名的草率，既没有示例代码，排版布局也十分混乱，扣子基础版、扣子专业版、豆包大模型、火山引擎、火山方舟让人傻傻分不清楚，混乱程度简直令人咋舌。

本文将提供官方文档没有提供的调用 COZE BOT API 的 Python 代码，关于豆包大模型的调用将在另一篇中详述。

一、基础知识
首先，扣子分为国内版和海外版，可以调用基础模型不一样，比如海外版可以调用Chat-GPT，但国内版不行。不过，海外版需要用到梯子，所以我们还是先以国内版为例，国内版的官网是这个：

扣子-AI 智能体开发平台
​www.coze.cn/
国内版又分为基础版和专业版（国外版好像是不分的），专业版和基础版登录的入口是不同的，而且你同一个账号下的专业版和基础版是不互通的，也就是说你在基础版里创建的智能体，不会自动出现在专业版的账号里，虽然可以进行迁移，但只能迁移一次，这点是最神奇的。

专业版和基础版在API调用限制上的区别如下：

基础版	专业版
COZE国内版API	2024年8月15日之后，扣子 API 的免费额度为每个账号 100 次 API 调用。一旦累计调用次数超过免费额度，此账号将无法继续使用任何扣子 API。
API 免费额度不适用于通过扣子平台、其他发布渠道或 SDK 产生的请求。	不限制 API 调用次数。
调用发起对话、执行工作流或执行工作流（流式响应）API，根据 Bot 调用次数和方舟模型 Token 消耗收取费用；调用恢复运行工作流，仅根据方舟模型 Token 消耗收取费用；调用其他接口免费。
总结起来就是，免费版有调用次数限制，且总共只有100次。所以如果100次不够用的小伙伴，就只能选择专业版了。

值得一提的是，专业版每次调用的收费分为两部分：

bot调用次数，就是调用一次智能体收一次费；
智能体消耗的token数，就是看你智能体里用到的大语言模型消耗的token，这一点和单独调用豆包一样；
不过，虽然是两道收费，但其实也不贵。首先，字节的大模型token收费可以说是国内所有大模型里的地板价了，比那些小厂的甚至可以低2个数量级；其次，智能体调用收费好像是调用一次扣2点，但现在有优惠，50万点1块钱，所以这个费用也就忽略不计了。

二、创建智能体
本篇文章主要是讲如何通过API来调用你已经创建好的智能体，所以创建智能体的部分就不再赘述啦，网上教程也越来越多，COZE在B站也有官方教程，可以参考一下：

扣子Coze个人主页
​space.bilibili.com/1444391473
注意，记得在专业版里创建，因为基础版里创建的话你只有100次的API调用机会。

专业版里的智能体调用大语言模型需要你创建接入点，这个我会另外出一个教程。

三、调用的前置准备
在调用COZE的API之前，确保你完成了以下两件事：

发布 Bot 为 API 服务，发布 Bot 时一定要勾选“Bot as API”；
获取访问令牌，这个在调用API时需要用到；
具体可以参考这个官方文档：

扣子 - 开发指南 - 准备工作
​www.coze.cn/docs/developer_guides/preparation
四、用Python调用Bot API
好，重头戏来了。

虽然扣子的官方文档写的不咋地，但我还是礼貌性地提供一下，毕竟先看官方文档是一个好习惯：

扣子 - 开发指南
​www.coze.cn/docs/developer_guides/coze_api_overview
（一）导入必要的库
import re
import requests
import json
import time
import sys
这几个是基础的，当然可能还有其他的，根据你的需求来。

（二）准备ID信息
bot_id = "你的BOT-ID"
access_token = 'Bearer pat_你的访问令牌'
user_id = "你的USER-ID"
如何获取bot_id和user_id：打开你的智能体编辑界面，网址的结构应该是这样的：

https://www.coze.cn/space/"你的USER-ID"/bot/"你的BOT-ID"
如何获取access_token：请参考上述“三、调用的前置准备”，请注意，令牌仅在生成时展示一次，请即刻复制并保存。另外，设置access_token 时不要忘记加上“Bearer pat_”的前缀。

（三）构建请求
api_url = 'https://api.coze.cn/v3/chat'
headers = {
    'Authorization': access_token,
    'Content-Type': 'application/json'
}    
body = {
    "bot_id": bot_id,  
    "user_id": user_id,  
    "stream": True,
    "auto_save_history": not(True),
    "additional_messages": messages
}
response = requests.post(api_url, headers=headers, json=body)
#print(response)
这里要注意，stream为True时，auto_save_history只能为False；stream为False时，auto_save_history只能为True，否则会报错。

messages就是常规格式，比如：

messages = [
            {"role": "system", "content": "你是智能助手",},
            {"role": "user", "content": "请回答我的问题",},
        ]
（四）流式输出
这里讲流式输出，我们先来了解一下流式输出的结构：

扣子 - 开发指南 - 流式输出结构
​www.coze.cn/docs/developer_guides/get_chat_response
流式输出的有效字段是在 event ='conversation.message.delta' 的前提下，data 返回值中的"content"，具体代码如下：

for line in response.iter_lines():
    decoded_line = line.decode('utf-8',errors='ignore')   #解码
    #print(decoded_line)
    if decoded_line.startswith("event:"):   #标记event
        event = decoded_line[6:]
        #print(event)
    if decoded_line.startswith("data:"):
        event_data = json.loads(decoded_line[5:])
        #print(event_data)
        if event == 'conversation.message.delta':   #流式输出标记   
            sys.stdout.write(event_data["content"])
            time.sleep(0.1)
流式输出有个前提，就是你的智能体最后一步是大语言模型的输出，或者你的智能体有消息模块来展示大语言模型的流式输出结果。假如你的智能体本身就无法将结果流式输出，那么通过API也是无法办到的。具体的你可以在自己的智能体编辑页面尝试一下，看看是不是能够流式输出。

（五）非流式输出
非流式输出反而更复杂一些。

你要设置 stream = false，auto_save_history=true，表示使用非流式响应，并记录历史消息。
你需要记录会话的 Conversation ID 和 Chat ID，用于后续查看详细信息。
定期轮询查看对话详情接口，建议每次间隔 1 秒以上，直到会话状态流转为终态，即 status 为 completed 或 required_action。
调用查看对话消息详情接口，查询模型生成的最终结果。
具体代码如下：

response = response.json()
#print(response)

conversation_id = response['data'].get('conversation_id')
chat_id = response['data'].get('id')
print(f'Chat_ID:{conversation_id};\nConversation_ID:{conversation_id}')

retrieve_url = f'https://api.coze.cn/v3/chat/retrieve?conversation_id={conversation_id}&chat_id={chat_id}'
while requests.get(retrieve_url, headers=headers).json()['data']['status'] != "completed":
    time.sleep(0.5)
    print("coze bot wait ......")

message_url = f'https://api.coze.cn/v3/chat/message/list?chat_id={chat_id}&conversation_id={conversation_id}'
message_response = requests.get(message_url, headers=headers).json()
event_data_answer = message_response['data'][1]
output = event_data_answer["content"]
print(output)
至此，COZE专业版API调用的核心部分就讲完啦，希望对大家有帮助。

（六）知识库召回结果
如果你的智能体里面有用到知识库，那么 Coze Bot 的返回结果里是有知识库的RAG召回结果的，甚至还有召回内容所在知识库的页面link，如果你需要的话，可以通过下面的方式调用：

知识库的召回内容是在 event = 'conversation.message.completed' 时（流式输出）且 event_data['type'] = 'verbose' 时，event_data_content["msg_type"] = "knowledge_recall" 下的内容，具体地，我们可以写出如下函数来解析响应的内容：

def get_coze_rag(event_data):
    
    result = list()
    
    if event_data['type']=='verbose':
        
        event_data_content = json.loads(event_data["content"])
        #print(json.dumps(event_data_content, indent=4,ensure_ascii=False))

        if event_data_content["msg_type"]=="knowledge_recall":
            event_data_content_data = json.loads(event_data_content["data"])
            #print(json.dumps(event_data_content_data, indent=4,ensure_ascii=False))
            
            event_chunks = event_data_content_data['chunks']
            for event_chunk in event_chunks:
                knowledge_slice = event_chunk['slice']
                result.append(knowledge_slice)
                knowledge_url = event_chunk['meta']['link']['url'].replace('u0026', '&')
                result.append(knowledge_url)
                
    return result
这个函数的输入是响应流event_data，输出的result为由召回片段和召回片段所在的知识库页面link组成的list。

由此，对于流式输出，我们的改写如下：

knowledge_results = []

for line in response.iter_lines():
    decoded_line = line.decode('utf-8',errors='ignore')   #解码
    #print(decoded_line)
    if decoded_line.startswith("event:"):   #标记event
        event = decoded_line[6:]
        #print(event)
    if decoded_line.startswith("data:"):
        event_data = json.loads(decoded_line[5:])
        #print(event_data)
        if event == 'conversation.message.delta':   #流式输出标记   
            sys.stdout.write(event_data["content"])
            time.sleep(0.1)
        if event == 'conversation.message.completed':   #知识库、最终完整输出标记
            knowledge_results = knowledge_results + get_coze_rag(event_data)

print(f"\n\n知识库召回片段：{knowledge_results}")
对于非流式输出，我们的改写如下：

response = response.json()
#print(response)

conversation_id = response['data'].get('conversation_id')
chat_id = response['data'].get('id')
print(f'Chat_ID:{conversation_id};\nConversation_ID:{conversation_id}')

retrieve_url = f'https://api.coze.cn/v3/chat/retrieve?conversation_id={conversation_id}&chat_id={chat_id}'
while requests.get(retrieve_url, headers=headers).json()['data']['status'] != "completed":
    time.sleep(0.5)
    print("coze bot wait ......")

message_url = f'https://api.coze.cn/v3/chat/message/list?chat_id={chat_id}&conversation_id={conversation_id}'
message_response = requests.get(message_url, headers=headers).json()

event_data_knowledge = message_response['data'][0]
knowledge_results = get_coze_rag(event_data_knowledge)

event_data_answer = message_response['data'][1]
output = event_data_answer["content"]

print(output)
print(f"\n知识库召回片段：{knowledge_results}")
上面所有代码均实测可用无报错，但也均预留了print调试接口，以供遇到bug时调试。当然，报错时求助大模型也是一个好主意（推荐DeepSeek）。

编辑于 2024-10-15 20:51・IP 属地上海
Python
API
coze专业版
​赞同 1​
​2 条评论
​分享
​喜欢
​收藏
​申请转载
​

赞同 1

​
分享

理性发言，友善互动

2 条评论
默认
最新
白笑猫
白笑猫
可以出个工作流API调用吗谢谢[爱]

02-21 · 广东
​回复
​1
DefinitelyFly
DefinitelyFly
作者
我找了一下 COZE好像不支持直接调用工作流哈 必须包装为智能体或者应用后才能发布API

03-10 · 上海
​回复
​喜欢
推荐阅读
基于coze创建自己的私人知识库
corz是字节跳动发布的“一站式AI开发平台“，看官方介绍为： Coze is a next-generation AI Bot development platform. Regardless of your programming experience, Coze enables you to e…

Ryan
人人都学得会用coze工作流搭建|保姆级工作流教程
之前我们写了一篇详细介绍如何通过coze搭建bot（机器人）的详细教程。 100%免费用GPT4 Turbo！Coze（扣子）平台保姆级创建bot（智能体）教程这篇阅读量还不错，今天我们来介绍一下比较难的 …

小吴科技屋
千亿参数，百万序列 | XTuner 超长上下文训练方案
千亿参数，百万序列 | XTuner 超长上下文训练方案
OpenMMLab
coze教程 | 04 工作流之大模型节点
1 大模型节点概述首先看一下大模型节点的配置： 配置可以看到5个部分： 1.1 模型这次介绍的是coze国内版，如果是海外版的话模型的选择是不一样的。根据自己的需求特别要注意一下模型的token…

荣姐聊AI
发表于AI智能体


选择语言
