import asyncio
from typing import List, Any
from sentence_transformers import SentenceTransformer
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.bridge.pydantic import Field, ConfigDict
from llama_index.core.schema import BaseNode
from etl.processors.nodes import get_node_content

class HuggingFaceEmbedding(BaseEmbedding):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        protected_namespaces=()  # 解决Pydantic V2私有属性问题
    )
    
    model_name: str = Field(
        default="BAAI/bge-small-zh-v1.5",  # 改为一个兼容的模型
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
        # 处理模型名称，移除可能的"sentence-transformers/"前缀
        model_name = kwargs.get('model_name', self.model_name)
        if model_name.startswith("sentence-transformers/"):
            model_name = model_name.replace("sentence-transformers/", "")
        self._model = SentenceTransformer(
            model_name,
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

    def get_text_embedding_batch(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """批量获取文本嵌入"""
        return self._embed(texts)
    
    async def aget_text_embedding_batch(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """异步批量获取文本嵌入"""
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

# 定义HFEmbeddings作为HuggingFaceEmbedding的别名
HFEmbeddings = HuggingFaceEmbedding
