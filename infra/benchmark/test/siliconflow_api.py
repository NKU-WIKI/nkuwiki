import requests
import json
import pandas as pd
import time
from typing import Optional, List, Tuple
import concurrent.futures
from rich.console import Console
from rich.progress import Progress
from config import Config  # 导入配置类

# 初始化控制台
console = Console()

class SiliconFlowAPI:
    def __init__(self):
        # 从配置文件读取设置
        config = Config()
        self.api_url = config.core.agent.siliconflow.base_url
        self.api_key = config.core.agent.siliconflow.api_key
        self.model = config.core.agent.siliconflow.model
        self.settings = config.core.agent.siliconflow.settings
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_response(self, question: str) -> Optional[str]:
        """发送单个问题到API并获取回复"""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": question}
            ],
            **self.settings  # 展开settings中的配置
        }

        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            response_data = response.json()
            if 'choices' in response_data and len(response_data['choices']) > 0:
                return response_data['choices'][0]['message']['content']
            else:
                console.print(f"[red]API返回数据格式异常: {response_data}[/]")
                return None
                
        except requests.exceptions.RequestException as e:
            console.print(f"[red]API请求失败: {str(e)}[/]")
            return None
        except json.JSONDecodeError as e:
            console.print(f"[red]JSON解析失败: {str(e)}[/]")
            return None
        except Exception as e:
            console.print(f"[red]发生未知错误: {str(e)}[/]")
            return None

def process_questions_batch(api_client: SiliconFlowAPI, questions: List[Tuple[int, str]]) -> List[Tuple[int, str]]:
    """处理一批问题并返回结果"""
    results = []
    for idx, question in questions:
        try:
            if pd.isna(question) or str(question).strip() == "":
                results.append((idx, "无效问题"))
                continue

            console.print(f"[cyan]正在处理第 {idx + 1} 个问题: {question}[/]")
            answer = api_client.get_response(str(question).strip())
            results.append((idx, answer if answer else "未获取到有效回答"))

            # 防止请求频率过高
            time.sleep(10)

        except Exception as e:
            results.append((idx, "API调用失败"))
            console.print(f"[red]处理问题失败: {str(e)}[/]")
    
    return results

def process_excel_parallel(input_path: str, output_path: str, num_workers: int = 10):
    """并行处理Excel文件中的问题并保存回答"""
    console.print(f"[green]开始并行处理，使用 {num_workers} 个工作线程[/]")
    
    # 初始化多个API客户端
    api_clients = [SiliconFlowAPI() for _ in range(num_workers)]
    
    # 读取Excel文件
    try:
        df = pd.read_excel(input_path)
        if "问题" not in df.columns:
            raise ValueError("Excel文件中必须包含'问题'列")
    except Exception as e:
        console.print(f"[red]读取Excel文件失败: {str(e)}[/]")
        return

    # 准备问题批次，使用轮换策略分配问题
    questions = [(i, q) for i, q in enumerate(df["问题"])]
    total_questions = len(questions)
    batches = [[] for _ in range(num_workers)]
    
    # 轮换分配问题到不同的worker
    for i, question in enumerate(questions):
        worker_idx = i % num_workers
        batches[worker_idx].append(question)
    
    # 存储所有答案
    all_answers = [None] * total_questions
    
    console.print(f"[green]总问题数: {total_questions}[/]")
    
    # 使用线程池并行处理
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        # 提交所有任务
        future_to_batch = {
            executor.submit(
                process_questions_batch,
                api_clients[i],
                batch
            ): i for i, batch in enumerate(batches) if batch
        }
        
        # 收集结果
        for future in concurrent.futures.as_completed(future_to_batch):
            worker_idx = future_to_batch[future]
            try:
                results = future.result()
                for idx, answer in results:
                    all_answers[idx] = answer
            except Exception as e:
                console.print(f"[red]Worker {worker_idx} 处理批次时发生错误: {str(e)}[/]")

    # 添加回答列并保存
    df["ai答案"] = all_answers
    try:
        df.to_excel(output_path, index=False)
        console.print(f"[green]处理完成，结果已保存至: {output_path}[/]")
    except Exception as e:
        console.print(f"[red]保存结果失败: {str(e)}[/]")

if __name__ == "__main__":
    # 使用示例 - 并行处理
    process_excel_parallel(
        input_path="excel_questions/2025.03.18LLM测试集_top200.xlsx",
        output_path="excel_questions/2025.03.18LLM测试集_top200_dk回答版_parallel.xlsx",
        num_workers=10
    )