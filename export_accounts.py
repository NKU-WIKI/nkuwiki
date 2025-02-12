import pandas as pd
from dotenv import dotenv_values, set_key
import os

# 读取表格文件（假设是Excel格式）
df = pd.read_excel('公众号列表.xls')  # 根据实际文件类型修改读取方法

# 获取公众号名称列（列名可能需要根据实际情况调整）
accounts = df['公众号名称'].str.replace('微信公众号：', '', regex=False).unique().tolist()
accounts_str = ','.join(accounts)

# 读取现有.env文件
env_path = '.env'
config = dotenv_values(env_path)

# 更新或添加配置项
config['CLUB_OFFICIAL_ACCOUNT'] = accounts_str

# 写入.env文件（保留原有配置）
with open(env_path, 'w') as f:
    for key, value in config.items():
        f.write(f"{key}={value}\n") 