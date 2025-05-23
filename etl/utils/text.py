# 文本、模板、RAG、QA相关工具

# ====== template.py 内容 ======
QA_TEMPLATE = """\
    上下文信息如下：
    ----------
    {context_str}
    ----------
    请你基于上下文信息而不是自己的知识，回答以下问题，可以分点作答，如果上下文信息没有相关知识，可以回答不确定，不要复述上下文信息：
    {query_str}

    回答：\
    """
MERGE_TEMPLATE = """\
    上下文：
    ----------
    {context_str}
    ----------
    
    你将看到一个问题，和这个问题对应的参考答案

    请基于上下文知识而不是自己的知识补充参考答案，让其更完整地回答问题
    
    请注意，严格保留参考答案的每个字符，并将补充的内容和参考答案合理地合并，输出更长更完整的包含更多术语和分点的新答案
    
    请注意，严格保留参考答案的每个字符，并将补充的内容和参考答案合理地合并，输出更长更完整的包含更多术语和分点的新答案
    
    请注意，严格保留参考答案的每个字符，并将补充的内容和参考答案合理地合并，输出更长更完整的包含更多术语和分点的新答案

    问题：
    {query_str}

    参考答案：
    {answer_str}

    新答案：\
    """
SUMMARY_EXTRACT_TEMPLATE = """\
    这是这一小节的内容：
    {context_str}
    请用中文总结本节的关键主题和实体。

    总结：\
    """
HYDE_PROMPT_ORIGIN = """\
    Please write a passage to answer the question
    Try to include as many key details as possible
    {context_str}
    Passage:\
    """
HYDE_PROMPT_MODIFIED_V1 = """\
    你是系统运维专家，现在请你结合通信和系统运维的相关知识回答下列问题，
    请尽量包含更多你所知道的的关键细节。请详细分析可能的原因，提出有效的诊断步骤和解决方案。
    {context_str}
    请尽可能简洁的回答:\
    """
HYDE_PROMPT_MODIFIED_V2 = """\
    你是系统运维专家，现在请你结合通信和系统运维的相关知识回答下列问题，
    请详细分析可能的原因，返回有用的内容。
    {context_str}
    最终的回答请尽可能的精简:\
    """
HYDE_PROMPT_MODIFIED_MERGING = """\
    你是系统运维专家，现在请你结合通信和系统运维的相关知识回答下列问题，
    现在有给定一个问题，一个生成的可能可用的文档和一个检索出的相关的上下文信息，你需要将上述问题和信息总结为一个文档，
    要求：这个文档要包含尽可能多的关键细节，要求尽可能详细，但是不要复述上下文信息。
    {context_str}
    不需要阐述无关信息和无关注释和总结，只需要关键信息，最终的回答请尽可能的精简
    请按照要求作答：\
    """

# ====== qa.py 内容 ======
from typing import Iterable
import jsonlines

def read_jsonl(path):
    content = []
    with jsonlines.open(path, "r") as json_file:
        for obj in json_file.iter(type=dict, skip_invalid=True):
            content.append(obj)
    return content

def write_jsonl(path, content):
    with jsonlines.open(path, "w") as json_file:
        json_file.write_all(content)

def save_answers(
        queries: Iterable, results: Iterable, path: str = "data/answers.jsonl"
):
    answers = []
    for query, result in zip(queries, results):
        answers.append(
            {"id": query["id"], "query": query["query"], "answer": result}
        )
    # 保存答案到 data/answers.jsonl
    write_jsonl(path, answers)
    return answers

# ====== rag.py 内容 ======
import re
from llama_index.core.base.llms.types import CompletionResponse

def cut_sent(para):
    para = re.sub('([。！？\?])([^”’])', r"\1\n\2", para)  # 单字符断句符
    para = re.sub('(\.{6})([^”’])', r"\1\n\2", para)  # 英文省略号
    para = re.sub('(\…{2})([^”’])', r"\1\n\2", para)  # 中文省略号
    para = re.sub('([。！？\?][”’])([^，。！？\?])', r'\1\n\2', para)
    para = para.rstrip()
    return para.split("\n")

def filter_specfic_words(prompt):
    word_dict = {
        "支持\nZDB": "ZDB"
    }
    for key, value in word_dict.items():
        prompt = prompt.replace(key, value)
    return prompt

async def generation(llm, fmt_qa_prompt):
    cnt = 0
    while True:
        try:
            ret = await llm.acomplete(fmt_qa_prompt)
            return ret
        except Exception as e:
            print(e)
            cnt += 1
            if cnt >= 10:
                print(f"已达到最大生成次数{cnt}次，返回'无法确定'")
                return CompletionResponse(text="无法确定")
            print(f"已重复生成{cnt}次")

def deduplicate(contents):
    new_contents = []
    contentmap = dict()
    for content in contents:
        if content not in contentmap:
            contentmap[content] = 1
            new_contents.append(content)
    return new_contents

__all__ = [
    'QA_TEMPLATE', 'MERGE_TEMPLATE', 'SUMMARY_EXTRACT_TEMPLATE',
    'HYDE_PROMPT_ORIGIN', 'HYDE_PROMPT_MODIFIED_V1', 'HYDE_PROMPT_MODIFIED_V2', 'HYDE_PROMPT_MODIFIED_MERGING',
    'read_jsonl', 'write_jsonl', 'save_answers',
    'cut_sent', 'filter_specfic_words', 'generation', 'deduplicate'
] 