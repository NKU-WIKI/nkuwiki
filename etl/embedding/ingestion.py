import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from etl import *
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.vector_stores.types import BasePydanticVectorStore
from llama_index.core.schema import TransformComponent, TextNode, NodeRelationship, MetadataMode, Document
from llama_index.core.callbacks.base import CallbackManager
from llama_index.core.selectors.llm_selectors import LLMSingleSelector
from llama_index.core.vector_stores import MetadataFilters, MetadataFilter, FilterOperator, FilterCondition
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import SimpleDirectoryReader
from llama_index.core.base.embeddings.base import BaseEmbedding
from etl.transform.splitter import SentenceSplitter
from llama_index.core.node_parser import HierarchicalNodeParser
from etl.transform.transformation import CustomTitleExtractor, CustomFilePathExtractor
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from __init__ import *

def merge_strings(A, B):
    # 找到A的结尾和B的开头最长的匹配子串
    max_overlap = 0
    min_length = min(len(A), len(B))

    for i in range(1, min_length + 1):
        if A[-i:] == B[:i]:
            max_overlap = i

    # 合并A和B，去除重复部分
    merged_string = A + B[max_overlap:]
    return merged_string


def get_node_content(node, embed_type=0, nodes: list[TextNode] = None, nodeid2idx: dict = None) -> str:
    # 添加空节点检查
    if node is None:
        return "无内容"
        
    try:
        text: str = node.get_content()
        if embed_type == 6:
            cur_text = text
            if cur_text.count("|") >= 5 and cur_text.count("---") == 0:
                cnt = 0
                flag = False
                while True:
                    pre_node_id = node.node.relationships[NodeRelationship.PREVIOUS].node_id
                    pre_node = nodes[nodeid2idx[pre_node_id]]
                    pre_text = pre_node.text
                    cur_text = merge_strings(pre_text, cur_text)
                    cnt += 1
                    if pre_text.count("---") >= 2:
                        flag = True
                        break
                    if cnt >= 3:
                        break
                if flag:
                    idx = cur_text.index("---")
                    text = cur_text[:idx].strip().split("\n")[-1] + cur_text[idx:]
            # print(flag, cnt)
        if embed_type == 1:
            if 'file_path' in node.metadata:
                text = '###\n' + node.metadata['file_path'] + "\n\n" + text
        elif embed_type == 2:
            if 'know_path' in node.metadata:
                text = '###\n' + node.metadata['know_path'] + "\n\n" + text
        elif embed_type == 3 or embed_type == 6:
            if "imgobjs" in node.metadata and len(node.metadata['imgobjs']) > 0:
                for imgobj in node.metadata['imgobjs']:
                    text = text.replace(f"{imgobj['cap']} {imgobj['title']}\n", f"{imgobj['cap']}.{imgobj['title']}:{imgobj['content']}\n")
        elif embed_type == 4:
            if 'file_path' in node.metadata:
                text = node.metadata['file_path']
            else:
                text = ""
        elif embed_type == 5:
            if 'know_path' in node.metadata:
                text = node.metadata['know_path']
            else:
                text = ""
        return text
    except Exception as e:
        # 添加错误处理
        print(f"获取节点内容时出错: {str(e)}")
        return "获取内容失败"


def read_data(data_path: str) -> List[Document]:
    """从给定路径读取文档数据
    
    Args:
        data_path: 数据目录路径
        
    Returns:
        读取的文档列表
    """
    reader = SimpleDirectoryReader(
        input_dir=data_path,
        required_exts=[".txt", ".pdf", ".docx", ".md", ".json"],
        exclude_hidden=True,
        recursive=True
    )
    
    try:
        documents = reader.load_data()
        if not documents:
            # 加载应急文档
            emergency_doc = BASE_PATH / "default.txt"
            if emergency_doc.exists():
                return [Document(text="应急文档内容")]
            raise ValueError("未找到任何有效文档")
        return documents
    except Exception as e:
        print(f"数据加载失败: {str(e)}")
        # 回退到应急文档
        return load_emergency_data()


def load_emergency_data():
    """加载应急数据"""
    emergency_doc = BASE_PATH / "default.txt"
    if emergency_doc.exists():
        return [Document(text=emergency_doc.read_text(encoding="utf-8"))]
    return [Document(text="未找到任何文档。")]


def build_preprocess(
        data_path=None,
        chunk_size=1024,
        chunk_overlap=50,
        split_type=0,  # 0-->Sentence 1-->Hierarchical
        callback_manager=None,
) -> List[TransformComponent]:
    if split_type == 0:
        parser = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            include_prev_next_rel=True,
            callback_manager=callback_manager,
        )
    else:
        parser = HierarchicalNodeParser.from_defaults(
            chunk_sizes=[chunk_size * 4, chunk_size],
            chunk_overlap=chunk_overlap,
            callback_manager=callback_manager,
        )
    transformation = [
        parser,
        CustomTitleExtractor(metadata_mode=MetadataMode.EMBED),
        CustomFilePathExtractor(last_path_length=100000, data_path=str(data_path) if data_path else "", metadata_mode=MetadataMode.EMBED),
    ]
    return transformation


def build_preprocess_pipeline(
        data_path=None,
        chunk_size=1024,
        chunk_overlap=50,
        split_type=0,
        callback_manager=None,
) -> IngestionPipeline:
    transformation = build_preprocess(
        data_path,
        chunk_size,
        chunk_overlap,
        split_type=split_type,
        callback_manager=callback_manager,
    )
    return IngestionPipeline(transformations=transformation)


def build_pipeline(
        llm: None,
        embed_model: BaseEmbedding,
        template: str = None,
        vector_store: BasePydanticVectorStore = None,
        data_path=None,
        chunk_size=1024,
        chunk_overlap=50,
        callback_manager=None,
) -> IngestionPipeline:
    transformation = build_preprocess(
        data_path,
        chunk_size,
        chunk_overlap,
        callback_manager=callback_manager,
    )
    transformation.extend([
        # SummaryExtractor(
        #     llm=llm,
        #     metadata_mode=MetadataMode.EMBED,
        #     prompt_template=template or SUMMARY_EXTRACT_TEMPLATE,
        # ),
        embed_model,
    ])
    return IngestionPipeline(transformations=transformation, vector_store=vector_store)


async def build_vector_store(
        qdrant_url: str = "http://localhost:6333",
        cache_path: str = "cache",
        reindex: bool = False,
        collection_name: str = "aiops24",
        vector_size: int = 3584,
) -> tuple[AsyncQdrantClient, QdrantVectorStore]:
    # 如果qdrant_url是标准的http地址，则使用URL连接
    # 否则使用本地路径
    if qdrant_url and qdrant_url.startswith(('http://', 'https://')):
        print(f"使用远程Qdrant服务: {qdrant_url}")
        client = AsyncQdrantClient(
            url=qdrant_url,
        )
    else:
        print(f"使用本地Qdrant存储: {cache_path}")
        client = AsyncQdrantClient(
            path=cache_path,
        )

    if reindex:
        try:
            await client.delete_collection(collection_name)
        except UnexpectedResponse as e:
            print(f"Collection not found: {e}")

    try:
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=vector_size, distance=models.Distance.COSINE
            ),
        )
    except Exception as e:
        print("集合已存在")
    return client, QdrantVectorStore(
        aclient=client,
        collection_name=collection_name,
        parallel=4,
        batch_size=32,
    )


def build_filters(dir):
    filters = MetadataFilters(
        filters=[
            MetadataFilter(
                key="dir",
                # operator=FilterOperator.EQ,
                value=dir,
            ),
        ]
    )
    return filters


def build_qdrant_filters(dir):
    filters = Filter(
        must=[
            FieldCondition(
                key="dir",
                match=MatchValue(value=dir),
            )
        ]
    )
    return filters
