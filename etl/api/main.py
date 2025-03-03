import json
import os
import sys
import tqdm
import argparse

# Add project root to PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from config import Config
from etl.retrieval.pipeline import EasyRAGPipeline
from etl.utils import get_yaml_data
from etl.api.api import read_jsonl, save_answers, write_jsonl

def get_test_data(split="val"):
    if split == 'test':
        queries = read_jsonl("data/question.jsonl")
    else:
        with open("data/val.json") as f:
            queries = json.loads(f.read())
    return queries


def main():
    parser = argparse.ArgumentParser(description='EasyRAG Pipeline')
    parser.add_argument('--query', type=str, help='Query string')
    parser.add_argument('--top_k', type=int, default=5, help='Number of top results to return')
    parser.add_argument('--threshold', type=float, default=0.5, help='Similarity threshold')
    args = parser.parse_args()

    try:
        # 从Config获取配置
        config = {}
        config['qdrant_url'] = Config().get('qdrant_url', "http://localhost:6334")
        config['qdrant_timeout'] = Config().get('qdrant_timeout', 30.0)
        config['embedding_name'] = Config().get('embedding_name', 'BAAI/bge-base-zh')
        config['auto_fix_model'] = Config().get('auto_fix_model', True)
        
        pipeline = EasyRAGPipeline()
        response = pipeline.query(args.query, top_k=args.top_k, threshold=args.threshold)
        print(response)
    except Exception as e:
        print(f"Error: {str(e)}")


def main_old(
        re_only=False,
        split='test',  # 使用哪个集合
        push=False,  # 是否直接提交这次test结果
        save_inter=True,  # 是否保存检索结果等中间结果
        note="best",  # 中间结果保存路径的备注名字
        config_path="/home/nkuwiki/nkuwiki/etl/EasyRAG/src/configs/easyrag.yaml",  # 配置文件
):
    # 读入配置文件
    config = get_yaml_data(config_path)
    config['re_only'] = re_only
    for key in config:
        print(f"{key}: {config[key]}")

    # 创建RAG流程
    rag_pipeline = EasyRAGPipeline(
        config
    )

    # 读入测试集
    queries = get_test_data(split)
    if not queries:
        raise ValueError("测试数据为空，请检查数据路径或数据格式")

    # 生成答案
    print("开始生成答案...")
    answers = []
    all_nodes = []
    all_contexts = []
    for query in tqdm(queries, total=len(queries)):
        res = rag_pipeline.run(query)
        answers.append(res['answer'])
        all_nodes.append(res['nodes'])
        all_contexts.append(res['contexts'])

    # 处理结果
    print("处理生成内容...")
    os.makedirs("outputs", exist_ok=True)

    # 本地提交
    answer_file = f"outputs/submit_result_{split}_{note}.jsonl"
    answers = save_answers(queries, answers, answer_file)
    print(f"保存结果至 {answer_file}")

    # docker提交
    answer_file = f"submit_result.jsonl"
    write_jsonl(answer_file, answers)



if __name__ == "__main__":
    main()
