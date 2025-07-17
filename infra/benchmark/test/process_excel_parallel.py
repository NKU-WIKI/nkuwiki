import pandas as pd
from nkuwiki.core.agent.coze.coze_agent_new import CozeAgentNew
import time
import concurrent.futures
from typing import List, Tuple
import math

# 初始化10个Coze机器人
BOT_IDS = [
    "7483065872811835404",  # 请替换为实际的10个bot IDs
    "7483065872811835405",
    "7483065872811835406",
    "7483065872811835407",
    "7483065872811835408",
    "7483065872811835409",
    "7483065872811835410",
    "7483065872811835411",
    "7483065872811835412",
    "7483065872811835413",
]

def process_questions_batch(agent: CozeAgentNew, questions: List[str], start_idx: int) -> List[Tuple[int, str]]:
    """处理一批问题并返回结果"""
    results = []
    for idx, question in enumerate(questions):
        try:
            if pd.isna(question) or str(question).strip() == "":
                results.append((start_idx + idx, "无效问题"))
                continue

            print(f"Bot {agent.bot_id} 正在处理第 {start_idx + idx + 1} 个问题: {question}")
            answer = agent.reply(str(question).strip())
            results.append((start_idx + idx, answer if answer else "未获取到有效回答"))

            # 防止请求频率过高
            time.sleep(10)

        except Exception as e:
            results.append((start_idx + idx, "API调用失败"))
            print(f"处理问题失败: {str(e)}")
    
    return results

def process_excel_parallel(input_path: str, output_path: str, questions_per_bot: int = 40):
    # 读取Excel文件
    try:
        df = pd.read_excel(input_path)
        if "问题" not in df.columns:
            raise ValueError("Excel文件中必须包含'问题'列")
    except Exception as e:
        print(f"读取Excel文件失败: {str(e)}")
        return

    # 计算需要的bot数量
    total_questions = len(df)
    num_bots = len(BOT_IDS)
    
    print(f"总问题数: {total_questions}")
    print(f"使用 {num_bots} 个bot进行处理")
    
    # 初始化所有bot
    agents = [CozeAgentNew(bot_id) for bot_id in BOT_IDS]
    
    # 准备问题批次，使用轮换策略分配问题
    questions = df["问题"].tolist()
    batches = [[] for _ in range(num_bots)]  # 为每个bot创建一个批次列表
    
    # 轮换分配问题到不同的bot
    for i, question in enumerate(questions):
        bot_idx = i % num_bots
        batches[bot_idx].append((i, question))
    
    # 存储所有答案
    all_answers = [None] * total_questions
    
    # 使用线程池并行处理
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_bots) as executor:
        # 提交所有任务
        future_to_batch = {
            executor.submit(
                process_questions_batch,
                agents[i],
                [q[1] for q in batch],  # 提取问题文本
                batch[0][0] if batch else 0  # 使用第一个问题的索引作为起始索引
            ): i for i, batch in enumerate(batches)
        }
        
        # 收集结果
        for future in concurrent.futures.as_completed(future_to_batch):
            bot_idx = future_to_batch[future]
            try:
                results = future.result()
                for idx, answer in results:
                    all_answers[idx] = answer
            except Exception as e:
                print(f"Bot {BOT_IDS[bot_idx]} 处理批次时发生错误: {str(e)}")

    # 添加回答列并保存
    df["ai答案"] = all_answers
    try:
        df.to_excel(output_path, index=False)
        print(f"处理完成，结果已保存至: {output_path}")
    except Exception as e:
        print(f"保存结果失败: {str(e)}")

if __name__ == "__main__":
    # 使用示例
    process_excel_parallel(
        input_path="excel_questions/2025.03.18LLM测试集_top200.xlsx",
        output_path="excel_questions/2025.03.18LLM测试集_top200_ai回答版_parallel.xlsx"
    ) 