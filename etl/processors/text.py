"""
文本处理器

整合文本分割、层次化解析等文本处理功能
"""

from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union
import uuid
import sys
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))


from llama_index.core.bridge.pydantic import Field
from llama_index.core.callbacks.base import CallbackManager
from llama_index.core.callbacks.schema import CBEventType, EventPayload
from llama_index.core.node_parser.interface import NodeParser
from llama_index.core.schema import BaseNode, Document, NodeRelationship, TextNode, RelatedNodeInfo
from llama_index.core.utils import get_tqdm_iterable
from llama_index.core.node_parser import TextSplitter as BaseTextSplitter

# 直接在此模块中定义SentenceSplitter
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple, ClassVar, Any

from pydantic import Field, model_validator, PrivateAttr
from llama_index.core.callbacks.schema import CBEventType, EventPayload
from llama_index.core.constants import DEFAULT_CHUNK_SIZE
from llama_index.core.node_parser.interface import MetadataAwareTextSplitter
from llama_index.core.node_parser.node_utils import default_id_func
from llama_index.core.node_parser.text.utils import (
    split_by_char,
    split_by_regex,
    split_by_sentence_tokenizer,
    split_by_sep,
)
from llama_index.core.utils import get_tokenizer

SENTENCE_CHUNK_OVERLAP = 200
CHUNKING_REGEX = "[^,.;。？！]+[,.;。？！]?"
DEFAULT_PARAGRAPH_SEP = "\n\n\n"


@dataclass
class _Split:
    text: str  # the split text
    is_sentence: bool  # save whether this is a full sentence
    token_size: int  # token length of split text


class SentenceSplitter(MetadataAwareTextSplitter):
    """句子分割器，尽可能保持句子和段落完整"""

    chunk_size: int = Field(
        default=DEFAULT_CHUNK_SIZE,
        description="每个chunk的token大小",
        gt=0,
    )
    chunk_overlap: int = Field(
        default=SENTENCE_CHUNK_OVERLAP,
        description="分割时每个chunk的token重叠",
        gte=0,
    )
    separator: str = Field(
        default=" ", description="分割成单词的默认分隔符"
    )
    paragraph_separator: str = Field(
        default=DEFAULT_PARAGRAPH_SEP, description="段落间分隔符"
    )
    secondary_chunking_regex: str = Field(
        default=CHUNKING_REGEX, description="分割成句子的备用正则表达式"
    )
    include_metadata: bool = Field(
        default=True, description="是否在分割中包含元数据"
    )
    include_prev_next_rel: bool = Field(
        default=True, description="是否包含前后关系"
    )
    tokenizer: Optional[Callable] = Field(
        default=None, description="可选的tokenizer"
    )
    chunking_tokenizer_fn: Optional[Callable[[str], List[str]]] = Field(
        default=None, description="可选的chunking tokenizer函数"
    )
    callback_manager: Optional[CallbackManager] = Field(
        default=None, description="回调管理器"
    )
    id_func: Optional[Callable[[int, Document], str]] = Field(
        default=None, description="生成ID的函数"
    )

    # 私有属性
    _chunking_tokenizer_fn: Callable[[str], List[str]] = PrivateAttr(default=None)
    _tokenizer: Callable = PrivateAttr(default=None)
    _split_fns: List[Callable] = PrivateAttr(default=None)
    _sub_sentence_split_fns: List[Callable] = PrivateAttr(default=None)

    @model_validator(mode='after')
    def init_private_attrs(self) -> 'SentenceSplitter':
        """在创建模型后初始化私有属性"""
        if self.chunk_overlap > self.chunk_size:
            raise ValueError(
                f"chunk重叠({self.chunk_overlap})大于chunk大小({self.chunk_size})"
            )
        
        self.id_func = self.id_func or default_id_func
        self.callback_manager = self.callback_manager or CallbackManager([])
        
        self._chunking_tokenizer_fn = (
                self.chunking_tokenizer_fn or split_by_sentence_tokenizer()
        )
        self._tokenizer = self.tokenizer or get_tokenizer()

        self._split_fns = [
            split_by_sep(self.paragraph_separator),
            self._chunking_tokenizer_fn,
        ]

        self._sub_sentence_split_fns = [
            split_by_regex(self.secondary_chunking_regex),
            split_by_sep(self.separator),
            split_by_char(),
        ]
        return self

    @classmethod
    def from_defaults(
            cls,
            separator: str = " ",
            chunk_size: int = DEFAULT_CHUNK_SIZE,
            chunk_overlap: int = SENTENCE_CHUNK_OVERLAP,
            tokenizer: Optional[Callable] = None,
            paragraph_separator: str = DEFAULT_PARAGRAPH_SEP,
            chunking_tokenizer_fn: Optional[Callable[[str], List[str]]] = None,
            secondary_chunking_regex: str = CHUNKING_REGEX,
            callback_manager: Optional[CallbackManager] = None,
            include_metadata: bool = True,
            include_prev_next_rel: bool = True,
    ) -> "SentenceSplitter":
        """使用参数初始化"""
        return cls(
            separator=separator,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            tokenizer=tokenizer,
            paragraph_separator=paragraph_separator,
            chunking_tokenizer_fn=chunking_tokenizer_fn,
            secondary_chunking_regex=secondary_chunking_regex,
            callback_manager=callback_manager,
            include_metadata=include_metadata,
            include_prev_next_rel=include_prev_next_rel,
        )

    @classmethod
    def class_name(cls) -> str:
        return "SentenceSplitter"

    def split_text_metadata_aware(self, text: str, metadata_str: str) -> List[str]:
        metadata_len = len(self._tokenizer(metadata_str))
        effective_chunk_size = self.chunk_size
        if effective_chunk_size <= 0:
            raise ValueError(f"元数据长度({metadata_len})大于chunk大小({self.chunk_size})")
        elif effective_chunk_size < 50:
            print(f"元数据长度({metadata_len})接近chunk大小({self.chunk_size})")

        return self._split_text(text, chunk_size=effective_chunk_size)

    def split_text(self, text: str) -> List[str]:
        return self._split_text(text, chunk_size=self.chunk_size)

    def _split_text(self, text: str, chunk_size: int) -> List[str]:
        """分割文本并返回具有重叠大小的chunks"""
        if text == "":
            return [text]

        with self.callback_manager.event(
                CBEventType.CHUNKING, payload={EventPayload.CHUNKS: [text]}
        ) as event:
            splits = self._split(text, chunk_size)
            chunks = self._merge(splits, chunk_size)
            event.on_end(payload={EventPayload.CHUNKS: chunks})

        return chunks

    def _split(self, text: str, chunk_size: int) -> List[_Split]:
        """将文本分解为小于chunk大小的分割"""
        token_size = self._token_size(text)
        if token_size <= chunk_size:
            return [_Split(text, is_sentence=True, token_size=token_size)]

        text_splits_by_fns, is_sentence = self._get_splits_by_fns(text)

        text_splits = []
        for text_split in text_splits_by_fns:
            token_size = self._token_size(text_split)
            if token_size <= chunk_size:
                text_splits.append(_Split(text_split, is_sentence=is_sentence, token_size=token_size))
            else:
                recursive_text_splits = self._split(text_split, chunk_size=chunk_size)
                text_splits.extend(recursive_text_splits)
        return text_splits

    def _merge(self, splits: List[_Split], chunk_size: int) -> List[str]:
        """合并分割为最终chunks"""
        chunks: List[str] = []
        cur_chunk: List[Tuple[str, int]] = []
        last_chunk: List[Tuple[str, int]] = []
        cur_chunk_len = 0
        last_chunk_len = 0

        def close_chunk() -> None:
            nonlocal chunks, cur_chunk, last_chunk, cur_chunk_len, last_chunk_len

            chunks.append("".join([text for text, length in cur_chunk]))
            last_chunk = cur_chunk
            last_chunk_len = cur_chunk_len
            cur_chunk = []
            cur_chunk_len = 0

        for split in splits:
            cur_chunk_len += split.token_size
            cur_chunk.append((split.text, split.token_size))

            if cur_chunk_len > chunk_size:
                close_chunk()

                if self.chunk_overlap > 0:
                    last_index = len(last_chunk) - 1
                    overlap_len = 0
                    while overlap_len < self.chunk_overlap and last_index >= 0:
                        text, length = last_chunk[last_index]
                        overlap_len += length
                        cur_chunk_len += length
                        cur_chunk.insert(0, (text, length))
                        last_index -= 1

        if cur_chunk:
            close_chunk()

        chunks = self._postprocess_chunks(chunks)
        return chunks

    def _postprocess_chunks(self, chunks: List[str]) -> List[str]:
        """后处理chunks"""
        new_chunks = []
        for chunk in chunks:
            stripped_chunk = chunk.strip()
            if stripped_chunk == "":
                continue
            new_chunks.append(stripped_chunk)
        return new_chunks

    def _token_size(self, text: str) -> int:
        return len(self._tokenizer(text))

    def _get_splits_by_fns(self, text: str) -> Tuple[List[str], bool]:
        """通过分割函数获取分割"""
        for split_fn in self._split_fns:
            splits = split_fn(text)
            if len(splits) > 1:
                return splits, True

        for split_fn in self._sub_sentence_split_fns:
            splits = split_fn(text)
            if len(splits) > 1:
                return splits, False

        return [text], True


def _add_parent_child_relationship(parent_node: TextNode, child_node: TextNode) -> None:
    """在节点间添加父子关系"""
    if parent_node.id != child_node.id:
        parent_node.relationships[NodeRelationship.CHILD] = RelatedNodeInfo(
            node_id=child_node.id, metadata={}
        )
        child_node.relationships[NodeRelationship.PARENT] = RelatedNodeInfo(
            node_id=parent_node.id, metadata={}
        )


def get_leaf_nodes(nodes_dict: Dict[str, TextNode]) -> List[TextNode]:
    """获取叶子节点"""
    leaf_nodes = set(nodes_dict.values())
    
    for node in nodes_dict.values():
        if NodeRelationship.CHILD in node.relationships:
            child_id = node.relationships[NodeRelationship.CHILD].node_id
            child_node = nodes_dict.get(child_id)
            if child_node in leaf_nodes:
                leaf_nodes.remove(node)
    
    return list(leaf_nodes)


def get_root_nodes(nodes_dict: Dict[str, TextNode]) -> List[TextNode]:
    """获取根节点"""
    root_nodes = set(nodes_dict.values())
    
    for node in nodes_dict.values():
        if NodeRelationship.PARENT in node.relationships:
            parent_id = node.relationships[NodeRelationship.PARENT].node_id
            parent_node = nodes_dict.get(parent_id)
            if parent_node in root_nodes:
                root_nodes.remove(node)
    
    return list(root_nodes)


def get_child_nodes(node: TextNode, nodes_dict: Dict[str, TextNode]) -> List[TextNode]:
    """从给定节点字典获取子节点"""
    child_nodes = []
    
    if NodeRelationship.CHILD in node.relationships:
        child_id = node.relationships[NodeRelationship.CHILD].node_id
        child_node = nodes_dict.get(child_id)
        if child_node:
            child_nodes.append(child_node)
            child_nodes.extend(get_child_nodes(child_node, nodes_dict))
    
    return child_nodes


def get_deeper_nodes(nodes: List[BaseNode], depth: int = 1) -> List[BaseNode]:
    """获取指定深度的子节点"""
    if depth < 0:
        raise ValueError("深度不能为负数!")
    root_nodes = get_root_nodes(nodes)
    if not root_nodes:
        raise ValueError("给定节点中没有根节点!")

    deeper_nodes = root_nodes
    for _ in range(depth):
        deeper_nodes = get_child_nodes(deeper_nodes, nodes)

    return deeper_nodes


# 重新导出SentenceSplitter作为TextSplitter
TextSplitter = SentenceSplitter


class HierarchicalNodeParser(NodeParser):
    """层次化节点解析器

    使用NodeParser将文档分割为递归层次的节点。

    注意：这将返回一个平铺列表中的节点层次结构，其中父节点（例如较大的chunk大小）
    和每个父节点的子节点（例如较小的chunk大小）之间会有重叠。

    例如，这可能返回如下节点列表：
    - chunk大小为2048的顶级节点列表
    - 二级节点列表，其中每个节点都是顶级节点的子节点，chunk大小为512
    - 三级节点列表，其中每个节点都是二级节点的子节点，chunk大小为128
    """

    chunk_sizes: Optional[List[int]] = Field(
        default=None,
        description="按级别顺序分割文档时使用的chunk大小",
    )
    node_parser_ids: List[str] = Field(
        default_factory=list,
        description="按级别顺序分割文档时使用的节点解析器ID列表（第一个ID用于第一级等）",
    )
    node_parser_map: Dict[str, NodeParser] = Field(
        description="节点解析器ID到节点解析器的映射",
    )

    @classmethod
    def from_defaults(
            cls,
            chunk_sizes: Optional[List[int]] = None,
            chunk_overlap: int = 20,
            node_parser_ids: Optional[List[str]] = None,
            node_parser_map: Optional[Dict[str, NodeParser]] = None,
            include_metadata: bool = True,
            include_prev_next_rel: bool = True,
            callback_manager: Optional[CallbackManager] = None,
    ) -> "HierarchicalNodeParser":
        callback_manager = callback_manager or CallbackManager([])

        if node_parser_ids is None:
            if chunk_sizes is None:
                chunk_sizes = [2048, 512, 128]

            node_parser_ids = [f"chunk_size_{chunk_size}" for chunk_size in chunk_sizes]
            node_parser_map = {}
            for chunk_size, node_parser_id in zip(chunk_sizes, node_parser_ids):
                node_parser_map[node_parser_id] = SentenceSplitter(
                    chunk_size=chunk_size,
                    callback_manager=callback_manager,
                    chunk_overlap=chunk_overlap,
                    include_metadata=include_metadata,
                    include_prev_next_rel=include_prev_next_rel,
                )
        else:
            if chunk_sizes is not None:
                raise ValueError("不能同时指定node_parser_ids和chunk_sizes")
            if node_parser_map is None:
                raise ValueError("使用node_parser_ids时必须指定node_parser_map")

        return cls(
            chunk_sizes=chunk_sizes,
            node_parser_ids=node_parser_ids,
            node_parser_map=node_parser_map,
            include_metadata=include_metadata,
            include_prev_next_rel=include_prev_next_rel,
            callback_manager=callback_manager,
        )

    @classmethod
    def class_name(cls) -> str:
        return "HierarchicalNodeParser"

    def _recursively_get_nodes_from_nodes(
            self,
            nodes: List[BaseNode],
            level: int,
            show_progress: bool = False,
    ) -> List[BaseNode]:
        """递归地从节点获取节点"""
        if level >= len(self.node_parser_ids):
            raise ValueError(
                f"级别{level}大于文本分割器数量({len(self.node_parser_ids)})"
            )

        # 首先将当前节点分割为子节点
        nodes_with_progress = get_tqdm_iterable(
            nodes, show_progress, "将文档解析为节点"
        )
        sub_nodes = []
        for node in nodes_with_progress:
            cur_sub_nodes = self.node_parser_map[
                self.node_parser_ids[level]
            ].get_nodes_from_documents([node])
            # 添加从子节点到父节点的父关系
            # 添加从父节点到子节点的子关系
            # 仅在level > 0时添加关系，因为我们不想为正在分割的顶级文档对象添加关系
            if level > 0:
                for sub_node in cur_sub_nodes:
                    _add_parent_child_relationship(
                        parent_node=node,
                        child_node=sub_node,
                    )

            sub_nodes.extend(cur_sub_nodes)

        # 现在对于每个子节点，递归分割为子子节点，并添加
        if level < len(self.node_parser_ids) - 1:
            sub_sub_nodes = self._recursively_get_nodes_from_nodes(
                sub_nodes,
                level + 1,
                show_progress=show_progress,
            )
        else:
            sub_sub_nodes = []

        return sub_nodes + sub_sub_nodes

    def get_nodes_from_documents(
            self,
            documents: Sequence[Document],
            show_progress: bool = False,
            **kwargs: Any,
    ) -> List[BaseNode]:
        """将文档解析为节点

        Args:
            documents (Sequence[Document]): 要解析的文档
            include_metadata (bool): 是否在节点中包含元数据
        """
        with self.callback_manager.event(
                CBEventType.NODE_PARSING, payload={EventPayload.DOCUMENTS: documents}
        ) as event:
            all_nodes: List[BaseNode] = []
            documents_with_progress = get_tqdm_iterable(
                documents, show_progress, "将文档解析为节点"
            )

            # TODO: 目前对tqdm有点hack
            for doc in documents_with_progress:
                nodes_from_doc = self._recursively_get_nodes_from_nodes([doc], 0)
                all_nodes.extend(nodes_from_doc)

            event.on_end(payload={EventPayload.NODES: all_nodes})

        return all_nodes

    # 未使用的抽象方法
    def _parse_nodes(
            self, nodes: Sequence[BaseNode], show_progress: bool = False, **kwargs: Any
    ) -> List[BaseNode]:
        return list(nodes) 