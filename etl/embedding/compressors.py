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
        """Initialize the context compressor.
        
        Args:
            method (str): Compression method, either "bm25_extract" or "llmlingua"
            rate (float): Compression rate (0.0 to 1.0)
            bm25_retriever: BM25 retriever instance for bm25_extract method
        """
        if not 0.0 <= rate <= 1.0:
            raise ValueError("Compression rate must be between 0.0 and 1.0")
            
        self.rate = rate
        self.method = method
        
        if method == "bm25_extract" and bm25_retriever is None:
            raise ValueError("bm25_retriever is required for bm25_extract method")
            
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
                raise RuntimeError(f"Failed to initialize LLMLingua: {str(e)}")
        elif method == "bm25_extract":
            self.bm25_retriever = bm25_retriever
        else:
            raise ValueError(f"Unsupported compression method: {method}")

    def compress(
            self,
            query: str,
            context: str
    ) -> str:
        """Compress the context based on the query.
        
        Args:
            query (str): The query string
            context (str): The context to compress
            
        Returns:
            str: The compressed context
        """
        if not query or not context:
            return context
            
        try:
            if self.method == 'bm25_extract':
                return self._compress_bm25(query, context)
            else:  # llmlingua
                return self._compress_llmlingua(query, context)
        except Exception as e:
            print(f"Error in context compression: {str(e)}")
            return context  # 返回原始上下文而不是失败
            
    def _compress_bm25(self, query: str, context: str) -> str:
        """Compress context using BM25 extraction method."""
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
            print(f"Error in BM25 compression: {str(e)}")
            return context
            
    def _compress_llmlingua(self, query: str, context: str) -> str:
        """Compress context using LLMLingua method."""
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
            print(f"Error in LLMLingua compression: {str(e)}")
            return context
