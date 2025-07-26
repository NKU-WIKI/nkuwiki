##修复：未获取到有效回答时，进行重试
import pandas as pd
import time
import random
from nkuwiki.core.agent.coze.coze_agent_new import CozeAgentNew

# 初始化Coze机器人（直接使用指定的bot_id）
BOT_ID = "7483065872811835404"
agent = CozeAgentNew(BOT_ID)

def retry_failed_answers(input_path: str, output_path: str = None, max_retries: int = 8, 
                         min_delay: int = 10, max_delay: int = 20):
    """
    重新处理未获取到有效回答的问题
    
    参数:
        input_path: 包含已有回答的Excel文件路径
        output_path: 输出结果的Excel文件路径，默认为None（覆盖输入文件）
        max_retries: 每个问题的最大重试次数
        min_delay: 每次请求之间的最小延迟时间（秒）
        max_delay: 每次请求之间的最大延迟时间（秒）
    """
    # 如果未指定输出路径，则覆盖输入文件
    if output_path is None:
        output_path = input_path
    
    # 读取Excel文件
    try:
        df = pd.read_excel(input_path)
        if "问题" not in df.columns or "ai答案" not in df.columns:
            raise ValueError("Excel文件中必须包含'问题'和'ai答案'列")
    except Exception as e:
        print(f"读取Excel文件失败: {str(e)}")
        return
    
    # 计数器
    retry_count = 0
    success_count = 0
    
    # 遍历处理每个问题
    for idx, row in df.iterrows():
        question = row["问题"]
        answer = row["ai答案"]
        
        # 检查是否需要重试
        if answer == "未获取到有效回答" or answer == "API调用失败":
            if pd.isna(question) or str(question).strip() == "":
                continue
                
            print(f"正在重新处理第 {idx + 1} 行问题: {question}")
            retry_count += 1
            
            # 尝试重新获取回答
            for attempt in range(max_retries):
                try:
                    new_answer = agent.reply(str(question).strip())
                    if new_answer and new_answer.strip():
                        df.at[idx, "ai答案"] = new_answer
                        print(f"✓ 成功获取回答 (尝试 {attempt + 1}/{max_retries})")
                        success_count += 1
                        break
                    else:
                        print(f"× 第 {attempt + 1}/{max_retries} 次尝试未获取到有效回答")
                except Exception as e:
                    print(f"× 第 {attempt + 1}/{max_retries} 次尝试失败: {str(e)}")
                
                # 最后一次尝试失败后不需要等待
                if attempt < max_retries - 1:
                    # 使用随机延迟时间
                    random_delay = random.uniform(min_delay, max_delay)
                    print(f"等待 {random_delay:.1f} 秒后重试...")
                    time.sleep(random_delay)
    
    # 保存结果
    try:
        df.to_excel(output_path, index=False)
        print(f"\n处理完成:")
        print(f"- 共重试: {retry_count} 个问题")
        print(f"- 成功修复: {success_count} 个问题")
        print(f"- 结果已保存至: {output_path}")
    except Exception as e:
        print(f"保存结果失败: {str(e)}")

if __name__ == "__main__":
    # 使用示例
    retry_failed_answers(
        input_path="excel_questions/2025.03.18LLM测试集_top200_ai回答版.xlsx",
        output_path="excel_questions/2025.03.18LLM测试集_top200_ai回答版（修复版）.xlsx",
        max_retries=8,
        min_delay=10,
        max_delay=20
    ) 