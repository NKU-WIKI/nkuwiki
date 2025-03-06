import asyncio
import logging
from typing import Any, List

from llama_index.core.base.embeddings.base import (
    DEFAULT_EMBED_BATCH_SIZE,
    BaseEmbedding,
)
from etl.embedding.ingestion import get_node_content
from llama_index.core.bridge.pydantic import Field, ConfigDict
from llama_index.core.schema import BaseNode
from sentence_transformers import SentenceTransformer

DEFAULT_HUGGINGFACE_LENGTH = 512
DEFAULT_HUGGINGFACE_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
logger = logging.getLogger(__name__)


class HuggingFaceEmbedding(BaseEmbedding):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        protected_namespaces=()  # 解决Pydantic V2私有属性问题
    )
    
    model_name: str = Field(
        default="BAAI/bge-small-en-v1.5",
        description="Sentence transformers模型名称"
    )
    normalize: bool = Field(
        default=True,
        description="是否对嵌入结果进行归一化"
    )
    embed_type: int = Field(
        default=1,
        description="嵌入类型"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._embed_type = kwargs.get('embed_type', 1)
        self._model = SentenceTransformer(
            self.model_name,
            device=kwargs.get('device', 'cpu'),
            trust_remote_code=True
        )

    @classmethod
    def class_name(cls) -> str:
        return "HuggingFaceEmbedding"

    def _embed(self, texts: List[str]) -> List[List[float]]:
        return self._model.encode(texts, normalize_embeddings=self.normalize).tolist()

    def _get_query_embedding(self, query: str) -> List[float]:
        return self._embed([query])[0]

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return await asyncio.to_thread(self._get_query_embedding, query)

    def _get_text_embedding(self, text: str) -> List[float]:
        return self._embed([text])[0]

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return await asyncio.to_thread(self._get_text_embedding, text)

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return self._embed(texts)

    async def _aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return await asyncio.to_thread(self._embed, texts)

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
