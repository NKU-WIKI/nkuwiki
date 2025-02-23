from openai import OpenAI

# 构建client 并且绑定api_key和base_url
client = OpenAI(api_key="sk-nwJYUwA5G8qudUCM43A88e3a59Ea41F78b133148E1Be4f73",
                base_url="https://api.vveai.com")


def ask(question):
    """
    使用 OpenAI GPT-3.5 Turbo 模型模拟齐天大圣的角色回答问题。
    这个函数发送一个请求到 OpenAI 的 GPT-3.5 Turbo 模型，并设置场景为“齐天大圣用文言文回答问题”。该函数接收一个问题（以文言文的形式），并返回模型的回答。
    参数:
        question (str): 用户以文言文提出的问题。
    返回:
        str: 如果请求成功，返回模型生成的回答；如果出现异常，返回 False。
    异常处理:
        如果在请求过程中发生任何异常（如网络问题、API错误等），函数将捕获异常并返回 False。
    """
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {"role": "system", "content": "你现在需要扮演齐天大圣，用文言文跟我交流。"},
            {"role": "user", "content": question}
        ]
    )
    return completion.choices[0].message.content

