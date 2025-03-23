"""Hierarchical node parser."""

from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union
import uuid
import sys
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# 明确导入
from etl.embedding import embedding_logger
from etl import DATA_PATH, BASE_PATH

from llama_index.core.bridge.pydantic import Field
from llama_index.core.callbacks.base import CallbackManager
from llama_index.core.callbacks.schema import CBEventType, EventPayload
from llama_index.core.node_parser.interface import NodeParser
from etl.transform.splitter import SentenceSplitter
from llama_index.core.schema import BaseNode, Document, NodeRelationship, TextNode, RelatedNodeInfo
from llama_index.core.utils import get_tqdm_iterable
from llama_index.core.node_parser import TextSplitter


def _add_parent_child_relationship(parent_node: TextNode, child_node: TextNode) -> None:
    """Add parent/child relationship between nodes."""
    if parent_node.id != child_node.id:
        parent_node.relationships[NodeRelationship.CHILD] = RelatedNodeInfo(
            node_id=child_node.id, metadata={}
        )
        child_node.relationships[NodeRelationship.PARENT] = RelatedNodeInfo(
            node_id=parent_node.id, metadata={}
        )


def get_leaf_nodes(nodes_dict: Dict[str, TextNode]) -> List[TextNode]:
    """Get leaf nodes."""
    leaf_nodes = set(nodes_dict.values())
    
    for node in nodes_dict.values():
        if NodeRelationship.CHILD in node.relationships:
            child_id = node.relationships[NodeRelationship.CHILD].node_id
            child_node = nodes_dict.get(child_id)
            if child_node in leaf_nodes:
                leaf_nodes.remove(node)
    
    return list(leaf_nodes)


def get_root_nodes(nodes_dict: Dict[str, TextNode]) -> List[TextNode]:
    """Get root nodes."""
    root_nodes = set(nodes_dict.values())
    
    for node in nodes_dict.values():
        if NodeRelationship.PARENT in node.relationships:
            parent_id = node.relationships[NodeRelationship.PARENT].node_id
            parent_node = nodes_dict.get(parent_id)
            if parent_node in root_nodes:
                root_nodes.remove(node)
    
    return list(root_nodes)


def get_child_nodes(node: TextNode, nodes_dict: Dict[str, TextNode]) -> List[TextNode]:
    """Get child nodes of nodes from given all_nodes."""
    child_nodes = []
    
    if NodeRelationship.CHILD in node.relationships:
        child_id = node.relationships[NodeRelationship.CHILD].node_id
        child_node = nodes_dict.get(child_id)
        if child_node:
            child_nodes.append(child_node)
            child_nodes.extend(get_child_nodes(child_node, nodes_dict))
    
    return child_nodes


def get_deeper_nodes(nodes: List[BaseNode], depth: int = 1) -> List[BaseNode]:
    """Get children of root nodes in given nodes that have given depth."""
    if depth < 0:
        raise ValueError("Depth cannot be a negative number!")
    root_nodes = get_root_nodes(nodes)
    if not root_nodes:
        raise ValueError("There is no root nodes in given nodes!")

    deeper_nodes = root_nodes
    for _ in range(depth):
        deeper_nodes = get_child_nodes(deeper_nodes, nodes)

    return deeper_nodes


class HierarchicalNodeParser(NodeParser):
    """Hierarchical node parser.

    Splits a document into a recursive hierarchy Nodes using a NodeParser.

    NOTE: this will return a hierarchy of nodes in a flat list, where there will be
    overlap between parent nodes (e.g. with a bigger chunk size), and child nodes
    per parent (e.g. with a smaller chunk size).

    For instance, this may return a list of nodes like:
    - list of top-level nodes with chunk size 2048
    - list of second-level nodes, where each node is a child of a top-level node,
      chunk size 512
    - list of third-level nodes, where each node is a child of a second-level node,
      chunk size 128
    """

    chunk_sizes: Optional[List[int]] = Field(
        default=None,
        description=(
            "The chunk sizes to use when splitting documents, in order of level."
        ),
    )
    node_parser_ids: List[str] = Field(
        default_factory=list,
        description=(
                "List of ids for the node parsers to use when splitting documents, "
                + "in order of level (first id used for first level, etc.)."
        ),
    )
    node_parser_map: Dict[str, NodeParser] = Field(
        description="Map of node parser id to node parser.",
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
                raise ValueError("Cannot specify both node_parser_ids and chunk_sizes.")
            if node_parser_map is None:
                raise ValueError(
                    "Must specify node_parser_map if using node_parser_ids."
                )

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
        """Recursively get nodes from nodes."""
        if level >= len(self.node_parser_ids):
            raise ValueError(
                f"Level {level} is greater than number of text "
                f"splitters ({len(self.node_parser_ids)})."
            )

        # first split current nodes into sub-nodes
        nodes_with_progress = get_tqdm_iterable(
            nodes, show_progress, "Parsing documents into nodes"
        )
        sub_nodes = []
        for node in nodes_with_progress:
            cur_sub_nodes = self.node_parser_map[
                self.node_parser_ids[level]
            ].get_nodes_from_documents([node])
            # add parent relationship from sub node to parent node
            # add child relationship from parent node to sub node
            # relationships for the top-level document objects that            # NOTE: Only add relationships if level > 0, since we don't want to add we are splitting
            if level > 0:
                for sub_node in cur_sub_nodes:
                    _add_parent_child_relationship(
                        parent_node=node,
                        child_node=sub_node,
                    )

            sub_nodes.extend(cur_sub_nodes)

        # now for each sub-node, recursively split into sub-sub-nodes, and add
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
        """Parse document into nodes.

        Args:
            documents (Sequence[Document]): documents to parse
            include_metadata (bool): whether to include metadata in nodes

        """
        with self.callback_manager.event(
                CBEventType.NODE_PARSING, payload={EventPayload.DOCUMENTS: documents}
        ) as event:
            all_nodes: List[BaseNode] = []
            documents_with_progress = get_tqdm_iterable(
                documents, show_progress, "Parsing documents into nodes"
            )

            # TODO: a bit of a hack rn for tqdm
            for doc in documents_with_progress:
                nodes_from_doc = self._recursively_get_nodes_from_nodes([doc], 0)
                all_nodes.extend(nodes_from_doc)

            event.on_end(payload={EventPayload.NODES: all_nodes})

        return all_nodes

    # Unused abstract method
    def _parse_nodes(
            self, nodes: Sequence[BaseNode], show_progress: bool = False, **kwargs: Any
    ) -> List[BaseNode]:
        return list(nodes)
