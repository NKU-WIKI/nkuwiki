# rag方案

## 摘要

本文提出了EasyRAG,一个面向AIOps网络运维的简洁､轻量､高效的检索增强问答框架｡我们主要的贡献为:(1) 问答准确,我们设计了一套简洁的基于两路稀疏检索粗排—LLM Reranker重排—LLM答案生成与优化的RAG方案以及配套的数据处理流程, 部署简单,我们的方法主要由bm25检索和bge-reranker重排组成,无需微调任何模型,占用显存少,部署容易,可扩展性强;我们提供了一套灵活的代码库,内置了多种搜索和生成策略,方便自定义流程实现｡(2) 推理高效,我们设计了一套粗排-重排-生成全流程的高效推理加速方案,能够大幅降低RAG的推理延迟且较好地维持了准确度水平;每个加速方案都可以即插即用到任意的RAG流程的相关组件中,一致地提升RAG系统的效率｡  

## 1 EasyRAG框架介绍  

我们的复赛方案可以用图1概括｡包含数据处理流程(1.1) 和RAG流程(1.2)｡  

### 1.1 数据处理流程  

### 1.1.1 文本分块  

分块设置 我们使用了SentenceSplitter对文档进行分块,即先利用中文分隔符分割为句子,再按照设置的文本块大小合并,使用的块大小(chunk-size)为1024,块重叠大小(chunkoverlap)为200｡  
消除分块中的路径影响 在实践中,我们发现llama-idnex的原实现中含有对路径信息的简单但不稳定的使用方式,即将文本长度减去文件路径长度得到实际使用的文本长度,这样会让不同的数据路径产生不同的分块结果,在初赛中我们发现同样的chunk-size和chunkoverlap,更换路径最多可以为最终评测结果带来3个点的波动,这显然在实践中无法接受｡针对此问题,我们实现了自定义的分块类,将路径长度的利用给消除,从而保证可稳定复现｡  

### 1.2 RAG流程

### 1.2.1 查询改写

用户所给的查询都非常简短，并且我们发现部分查询语句存在语义不通顺或者关键词不清晰的问题，例如：“查询课表？”。我们在将问题query输入到RAG Pipeline前，通过LLM（doubao）进行查询改写（扩展）

- **查询扩展**：我们对用户日志的查询问题进行了总结，其中查询语句存在以下特点：  
  • 查询中的关键词非常重要；  
  • 查询语句长度短、信息量方差大。  
  在这种情况下，我们尝试了根据初始查询语句和设计的提示词，利用LLM模型总结问题中的关键词或者是可能涉及到的一些关键词，即利用LLM模型的知识，进行运维、通信领域的关键词联想和查询关键词的总结，我们称之为关键词扩展。  
  人工标注若干条数据中的关键词和可能联想的关键词后，随即利用LLM即进行few - shots的关键词总结、扩展。我们参考（Wang et al., 2023），将扩展得到的关键词基于原始查询通过直接拼接、再次利用大语言模型总结两种方式生成新的查询。  
  其中，c表示的大语言模型LLM，q、p分别代表的是初始查询和提示词，\(p_{\exp}\)表示扩展查询的提示词，其中包括人工标注的几条数据，\(p_{sum}\)表示的是利用大模型进行语句和扩展关键词的总结拼接的提示词。   

#### 1.2.2 两路稀疏检索粗排

在稀疏检索部分，我们采用BM25算法构建检索器，BM25的核心思想是基于词频（TF）和逆文档频率（IDF）来，同时还引入了文档的长度信息来计算文档和查询q之间的相关性。具体实现上，BM25检索器主要由中文分词器、停用词表构成，我们逐一进行介绍。  

- **中文分词器**：对于中文分词器，我们采用的是常见的jieba中文分词器，jieba分词器的优点在于轻量级，可以开启多线程模式加速分词和词性分析，并且可以根据自己的需要自定义词频或是自定义词典调整分词偏好。对于分词器我们也尝试做了词表的自定义，当前场景是南开大学校园问答，由于缺乏数据词表，因此最终我们仍然使用了原始的jieba词表。  
- **停用词表**：对于中文的停用词表，我们采用了哈尔滨工业大学搜集的中文常见停用词表作为中文分词过程中过滤无意义词汇的参考词表，通过过滤无意义的词汇和特殊符号以提高有效关键词的命中率，提高正确文档的召回率。  
- **两路检索**：BM25两路检索粗排为文本块检索和路径检索。  
  1. **文本块检索**：使用BM25对分割好的文本块进行搜索，粗排召回得分大于0的前192个文本块。  
- **检索流程**：BM25检索器对于一个给定的查询q，具体的文档检索流程如下：  
  1. 文档预处理：先对所有文档（文本块或路径）进行停用词过滤，再利用中文分词器进行中文分词，并预先计算文档的的IDF分数。  
  2. 查询处理：对查询q进行停用词过滤和中文分词。  
  3. 相似度召回：统计查询q的关键词和计算各个文档的TF值，根据TF、IDF值计算查询q和各个文档中的相关分数，根据分数召回相关文档。  

#### 1.2.3 密集检索粗排  

密集检索部分我们采用了BAAI/bge-large-zh-v1.5（引用待补充），此模型在（待补充）上达到了先进效果。  

- **检索流程**：密集检索器对于一个给定的查询q，具体的文档检索流程如下：  
  1. 文档编码：将所有文本块输入模型进行编码得到表征，存入qdrant向量数据库。  
  2. 查询编码：利用查询提示模板将q转换为bge的查询输入，利用模型进行编码。  
  3. 相似度召回：在检索时，使用余弦相似度进行匹配，召回前288个文本块。  

#### 1.2.4 LLM Reranker重排

我们采用了BAAI/bge-reranker-base（待补充），一个基于（待补充）在混合的多个多语言排序数据集上训练的LLM Reranker，此模型在中英文上具有先进的排序效果，且含有配套的工具代码，可以很方便地根据具体场景进行进一步微调。  

- **重排流程**：LLM - Reranker对于一个给定的查询q和\(k'\)个粗排得到的文本块，具体的文档排序流程如下：  
  1. 文档扩展：将知识路径和每个文本块拼接起来作为扩展文档用于检索。  
  2. 文本处理：将q和\(k'\)文本块分别组合成\(k'\)个查询 - 文档对，输入分词器得到LLM的输入数据。  
  3. 相似度排序：将输入数据输入LLM得到查询和每个文本块的重排分数，并根据此分数进行排序，取最高的k（一般为6）个文本块返回。  

#### 1.2.5 多路排序融合  

- **融合算法**：由于我们设计了多路检索粗排，那么也需要设计相应的排序融合策略，我们主要使用了简单合并与倒数排序融合（Reciprocal Rank Fusion RRF）两种策略。简单合并策略直接将多路得到的文本块进行去重与合并。倒数排序融合则将同一个文档在多个路径的搜索排序的倒数进行求和作为融合的分数进行再次排序。  
- **粗排融合**：最直接的排序融合的使用方式是，得到多路粗排结果后直接使用融合算法将多路粗排得到的文本块合并为一个文本块集合，再交给Reranker重排。复赛中我们使用了简单合并将两路稀疏检索粗排结果合并。  
- **重排融合**：我们还可以在每一路完成粗排 - 重排后，再进行融合。初赛中我们融合了文本块稀疏检索和文本块密集检索两路，针对这两路检索，我们设计了三种重排融合方法。  
  1. 使用RRF将多路的粗排 - 精排后的结果合并。  
  2. 将多路重排后的文本块输入LLM分别得到相应的答案，取答案更长的作为最终答案。  
  3. 将多路重排后的文本块输入LLM分别得到相应的答案，将多路的答案直接拼接。  

#### 1.2.6 LLM回答

此部分我们先将重排得到的top6文本块的内容用以下模板拼接得到上下文字符串：  

```markdown  
### 文档0: {chunk_i} ### 文档5: {chunk_i}  
```  

之后我们将上下文字符串和问题用如下的问答模板组合成提示词，输入LLM（deepseek-V3）获得答案。  

```markdown  
上下文信息如下:  
{context_str}  
请你基于上下文信息而不是自己的知识,回答以下问题,可以分点作答,如果上下文信息没有相关知识,可以回答不确定,不要复述上下文信息:  
{query_str}  
回答:  
```  

除此之外，我们还设计了其他格式的问答模板，参考思维链（Wei et al., 2022）设计了思维链问答模板（附录A.2），参考COSTAR（Teo, 2023）设计了markdown格式问答模板（附录A.1），为了让LLM更重视top1文档设计了侧重问答模板（附录A.3） 

#### 1.2.7 LLM答案优化

由于我们发现LLM对于每个文本块都会给予一定的注意力，可能会导致top1文本块的有效信息没有得到充分利用，对于这种情况，我们设计了答案整合提示词（附录B），将根据6个文本块得到的答案利用top1文本块进行补充整合，得到最终的答案。

### 2 可扩展性

文档可扩展性 我们的方案主要基于bm25检索与Reranker重排,只需要对最新的文档进行处理,之后重新进行分块和idf值计算,整个过程时间开销较小,可以在5分钟内完成全部的处理流程｡  
用户可扩展性 我们的方案显存占用较小,且在各个环节都设计了相应的推理加速方法,可以根据用户的具体规模决定使用相应的优化策略｡即使是使用完全无加速的方案,一张80G的显卡也可以支撑至少6个RAG进程,在半分钟内返回答案给用户｡  

### 3 结论

本文提出了EasyRAG,一个面向AIOps网络运维的准确､轻量､高效､灵活且可扩展的检索增强问答框架｡  

### 参考文献  
[1] Jianlv Chen, Shitao Xiao, Peitian Zhang, Kun Luo, Defu Lian, and Zheng Liu. 2024. Bge m3-embedding: Multi-lingual, multifunctionality, multi-granularity text embeddings through self-knowledge distillation.  
[2] Luyu Gao, Xueguang Ma, Jimmy Lin, and Jamie Callan. 2022. Precise zero-shot dense retrieval without relevance labels. arXiv preprint arXiv:2212.10496.  
[3] Team GLM, Aohan Zeng, Bin Xu, Bowen Wang, Chenhui Zhang, Da Yin, Diego Rojas, Guanyu Feng, Hanlin Zhao, Hanyu Lai, Hao Yu, Hongning Wang, Jiadai Sun, Jiajie Zhang, Jiale Cheng, Jiayi Gui, Jie Tang, Jing Zhang, Juanzi Li, Lei Zhao, Lindong Wu, Lucen Zhong, Mingdao Liu, Minlie Huang, Peng Zhang, Qinkai Zheng, Rui Lu, Shuaiqi Duan, Shudan Zhang, Shulin Cao, Shuxun Yang, Weng Lam Tam, Wenyi Zhao, Xiao Liu, Xiao Xia, Xiaohan Zhang, Xiaotao Gu, Xin Lv, Xinghan Liu, Xinyi Liu, Xinyue Yang, Xixuan Song, Xunkai Zhang, Yifan An, Yifan Xu, Yilin Niu, Yuantao Yang, Yueyan Li, Yushi Bai, Yuxiao Dong, Zehan Qi, Zhaoyu Wang, Zhen Yang, Zhengxiao Du, Zhenyu Hou, and Zihan Wang. 2024. Chatglm: A family of large language models from glm-130b to glm-4 all tools.  
[4] Huiqiang Jiang, Qianhui Wu, Chin-Yew Lin, Yuqing Yang, and Lili Qiu. 2023a. LLMLingua: Compressing prompts for accelerated inference of large language models. In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing, pages 13358–13376, Singapore. Association for Computational Linguistics.  
[5] Huiqiang Jiang, Qianhui Wu, Xufang Luo, Dongsheng Li, Chin-Yew Lin, Yuqing Yang, and Lili Qiu. 2023b. Longllmlingua: Accelerating and enhancing llms in long context scenarios via prompt compression. arXiv preprint arXiv:2310.06839.  
[6] Zehan Li, Xin Zhang, Yanzhao Zhang, Dingkun Long, Pengjun Xie, and Meishan Zhang. 2023. Towards general text embeddings with multistage contrastive learning. arXiv preprint arXiv:2308.03281.  
[7] Weijie Liu, Peng Zhou, Zhiruo Wang, Zhe Zhao, Haotang Deng, and Qi Ju. 2020. FastBERT: a self-distilling BERT with adaptive inference time. In Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics, pages 6035–6044, Online. Association for Computational Linguistics.  
[8] Xing Han Lù. 2024. Bm25s: Orders of magnitude faster lexical search via eager sparse scoring.  
[9] Sheila Teo. 2023. How i won singapore’s gpt-4 prompt engineering competition.  
[10] Liang Wang, Nan Yang, and Furu Wei. 2023. Query2doc: Query expansion with large language models. arXiv preprint arXiv:2303.07678.  
[11] Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Fei Xia, Ed Chi, Quoc V Le, Denny Zhou, et al. 2022. Chain-of-thought prompting elicits reasoning in large language models. Advances in neural information processing systems, 35:24824–24837.  
[12] Ji Xin, Raphael Tang, Jaejun Lee, Yaoliang Yu, and Jimmy Lin. 2020. DeeBERT: Dynamic early exiting for accelerating BERT inference. In Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics, pages 2246–2251, Online. Association for Computational Linguistics.  


### 附录A 问答提示词模板  
#### A.1 Markdown格式问答模板  
## 目标  
请你结合上下文中k个5G运维私域文档的信息,回答给定的问题  
## 要求  
1. 可以分点作答,尽量详细且具体  
2. 不要简单复述上下文信息  
3. 不要使用自己的知识,只能根据上下文文档中的内容作答  
## 上下文  
{context_str}  
## 问题  
{query_str}  
## 回答  

#### A.2 思维链问答模板  
上下文信息如下:  
{context_str}  
请你基于上下文信息而不是自己的知识,回答以下问题,请一步步思考,先给出分析过程,再生成答案:  
{query_str}  
回答:  

#### A.3 侧重问答模板  
上下文信息如下:  
{context_str}  
请你基于上下文信息而不是自己的知识,回答以下问题,可以分点作答,0号文档的内容比较重要,可以重点参考,如果上下文信息没有相关知识,可以回答不确定,不要复述上下文信息:  
{query_str}  
回答:  

### 附录B 答案整合模板  
上下文:  
{top1_content_str}  
你将看到一个问题,和这个问题对应的参考答案  
请基于上下文知识而不是自己的知识补充参考答案,让其更完整地回答问题  
请注意,严格保留参考答案的每个字符,并将补充的内容和参考答案合理地合并,输出更长更完整的包含更多术语和分点的新答案  
问题:  
{query_str}  
参考答案:  
{answer_str}  
新答案: