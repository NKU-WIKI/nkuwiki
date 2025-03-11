from typing import Any, List, Optional

import torch
from llama_index.core.bridge.pydantic import Field, PrivateAttr, ConfigDict
from llama_index.core.callbacks import CBEventType, EventPayload
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import MetadataMode, NodeWithScore, QueryBundle
from llama_index.core.utils import infer_torch_device
from transformers import AutoTokenizer, AutoModelForCausalLM
from etl.embedding.ingestion import get_node_content
import numpy as np
import time
from pydantic import model_validator

DEFAULT_SENTENCE_TRANSFORMER_MAX_LENGTH = 512


class SentenceTransformerRerank(BaseNodePostprocessor):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="ignore",
        protected_namespaces=()
    )
    
    model: str = Field(description="Sentence transformer model name.")
    top_n: int = Field(description="Number of nodes to return sorted by score.")
    device: str = Field(
        default="cpu",
        description="Device to use for sentence transformer.",
    )
    keep_retrieval_score: bool = Field(
        default=False,
        description="Whether to keep the retrieval score in metadata.",
    )
    batch_size: int = Field(
        default=32,
        description="Batch size for predictions"
    )
    _model: Any = PrivateAttr()

    def __init__(
            self,
            top_n: int = 2,
            model: str = "cross-encoder/stsb-distilroberta-base",
            device: Optional[str] = None,
            keep_retrieval_score: Optional[bool] = False,
            batch_size: int = 32,
    ):
        try:
            from sentence_transformers import CrossEncoder
        except ImportError:
            raise ImportError(
                "Cannot import sentence-transformers or torch package,",
                "please `pip install torch sentence-transformers`",
            )
        
        device = infer_torch_device() if device is None else device
        
        super().__init__(
            model=model,
            top_n=top_n,
            device=device,
            keep_retrieval_score=keep_retrieval_score,
            batch_size=batch_size
        )
        
        try:
            self._model = CrossEncoder(
                model, 
                max_length=512,
                device=device
            )
        except Exception as e:
            raise Exception(f"Failed to initialize CrossEncoder model: {str(e)}")

    @classmethod
    def class_name(cls) -> str:
        return "SentenceTransformerRerank"

    def _batch_predict(self, query_and_nodes: List[tuple], pbar) -> List[float]:
        """批量预测，处理可能的错误"""
        try:
            # 分批处理
            all_scores = []
            total_processed = 0
            start_time = time.time()
            
            for i in range(0, len(query_and_nodes), self.batch_size):
                batch = query_and_nodes[i:i + self.batch_size]
                try:
                    scores = self._model.predict(batch)
                    # 处理不同类型的scores
                    if isinstance(scores, (list, tuple)):
                        scores = [float(s) if isinstance(s, (int, float)) else s.item() for s in scores]
                    elif isinstance(scores, torch.Tensor):
                        scores = scores.detach().cpu().numpy().tolist()
                        if not isinstance(scores, list):
                            scores = [scores]
                    elif isinstance(scores, np.ndarray):
                        scores = scores.tolist()
                        if not isinstance(scores, list):
                            scores = [scores]
                    else:
                        scores = [float(scores)]
                    all_scores.extend(scores)
                    
                    # 更新进度条
                    batch_size = len(batch)
                    total_processed += batch_size
                    elapsed = time.time() - start_time
                    speed = total_processed / elapsed if elapsed > 0 else 0
                    eta = (len(query_and_nodes) - total_processed) / speed if speed > 0 else 0
                    
                    pbar.set_postfix({
                        'Batch': f'{i//self.batch_size + 1}/{(len(query_and_nodes) + self.batch_size - 1)//self.batch_size}',
                        'Speed': f'{speed:.1f} nodes/s',
                        'ETA': f'{eta:.1f}s',
                        'Success': f'{total_processed}/{len(query_and_nodes)}'
                    })
                    pbar.update(batch_size)
                    
                except Exception as e:
                    print(f"Error in batch prediction: {str(e)}")
                    print(f"Batch size: {len(batch)}, Scores type: {type(scores)}")
                    # 如果批处理失败，给这批数据一个默认分数
                    all_scores.extend([0.0] * len(batch))
            return all_scores
        except Exception as e:
            print(f"Error in _batch_predict: {str(e)}")
            return [0.0] * len(query_and_nodes)

    def _postprocess_nodes(
            self,
            nodes: List[NodeWithScore],
            query_bundle: Optional[QueryBundle] = None,
    ) -> List[NodeWithScore]:
        if query_bundle is None:
            raise ValueError("Missing query bundle in extra info.")
        if len(nodes) == 0:
            print("警告: 重排器收到空节点列表")
            return []

        try:
            # 准备输入数据
            query_and_nodes = []
            valid_nodes = []
            
            for node in nodes:
                try:
                    content = node.node.get_content(metadata_mode=MetadataMode.NONE)
                    if content and isinstance(content, str):
                        query_and_nodes.append((query_bundle.query_str, content))
                        valid_nodes.append(node)
                except Exception as e:
                    print(f"Error getting content from node: {str(e)}")
                    continue

            if not valid_nodes:
                print("No valid nodes to process")
                return nodes[:self.top_n]

            # 设置进度条
            from tqdm.auto import tqdm
            
            print(f"\nReranking {len(valid_nodes)} nodes in batches of {self.batch_size}...")
            
            pbar = tqdm(
                total=len(valid_nodes),
                desc="Reranking Progress",
                unit="nodes",
                miniters=1,
                smoothing=0.1,
                dynamic_ncols=True,
                position=0,
                leave=True
            )

            start_time = time.time()

            with self.callback_manager.event(
                    CBEventType.RERANKING,
                    payload={
                        EventPayload.NODES: valid_nodes,
                        EventPayload.MODEL_NAME: self.model,
                        EventPayload.QUERY_STR: query_bundle.query_str,
                        EventPayload.TOP_K: self.top_n,
                    },
            ) as event:
                # 批量预测
                scores = self._batch_predict(query_and_nodes, pbar)

                if len(scores) != len(valid_nodes):
                    print(f"Warning: Scores length ({len(scores)}) does not match nodes length ({len(valid_nodes)})")
                    pbar.close()
                    return nodes[:self.top_n]

                # 更新分数
                for node, score in zip(valid_nodes, scores):
                    try:
                        if self.keep_retrieval_score:
                            node.node.metadata["retrieval_score"] = node.score
                        node.score = float(score) if score is not None else 0.0
                    except Exception as e:
                        print(f"Error updating node score: {str(e)}")
                        node.score = 0.0

                # 排序并选择top_n
                new_nodes = sorted(
                    valid_nodes,
                    key=lambda x: float('-inf') if x.score is None else -float(x.score)
                )[:min(self.top_n, len(valid_nodes))]
                
                # 显示完成统计
                total_time = time.time() - start_time
                print(f"\nReranking completed in {total_time:.2f}s ({len(valid_nodes)/total_time:.2f} nodes/s)")
                
                event.on_end(payload={EventPayload.NODES: new_nodes})
                pbar.close()
                return new_nodes

        except Exception as e:
            print(f"Error in _postprocess_nodes: {str(e)}")
            if 'pbar' in locals():
                pbar.close()
            return nodes[:min(self.top_n, len(nodes))]


class LLMRerank(BaseNodePostprocessor):
    model_config = ConfigDict(extra="ignore")  # 添加Pydantic配置
    
    model: str = Field(description="Transformer model name.")
    top_n: int = Field(description="Number of nodes to return sorted by score.")
    device: str = Field(
        default="cpu",
        description="Device to use for sentence transformer.",
    )
    keep_retrieval_score: bool = Field(
        default=True,
        description="Whether to keep the retrieval score in metadata.",
    )
    embed_bs: int = Field(
        default=16,  # 减小默认批次大小
    )
    _model: Any = PrivateAttr()
    _tokenizer: Any = PrivateAttr()
    _yes_loc: Any = PrivateAttr()
    _layer: int = PrivateAttr()
    _embed_bs: int = PrivateAttr()
    _embed_type: int = PrivateAttr()
    _type: int = PrivateAttr()
    _compress_ratio: int = PrivateAttr()
    _compress_layer: list[int] = PrivateAttr()
    _use_efficient: int = PrivateAttr()
    num_threads: int = Field(
        default=4, 
        description="CPU并行线程数",
        json_schema_extra={"example": 4}
    )

    def __init__(
            self,
            top_n: int = 2,
            model: str = "BAAI/bge-reranker-base",  # 使用base版本
            device: Optional[str] = None,
            keep_retrieval_score: Optional[bool] = True,
            embed_bs: int = 8,  # CPU环境下使用更小的批次
            embed_type: int = 0,
            use_efficient: int = 0,
    ):
        device = infer_torch_device() if device is None else device

        # 优化tokenizer配置
        self._tokenizer = AutoTokenizer.from_pretrained(
            model, 
            trust_remote_code=True,
            use_fast=True
        )
        self._tokenizer.padding_side = 'right'
        self._tokenizer.pad_token = self._tokenizer.eos_token if self._tokenizer.pad_token is None else self._tokenizer.pad_token
        
        self._yes_loc = self._tokenizer('Yes', add_special_tokens=False)['input_ids'][0]
        self._embed_type = embed_type

        # CPU优化的模型配置
        model_config = {
            'torch_dtype': torch.float32,  # CPU环境使用float32
            'trust_remote_code': True,
            'low_cpu_mem_usage': True,
        }
        
        # 加载模型
        self._model = AutoModelForCausalLM.from_pretrained(
            model,
            **model_config
        )
        
        # CPU性能优化
        self._model.eval()
        if not torch.cuda.is_available():
            # 启用Intel MKL优化（如果可用）
            
            # 启用torch的CPU优化
            torch.set_num_threads(self.num_threads)
            torch.set_num_interop_threads(1)  # 减少线程间开销
        
        self._type = 0  # 使用基础模型类型
        self._embed_bs = embed_bs
        
        super().__init__(
            top_n=top_n,
            model=model,
            device=device,
            keep_retrieval_score=keep_retrieval_score,
        )

    def last_logit_pool(self, logits: torch.Tensor,
                        attention_mask: torch.Tensor) -> torch.Tensor:
        if attention_mask.dim() == 1:
            attention_mask = attention_mask.unsqueeze(0)
        if logits.dim() == 2:
            logits = logits.unsqueeze(0)
            
        batch_size = logits.shape[0]
        sequence_lengths = attention_mask.sum(dim=1) - 1
        
        left_padding = (attention_mask[:, -1].sum() == attention_mask.shape[0])
        if left_padding:
            return logits[:, -1]
            
        gathered_logits = []
        for i in range(batch_size):
            seq_len = sequence_lengths[i]
            if seq_len < 0:
                seq_len = logits.shape[1] - 1
            gathered_logits.append(logits[i, seq_len])
            
        return torch.stack(gathered_logits, dim=0)

    def get_inputs(self, pairs, tokenizer, prompt=None, max_length=None):
        """Get model inputs."""
        if prompt is None:
            texts = [f"Query: {query}\nDocument: {document}\nVerdict:" for query, document in pairs]
        else:
            texts = [prompt.format(query=query, document=document) for query, document in pairs]
        
        # 直接使用512作为最大长度，强制截断
        inputs = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,  # 强制使用512作为最大长度
            return_tensors="pt",
            return_attention_mask=True,
            add_special_tokens=True
        )
        
        if inputs['attention_mask'].dim() == 1:
            inputs['attention_mask'] = inputs['attention_mask'].unsqueeze(0)
            
        return inputs

    def get_inputs_v2_5(self, pairs, tokenizer, prompt=None, max_length=None):
        """Get model inputs for version 2.5."""
        if prompt is None:
            texts = [f"Query: {query}\nDocument: {document}\nVerdict:" for query, document in pairs]
        else:
            texts = [prompt.format(query=query, document=document) for query, document in pairs]

        query_lengths = []
        prompt_lengths = []
        
        for query, document in pairs:
            query_tok = tokenizer(
                f"Query: {query}\nVerdict:", 
                truncation=True, 
                max_length=512,  # 强制使用512作为最大长度
                add_special_tokens=False,
                return_attention_mask=True
            )
            query_lengths.append(len(query_tok['input_ids']))
            
            prompt_tok = tokenizer(
                f"Document: {document}\nVerdict:", 
                truncation=True, 
                max_length=512,  # 强制使用512作为最大长度
                add_special_tokens=False,
                return_attention_mask=True
            )
            prompt_lengths.append(len(prompt_tok['input_ids']))

        inputs = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,  # 强制使用512作为最大长度
            return_tensors="pt",
            return_attention_mask=True,
            add_special_tokens=True
        )
        
        if inputs['attention_mask'].dim() == 1:
            inputs['attention_mask'] = inputs['attention_mask'].unsqueeze(0)
            
        return inputs, query_lengths, prompt_lengths

    @classmethod
    def class_name(cls) -> str:
        return "LLMRerank"

    def process_batch(self, batch_data, query_str):
        """处理单个批次的数据"""
        query_and_nodes = [
            (
                query_str,
                get_node_content(node.node, self._embed_type),
            )
            for node in batch_data
        ]

        try:
            if self._type == 2:
                inputs, query_lengths, prompt_lengths = self.get_inputs_v2_5(query_and_nodes, self._tokenizer)
            else:
                inputs = self.get_inputs(query_and_nodes, self._tokenizer)
            
            inputs = {k: v.to(self._model.device) for k, v in inputs.items()}

            with torch.no_grad():
                if self._type == 1:
                    all_scores = self._model(**inputs, return_dict=True, cutoff_layers=[self._layer])
                    scores_list = [scores.view(scores.size(0), -1)[:, -1].float() 
                                 for scores in all_scores[0]]
                    scores = scores_list[0]

                elif self._type == 2:
                    outputs = self._model(**inputs,
                                       return_dict=True,
                                       cutoff_layers=[self._layer],
                                       compress_ratio=self._compress_ratio,
                                       compress_layer=self._compress_layer,
                                       query_lengths=query_lengths,
                                       prompt_lengths=prompt_lengths)
                    
                    scores = []
                    for j in range(len(outputs.logits)):
                        logits = outputs.logits[j]
                        attention_mask = outputs.attention_masks[j]
                        
                        if logits.dim() == 2:
                            logits = logits.unsqueeze(0)
                        if attention_mask.dim() == 1:
                            attention_mask = attention_mask.unsqueeze(0)
                        
                        pooled_logits = self.last_logit_pool(logits, attention_mask)
                        scores.append(pooled_logits.cpu().float().tolist())
                    
                    scores = torch.tensor(scores[0], device=self._model.device)
                    
                else:
                    outputs = self._model(**inputs, return_dict=True)
                    logits = outputs.logits
                    if logits.dim() == 2:
                        logits = logits.unsqueeze(0)
                    scores = logits[:, -1, self._yes_loc].view(-1).float()

            # 更新分数
            for node, score in zip(batch_data, scores):
                if self.keep_retrieval_score:
                    node.node.metadata["retrieval_score"] = node.score
                node.score = float(score.item() if torch.is_tensor(score) else score)

            return batch_data, None
        except Exception as e:
            return None, str(e)

    @model_validator(mode="before")
    @classmethod
    def validate_model(cls, values: dict) -> dict:
        # 添加模型验证逻辑...
        return values

    def _postprocess_nodes(
            self,
            nodes: List[NodeWithScore],
            query_bundle: Optional[QueryBundle] = None,
    ) -> List[NodeWithScore]:
        if query_bundle is None:
            raise ValueError("Missing query bundle in extra info.")
        if len(nodes) == 0:
            print("警告: 重排器收到空节点列表")
            return []
        
        bsz = self._embed_bs
        N = len(nodes)

        from tqdm.auto import tqdm
        import time
        from concurrent.futures import ThreadPoolExecutor
        import math

        print(f"\nReranking {N} nodes in batches of {bsz}...")
        
        # 使用auto tqdm并优化显示
        pbar = tqdm(
            total=N,
            desc="Reranking Progress",
            unit="nodes",
            miniters=1,
            smoothing=0.1,
            dynamic_ncols=True,
            position=0,
            leave=True
        )

        start_time = time.time()
        processed_nodes = []
        errors = []

        # 计算总批次数
        total_batches = math.ceil(N / bsz)

        # 使用线程池进行并行处理
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = []
            
            # 提交所有批次的处理任务
            for i in range(0, N, bsz):
                if self._type == 1 and i == 0 and self._use_efficient != 0:
                    self._model.judge = True
                    self._model.cut_layer = self._layer

                batch = nodes[i:min(i + bsz, N)]
                future = executor.submit(
                    self.process_batch,
                    batch,
                    query_bundle.query_str
                )
                futures.append(future)

            # 处理完成的批次结果
            for i, future in enumerate(futures):
                try:
                    batch_result, error = future.result()
                    if batch_result is not None:
                        processed_nodes.extend(batch_result)
                    if error is not None:
                        errors.append(f"Batch {i+1}: {error}")
                    
                    # 更新进度条
                    batch_size = len(batch_result) if batch_result is not None else 0
                    pbar.update(batch_size)
                    
                    # 更新进度条信息
                    elapsed = time.time() - start_time
                    speed = len(processed_nodes) / elapsed
                    eta = (N - len(processed_nodes)) / speed if speed > 0 else 0
                    
                    pbar.set_postfix({
                        'Batch': f'{i+1}/{total_batches}',
                        'Speed': f'{speed:.1f} nodes/s',
                        'ETA': f'{eta:.1f}s',
                        'Success': f'{len(processed_nodes)}/{N}'
                    })
                    
                except Exception as e:
                    errors.append(f"Batch {i+1} failed: {str(e)}")

        # 关闭进度条并显示统计信息
        pbar.close()
        total_time = time.time() - start_time
        
        # 显示处理统计
        print(f"\nReranking completed in {total_time:.2f}s ({N/total_time:.2f} nodes/s)")
        if errors:
            print("\nErrors occurred during processing:")
            for error in errors:
                print(f"- {error}")

        # 排序并返回结果
        if processed_nodes:
            new_nodes = sorted(
                processed_nodes,
                key=lambda x: float('-inf') if x.score is None else -float(x.score)
            )[:self.top_n]
            return new_nodes
        else:
            print("Warning: No nodes were successfully processed")
            return []
