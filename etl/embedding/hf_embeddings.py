import logging
from typing import Any, List, Optional, Union

from llama_index.core.base.embeddings.base import (
    DEFAULT_EMBED_BATCH_SIZE,
    BaseEmbedding,
)
from etl.embedding.ingestion import get_node_content
from llama_index.core.bridge.pydantic import Field, PrivateAttr
from llama_index.core.callbacks import CallbackManager
from llama_index.core.schema import BaseNode
from llama_index.core.utils import get_cache_dir, infer_torch_device

from transformers import AutoModel, AutoTokenizer
import torch

DEFAULT_HUGGINGFACE_LENGTH = 512
logger = logging.getLogger(__name__)


class HuggingFaceEmbedding(BaseEmbedding):
    max_length: int = Field(
        default=DEFAULT_HUGGINGFACE_LENGTH, description="Maximum length of input.", gt=0
    )
    normalize: bool = Field(default=True, description="Normalize embeddings or not.")
    query_instruction: Optional[str] = Field(
        description="Instruction to prepend to query text."
    )
    text_instruction: Optional[str] = Field(
        description="Instruction to prepend to text."
    )
    cache_folder: Optional[str] = Field(
        description="Cache folder for Hugging Face files."
    )
    use_auth_token: Union[bool, str, None] = Field(
        description="Use authentication token for Hugging Face models."
    )

    _model: Any = PrivateAttr()
    _device: str = PrivateAttr()
    _embed_type: int = PrivateAttr()
    _tokenizer: Any = PrivateAttr()

    def __init__(
            self,
            model_name: str = 'BAAI/bge-small-zh-v1.5',
            tokenizer_name: Optional[str] = "deprecated",
            pooling: str = "deprecated",
            max_length: int = 512,
            query_instruction: Optional[str] = "为这个句子生成表示以用于检索相关文章：",
            text_instruction: Optional[str] = "为这个句子生成表示以用于检索相关文章：",
            normalize: bool = False,
            model: Optional[Any] = "deprecated",
            tokenizer: Optional[Any] = "deprecated",
            embed_batch_size: int = DEFAULT_EMBED_BATCH_SIZE,
            cache_folder: Optional[str] = None,
            trust_remote_code: bool = False,
            device: Optional[str] = None,
            callback_manager: Optional[CallbackManager] = None,
            embed_type: int = 0,
            use_auth_token: Union[bool, str, None] = None,
            **model_kwargs,
    ):
        # 先调用父类初始化
        super().__init__(
            model_name=model_name,
            max_length=max_length,
            normalize=normalize,
            query_instruction=query_instruction,
            text_instruction=text_instruction,
            use_auth_token=use_auth_token,
            cache_folder=cache_folder,
            embed_batch_size=embed_batch_size,
            callback_manager=callback_manager,
            **model_kwargs
        )
        
        # 然后执行子类初始化逻辑
        self._device = device or infer_torch_device()
        self._embed_type = embed_type
        cache_folder = cache_folder or get_cache_dir()

        for variable, value in [
            ("model", model),
            ("tokenizer", tokenizer),
            ("pooling", pooling),
            ("tokenizer_name", tokenizer_name),
        ]:
            if value != "deprecated":
                raise ValueError(
                    f"{variable} is deprecated. Please remove it from the arguments."
                )
        if model_name is None:
            raise ValueError("The `model_name` argument must be provided.")

        self._tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_folder)
        self._model = AutoModel.from_pretrained(model_name, cache_dir=cache_folder).to(self._device)
        self._model.eval()

    @classmethod
    def class_name(cls) -> str:
        return "HuggingFaceEmbedding"

    def _embed(
            self,
            sentences: List[str],
            prompt_name: Optional[str] = None,
    ) -> List[List[float]]:
        """使用HuggingFace本地模型编码"""
        encoded_input = self._tokenizer(
            sentences,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors='pt'
        ).to(self._device)
        
        with torch.no_grad():
            model_output = self._model(**encoded_input)
            embeddings = model_output[0][:, 0]
        
        if self.normalize:
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
            
        return embeddings.cpu().tolist()

    def _get_query_embedding(self, query: str) -> List[float]:
        """Get query embedding."""
        # 处理单个字符串查询
        if isinstance(query, str):
            query = [query]
        
        # 确保使用正确的提示前缀
        if hasattr(self, 'query_instruction') and self.query_instruction:
            query = [f"{self.query_instruction} {q}" for q in query]
            
        # 获取嵌入向量
        encoded_input = self._tokenizer(
            query,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors='pt'
        ).to(self._device)
        
        with torch.no_grad():
            model_output = self._model(**encoded_input)
            embeddings = model_output[0][:, 0]
        
        if self.normalize:
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
            
        # 确保返回浮点数列表
        result = embeddings.cpu().tolist()[0]
        if not all(isinstance(x, float) for x in result):
            print(f"警告：嵌入向量包含非浮点数值: {result[:5]}...")
            result = [float(x) for x in result]  # 强制转换为浮点数
            
        return result

    async def _aget_query_embedding(self, query: str) -> List[float]:
        """Get query embedding async."""
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        """Get text embedding async."""
        return self._get_text_embedding(text)

    def _get_text_embedding(self, text: str) -> List[float]:
        """Get text embedding."""
        # 添加调试输出
        # print(f"正在处理文本长度: {len(text)}", end=" | ")
        # print(f"前50字符: {text[:50].encode('unicode_escape').decode()}")
        
        inputs = self._tokenizer(text, return_tensors="pt", max_length=512, truncation=True)
        with torch.no_grad():
            outputs = self._model(**inputs)
        # print(outputs.last_hidden_state[:, 0].cpu().numpy().tolist()[0])
        return outputs.last_hidden_state[:, 0].cpu().numpy().tolist()[0]

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get text embeddings."""
        # 添加调试输出
        # print(f"批量处理文本数量: {len(texts)}")
        # for i, text in enumerate(texts[:3]):  # 打印前3个样本
            # print(f"样本{i}长度: {len(text)} | 前50字符: {text[:50].encode('unicode_escape').decode()}")
        
        # 调用原始实现
        embeddings = self._embed(texts, prompt_name="text")
        # print(f"生成嵌入向量形状: {len(embeddings)}x{len(embeddings[0])}")
        return embeddings

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
