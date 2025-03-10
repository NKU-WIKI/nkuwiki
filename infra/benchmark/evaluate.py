import pandas as pd
import os

def select_top_questions():
    # 读取Excel文件
    file_path = r"D:\Code\nkuwiki\etl\data\benchmark\大模型测试集.xlsx"
    df = pd.read_excel(file_path)
    
    # 保留前100个问题
    first_100 = df.head(100)
    remaining = df.iloc[100:]
    
    # 定义领域权重
    domain_weights = {
        '学习': 2.0,
        '生活': 1.5,
        '考研': 2.0,
        '保研': 2.0,
        '科研': 2.0,
        '职业': 1.5,
    }
    default_weight = 1.0
    
    # 处理剩余问题：按领域分组并选择
    result_dfs = [first_100]  # 先添加前100个问题
    for domain in remaining['领域'].unique():
        domain_df = remaining[remaining['领域'] == domain]
        weight = domain_weights.get(domain, default_weight)
        n_select = max(1, int(len(domain_df) * 0.1 * weight))  # 根据权重调整选择数量
        top_questions = domain_df.head(n_select)
        result_dfs.append(top_questions)
    
    # 合并所有选中的问题
    result_df = pd.concat(result_dfs, ignore_index=True)
    
    # 保存结果
    output_dir = os.path.dirname(file_path)
    output_path = os.path.join(output_dir, '大模型测试集_top10.xlsx')
    result_df.to_excel(output_path, index=False)
    print(f"已生成筛选后的数据集，保存至: {output_path}")
    print(f"总问题数: {len(result_df)}")
    print(f"其中前100个问题数: {len(first_100)}")
    print(f"其中后续筛选问题数: {len(result_df) - len(first_100)}")
    
if __name__ == "__main__":
    select_top_questions()
