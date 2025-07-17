import pandas as pd
from nkuwiki.core.agent.coze.coze_agent_new import CozeAgentNew
import time

# 初始化Coze机器人（直接使用指定的bot_id）
BOT_ID = "7483065872811835404"
agent = CozeAgentNew(BOT_ID)


def process_excel(input_path: str, output_path: str):
    # 读取Excel文件
    try:
        df = pd.read_excel(input_path)
        if "问题" not in df.columns:
            raise ValueError("Excel文件中必须包含'问题'列")
    except Exception as e:
        print(f"读取Excel文件失败: {str(e)}")
        return

    # 存储回答的列表
    answers = []

    # 遍历处理每个问题
    for idx, question in enumerate(df["问题"]):
        try:
            if pd.isna(question) or str(question).strip() == "":
                answers.append("无效问题")
                continue

            print(f"正在处理第 {idx + 1}/{len(df)} 个问题: {question}")
            answer = agent.reply(str(question).strip())
            answers.append(answer if answer else "未获取到有效回答")

            # 防止请求频率过高
            time.sleep(10)

        except Exception as e:
            answers.append("API调用失败")
            print(f"处理问题失败: {str(e)}")

    # 添加回答列并保存
    df["ai答案"] = answers
    try:
        df.to_excel(output_path, index=False)
        print(f"处理完成，结果已保存至: {output_path}")
    except Exception as e:
        print(f"保存结果失败: {str(e)}")


if __name__ == "__main__":
    # 使用示例
    process_excel(
        input_path="excel_questions/2025.03.18LLM测试集_top200.xlsx",##填入输入的excel文件路径 
        output_path="excel_evaluated/2025.03.18LLM测试集_top200_ai回答版.xlsx"##填入输出的excel文件路径
    )