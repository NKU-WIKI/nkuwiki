import logging
from typing import Any, List

import torch
import torch.nn.functional as F
from llama_index.core.base.embeddings.base import (
    BaseEmbedding,
)
from llama_index.core.bridge.pydantic import PrivateAttr
from llama_index.core.schema import BaseNode, MetadataMode
from llama_index.core.utils import infer_torch_device
from torch import Tensor
from transformers import AutoModel, AutoTokenizer

from etl.embedding.ingestion import get_node_content

logger = logging.getLogger(__name__)


class GTEEmbedding(BaseEmbedding):
    _model: Any = PrivateAttr()
    _tokenizer: Any = PrivateAttr()
    _device: str = PrivateAttr()
    _embed_type: int = PrivateAttr()

    def __init__(
            self,
            model_name: str = None,
            embed_type: int = 0,
            **kwargs: Any,
    ) -> None:
        self._device = infer_torch_device()
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._model = AutoModel.from_pretrained(model_name).to(self._device)
        self._embed_type = embed_type
        super().__init__(**kwargs)

    def last_token_pool(self, last_hidden_states: Tensor,
                        attention_mask: Tensor) -> Tensor:
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_states.size()).float()
        return torch.sum(last_hidden_states * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    def get_detailed_instruct(self, query: str) -> str:
        return f"为这个句子生成表示以用于检索相关文章：{query}"

    @classmethod
    def class_name(cls) -> str:
        return "GTEEmbedding"

    def _embed(self, texts: List[str]) -> List[List[float]]:
        """Embed sentences."""
        max_length = 8192
        # Tokenize the input texts
        batch_dict = self._tokenizer(texts, max_length=max_length, padding=True, truncation=True,
                                     return_tensors='pt').to(self._device)
        with torch.no_grad():
            outputs = self._model(**batch_dict)
            embeddings = self.last_token_pool(outputs.last_hidden_state, batch_dict['attention_mask'])

            # normalize embeddings
            embeddings = F.normalize(embeddings, p=2, dim=1)
            embeddings = embeddings.to(torch.float).tolist()
        return embeddings

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._get_text_embedding(text)

    def _get_query_embedding(self, query: str) -> List[float]:
        """获取查询嵌入"""
        embeddings = self._embed([query], prompt_name="query")
        # 确保返回的是浮点数列表
        if isinstance(embeddings, list) and len(embeddings) > 0:
            # 检查返回值类型并转换为浮点数
            if isinstance(embeddings[0], list):
                return [float(x) for x in embeddings[0]]
            else:
                return embeddings[0]
        return []

    def _get_text_embedding(self, text: str) -> List[float]:
        embeddings = self._embed([text])
        return embeddings[0]

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Embed sentences."""
        return self._embed(texts)

    def __call__(self, nodes: List[BaseNode], **kwargs: Any) -> List[BaseNode]:
        embeddings = self.get_text_embedding_batch(
            [get_node_content(node, self._embed_type) for node in nodes],
            **kwargs,
        )

        for node, embedding in zip(nodes, embeddings):
            node.embedding = embedding

        return nodes

    async def acall(self, nodes: List[BaseNode], **kwargs: Any) -> List[BaseNode]:
        embeddings = await self.aget_text_embedding_batch(
            [get_node_content(node, self._embed_type) for node in nodes],
            **kwargs,
        )

        for node, embedding in zip(nodes, embeddings):
            node.embedding = embedding

        return nodes
