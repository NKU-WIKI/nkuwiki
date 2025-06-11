"""
上下文压缩器模块

提供基于不同策略的上下文压缩功能：
- BM25提取压缩
- LLMLingua压缩
"""

import torch
from llmlingua import PromptCompressor
from etl.utils.text import cut_sent

class ContextCompressor:
    def __init__(
            self,
            method="bm25_extract",
            rate=0.5,
            bm25_retriever=None,
    ):
        """初始化上下文压缩器
        
        Args:
            method (str): 压缩方法，可选"bm25_extract"或"llmlingua"
            rate (float): 压缩率 (0.0 到 1.0)
            bm25_retriever: BM25检索器实例，用于bm25_extract方法
        """
        if not 0.0 <= rate <= 1.0:
            raise ValueError("压缩率必须在0.0到1.0之间")
            
        self.rate = rate
        self.method = method
        
        if method == "bm25_extract" and bm25_retriever is None:
            raise ValueError("bm25_extract方法需要提供bm25_retriever")
            
        if 'llmlingua' in method:
            try:
                self.prompt_compressor = PromptCompressor(
                    "Qwen/Qwen2-7B-Instruct",
                    model_config={
                        "torch_dtype": torch.bfloat16,
                        "low_cpu_mem_usage": True,
                        "trust_remote_code": True
                    }
                )
            except Exception as e:
                raise RuntimeError(f"初始化LLMLingua失败: {str(e)}")
        elif method == "bm25_extract":
            self.bm25_retriever = bm25_retriever
        else:
            raise ValueError(f"不支持的压缩方法: {method}")

    def compress(
            self,
            query: str,
            context: str
    ) -> str:
        """基于查询压缩上下文
        
        Args:
            query (str): 查询字符串
            context (str): 待压缩的上下文
            
        Returns:
            str: 压缩后的上下文
        """
        if not query or not context:
            return context
            
        try:
            if self.method == 'bm25_extract':
                return self._compress_bm25(query, context)
            else:  # llmlingua
                return self._compress_llmlingua(query, context)
        except Exception as e:
            print(f"上下文压缩错误: {str(e)}")
            return context  # 返回原始上下文而不是失败
            
    def _compress_bm25(self, query: str, context: str) -> str:
        """使用BM25提取方法压缩上下文"""
        # 上下文切割为句子
        pre_len = len(context)
        raw_sentences = cut_sent(context)
        
        # 过滤空句子
        sentences = [s.strip() for s in raw_sentences if s.strip()]
        if not sentences:
            return context
            
        try:
            # 获取query与每个句子的BM25分数
            scores = self.bm25_retriever.get_scores(query, sentences)
            
            # 按原句子相对顺序拼接分数高的句子，直到长度超过原长度的rate比例
            sorted_idx = scores.argsort()[::-1]
            current_len = 0
            target_len = pre_len * self.rate
            
            selected_indices = []
            for idx in sorted_idx:
                current_len += len(sentences[idx])
                selected_indices.append(idx)
                if current_len >= target_len:
                    break
                    
            # 保持原始顺序
            selected_indices.sort()
            
            # 拼接选中的句子
            return "".join(sentences[i] for i in selected_indices)
            
        except Exception as e:
            print(f"BM25压缩错误: {str(e)}")
            return context
            
    def _compress_llmlingua(self, query: str, context: str) -> str:
        """使用LLMLingua方法压缩上下文"""
        try:
            compressed_obj = self.prompt_compressor.compress_prompt(
                context,
                instruction="",
                question=query,
                rate=self.rate,
                rank_method=self.method,  # llmlingua or longllmlingua
            )
            return compressed_obj.get('compressed_prompt', context)
        except Exception as e:
            print(f"LLMLingua压缩错误: {str(e)}")
            return context 