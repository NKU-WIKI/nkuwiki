import os.path
from typing import Sequence, List
from llama_index.core.extractors.interface import BaseExtractor
from llama_index.core.schema import BaseNode
from pydantic import Field


def filter_image(cap, title, text, content):
    # 过滤text中含有特殊内容的node
    ignore_words = [
        "流程", "，", "示例", "配置", "组网图", "（可选）", "文件"
    ]
    ignore_sentences = [f'{ignore_word}如{cap}所示' for ignore_word in ignore_words]
    for ignore_sentence in ignore_sentences:
        if ignore_sentence in text:
            return True
    # 过滤title中含有特殊内容的node
    ignore_words = ["架构", "结构", "组网图", "页面", "对话框", "配置", "导读", "流程", "协议", "实例"]
    for ignore_word in ignore_words:
        if ignore_word in title:
            return True
    # 过滤content中含有特殊内容的node
    ignore_words = ["架构图", "树形图", "网络拓扑图", "表格"]
    for ignore_word in ignore_words:
        if ignore_word in content:
            return True
    # 过滤不含有某个模式的node
    contains_sentences = [f'如{cap}所示']
    for contains_sentence in contains_sentences:
        if contains_sentence not in text:
            return True
    return False


class CustomFilePathExtractor(BaseExtractor):
    data_path: str = Field(description="原始数据根目录路径")
    last_path_length: int = Field(default=3, description="保留的路径层级数")

    def __init__(self, data_path: str, last_path_length: int = 3, **kwargs):
        super().__init__(data_path=data_path, last_path_length=last_path_length, **kwargs)

    async def aextract(self, nodes: Sequence[BaseNode]) -> list[dict]:
        return [node.metadata for node in self(nodes)]

    @classmethod
    def class_name(cls) -> str:
        return "CustomFilePathExtractor"

    def __call__(self, nodes: List[BaseNode]) -> List[BaseNode]:
        for node in nodes:
            # 从原始文件路径提取相对路径
            source_path = node.metadata.get("file_path", "")
            relative_path = os.path.relpath(source_path, self.data_path)
            
            # 生成知识路径
            path_parts = relative_path.split(os.sep)
            if len(path_parts) > self.last_path_length:
                know_path = os.sep.join(path_parts[-self.last_path_length:])
            else:
                know_path = relative_path
                
            # 更新元数据
            node.metadata.update({
                "know_path": know_path,
                "dir": os.path.dirname(relative_path)
            })
        return nodes


class CustomTitleExtractor(BaseExtractor):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def class_name(cls) -> str:
        return "CustomTitleExtractor"

    # 将Document的第一行作为标题
    async def aextract(self, nodes: Sequence[BaseNode]) -> list[dict]:
        try:
            document_title = nodes[0].text.split("\n")[0]
            last_file_path = nodes[0].metadata["file_path"]
        except:
            document_title = ""
            last_file_path = ""
        metadata_list = []
        for node in nodes:
            if node.metadata["file_path"] != last_file_path:
                document_title = node.text.split("\n")[0]
                last_file_path = node.metadata["file_path"]
            node.metadata["document_title"] = document_title
            metadata_list.append(node.metadata)

        return metadata_list
