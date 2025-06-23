import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np
import os
from sklearn.metrics import f1_score, precision_score, recall_score

def calculate_similarity(model, text1, text2):
    """
    计算两段文本的语义相似度
    """
    # 将文本转换为向量
    embedding1 = model.encode(text1, convert_to_tensor=True)
    embedding2 = model.encode(text2, convert_to_tensor=True)
    
    # 计算余弦相似度
    similarity = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
    return float(similarity)

def calculate_metrics(similarities, threshold=0.7):
    """
    根据相似度计算F1值、准确率和召回率
    
    Args:
        similarities: 相似度列表
        threshold: 判定为正确的相似度阈值
    """
    # 将相似度转换为二元预测结果
    predictions = [1 if sim >= threshold else 0 for sim in similarities]
    # 真实标签全为1（因为参考答案就是正确答案）
    true_labels = [1] * len(similarities)
    
    # 计算各项指标
    precision = precision_score(true_labels, predictions)
    recall = recall_score(true_labels, predictions)
    f1 = f1_score(true_labels, predictions)
    
    return precision, recall, f1

def evaluate_answers(excel_path, reference_col='参考答案', ai_col='ai答案', threshold=0.7):
    """
    评估Excel文件中参考答案和AI答案的语义相似度，并输出单个合并的结果表格
    对"判断"类型的问题计算F1值等指标，对"问答"类型的问题单独计算相似度统计
    
    Args:
        excel_path: Excel文件路径
        reference_col: 参考答案列名
        ai_col: AI答案列名
        threshold: 判定为正确的相似度阈值
    """
    # 读取Excel文件
    df = pd.read_excel(excel_path)
    
    # 加载sentence-transformers模型
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    # 存储相似度结果
    all_similarities = []
    judge_similarities = []  # 只存储判断题的相似度
    qa_similarities = []     # 存储问答题的相似度
    
    # 创建结果DataFrame
    results_df = pd.DataFrame()
    
    # 遍历每一行计算相似度
    for idx, row in df.iterrows():
        ref_answer = str(row[reference_col])
        ai_answer = str(row[ai_col])
        question_type = str(row['问题类型(自动填充)']) if '问题类型(自动填充)' in row else ''
        
        # 计算相似度
        similarity = calculate_similarity(model, ref_answer, ai_answer)
        all_similarities.append(similarity)
        if question_type == '判断':
            judge_similarities.append(similarity)
        elif question_type == '问答':
            qa_similarities.append(similarity)
        
        # 打印每行的相似度
        print(f"行 {idx + 1}:")
        print(f"问题类型: {question_type}")
        print(f"参考答案: {ref_answer}")
        print(f"AI答案: {ai_answer}")
        print(f"相似度: {similarity:.4f}")
        print(f"是否匹配: {'是' if similarity >= threshold else '否'}")
        print("-" * 50)
        
        # 添加到结果DataFrame
        results_df.loc[idx, '题号'] = f'问题{idx + 1}'
        results_df.loc[idx, '问题类型'] = question_type
        results_df.loc[idx, '参考答案'] = ref_answer
        results_df.loc[idx, 'AI答案'] = ai_answer
        results_df.loc[idx, '语义相似度'] = f"{similarity:.4f}"
        results_df.loc[idx, '是否匹配'] = '是' if similarity >= threshold else '否'
    
    # 计算平均相似度
    avg_similarity = np.mean(all_similarities)
    
    # 计算问答题的平均相似度
    if qa_similarities:
        qa_avg_similarity = np.mean(qa_similarities)
        qa_max_similarity = max(qa_similarities)
        qa_min_similarity = min(qa_similarities)
        has_qa_questions = True
    else:
        qa_avg_similarity = qa_max_similarity = qa_min_similarity = None
        has_qa_questions = False
    
    # 只对判断题计算F1值等指标
    if judge_similarities:
        precision, recall, f1 = calculate_metrics(judge_similarities, threshold)
        has_judge_questions = True
    else:
        precision = recall = f1 = None
        has_judge_questions = False
    
    # 打印评估指标
    print(f"\n总体平均相似度: {avg_similarity:.4f}")
    
    if has_qa_questions:
        print("\n问答题评估指标：")
        print(f"平均相似度: {qa_avg_similarity:.4f}")
        print(f"最高相似度: {qa_max_similarity:.4f}")
        print(f"最低相似度: {qa_min_similarity:.4f}")
    
    if has_judge_questions:
        print("\n判断题评估指标：")
        print(f"准确率: {precision:.4f}")
        print(f"召回率: {recall:.4f}")
        print(f"F1值: {f1:.4f}")
    else:
        print("\n没有发现判断题，不计算F1值等指标")
    
    # 添加分隔行
    separator_idx = len(results_df)
    results_df.loc[separator_idx] = ['---', '---', '---', '---', '---', '---']
    
    # 添加评估指标到同一个表格
    metrics_data = []
    
    # 1. 问答题评估指标
    if has_qa_questions:
        qa_metrics = [
            ['问答题评估指标', '', '', '', '', ''],
            ['问答题平均相似度', '', '', '', f"{qa_avg_similarity:.4f}", ''],
            ['问答题最高相似度', '', '', '', f"{qa_max_similarity:.4f}", ''],
            ['问答题最低相似度', '', '', '', f"{qa_min_similarity:.4f}", '']
        ]
        metrics_data.extend(qa_metrics)
        metrics_data.append(['---', '---', '---', '---', '---', '---'])
    
    # 2. 判断题评估指标
    if has_judge_questions:
        judge_metrics = [
            ['判断题评估指标', '', '', '', '', ''],
            ['判断题准确率', '', '', '', f"{precision:.4f}", ''],
            ['判断题召回率', '', '', '', f"{recall:.4f}", ''],
            ['判断题F1值', '', '', '', f"{f1:.4f}", '']
        ]
        metrics_data.extend(judge_metrics)
        metrics_data.append(['---', '---', '---', '---', '---', '---'])
    
    # 3. 总体评估指标
    overall_metrics = [
        ['总体评估指标', '', '', '', '', ''],
        ['相似度阈值', '', '', '', f"{threshold:.4f}", ''],
        ['总体平均相似度', '', '', '', f"{avg_similarity:.4f}", '']
    ]
    metrics_data.extend(overall_metrics)
    
    # 添加所有指标到DataFrame
    for metric_row in metrics_data:
        separator_idx += 1
        results_df.loc[separator_idx] = metric_row
    
    # 生成输出文件名
    output_dir = os.path.dirname(excel_path)
    output_filename = os.path.splitext(os.path.basename(excel_path))[0]
    output_path = os.path.join(output_dir, f"{output_filename}_评估结果.xlsx")
    
    # 保存结果到Excel文件
    results_df.to_excel(output_path, index=False)
    
    print(f"\n结果已保存到: {output_path}")
    print("表格包含：")
    print("1. 每个答案的详细比较")
    if has_qa_questions:
        print("2. 问答题评估指标")
    if has_judge_questions:
        print("3. 判断题评估指标")
    print("4. 总体评估指标")
    
    return all_similarities, judge_similarities, qa_similarities, precision, recall, f1 if has_judge_questions else None

if __name__ == "__main__":
    # 使用示例
    excel_path = "excel_evaluated/2025.03.18LLM测试集_top200_dk回答版_parallel.xlsx"  # 替换为你的Excel文件路径
    all_similarities, judge_similarities, qa_similarities, precision, recall, f1 = evaluate_answers(excel_path)
