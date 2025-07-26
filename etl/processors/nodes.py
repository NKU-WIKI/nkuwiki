"""
节点处理工具模块

提供节点内容提取、合并等通用功能，供各个模块复用。
"""

from typing import List, Optional, Dict, Any
from llama_index.core.schema import TextNode, NodeRelationship


def merge_strings(A: str, B: str) -> str:
    """合并两个字符串，去除重复部分
    
    Args:
        A: 第一个字符串
        B: 第二个字符串
        
    Returns:
        合并后的字符串
    """
    # 找到A的结尾和B的开头最长的匹配子串
    max_overlap = 0
    min_length = min(len(A), len(B))

    for i in range(1, min_length + 1):
        if A[-i:] == B[:i]:
            max_overlap = i

    # 合并A和B，去除重复部分
    merged_string = A + B[max_overlap:]
    return merged_string


def get_node_content(node, embed_type: int = 0, nodes: List[TextNode] = None, nodeid2idx: Dict = None) -> str:
    """提取节点内容，支持多种嵌入类型
    
    Args:
        node: 要处理的节点
        embed_type: 嵌入类型 (0-6)
        nodes: 节点列表（用于embed_type=6）
        nodeid2idx: 节点ID到索引的映射（用于embed_type=6）
        
    Returns:
        处理后的节点内容
    """
    # 添加空节点检查
    if node is None:
        return "无内容"
        
    try:
        text: str = node.get_content()
        
        # embed_type=6: 特殊表格处理
        if embed_type == 6:
            cur_text = text
            if cur_text.count("|") >= 5 and cur_text.count("---") == 0:
                cnt = 0
                flag = False
                while True:
                    if not hasattr(node, 'relationships') or NodeRelationship.PREVIOUS not in node.relationships:
                        break
                    pre_node_id = node.relationships[NodeRelationship.PREVIOUS].node_id
                    if not nodes or not nodeid2idx or pre_node_id not in nodeid2idx:
                        break
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
        
        # embed_type=1: 添加文件路径前缀
        elif embed_type == 1:
            if 'file_path' in node.metadata:
                text = '###\n' + node.metadata['file_path'] + "\n\n" + text
        
        # embed_type=2: 添加知识路径前缀
        elif embed_type == 2:
            if 'know_path' in node.metadata:
                text = '###\n' + node.metadata['know_path'] + "\n\n" + text
        
        # embed_type=3,6: 图像对象处理
        elif embed_type == 3 or embed_type == 6:
            if "imgobjs" in node.metadata and len(node.metadata['imgobjs']) > 0:
                for imgobj in node.metadata['imgobjs']:
                    text = text.replace(
                        f"{imgobj['cap']} {imgobj['title']}\n", 
                        f"{imgobj['cap']}.{imgobj['title']}:{imgobj['content']}\n"
                    )
        
        # embed_type=4: 仅返回文件路径
        elif embed_type == 4:
            text = node.metadata.get('file_path', "")
        
        # embed_type=5: 仅返回知识路径
        elif embed_type == 5:
            text = node.metadata.get('know_path', "")
        
        return text
        
    except Exception as e:
        # 添加错误处理
        print(f"获取节点内容时出错: {str(e)}")
        return "获取内容失败"


def extract_node_metadata(record: Dict[str, Any]) -> Dict[str, Any]:
    """从数据库记录中提取节点元数据
    
    Args:
        record: 数据库记录
        
    Returns:
        格式化的元数据字典
    """
    return {
        'source_id': record.get('id'),
        'title': record.get('title'),
        'author': record.get('author'),
        'original_url': record.get('original_url'),
        'publish_time': str(record.get('publish_time')) if record.get('publish_time') else None,
        'pagerank_score': record.get('pagerank_score', 0.0),
        'platform': record.get('platform', ''),
    }


def generate_doc_id(record: Dict[str, Any], index: int = 0) -> str:
    """生成文档ID
    
    Args:
        record: 数据库记录
        index: 索引值（作为后备）
        
    Returns:
        生成的文档ID
    """
    doc_id = record.get('original_url')
    if not doc_id:
        doc_id = f"doc_{record.get('id', index)}"
    return doc_id 