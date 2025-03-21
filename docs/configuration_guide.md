# nkuwiki 配置指南

本文档提供了nkuwiki项目的配置说明，包括创建配置文件、配置通道、配置智能体等内容。

## 配置项目

### 创建配置文件

```bash
# 复制配置模板（根据使用场景选择合适的模板）
# 以下是可用的配置模板：
# config-terminal.json - 终端调试通道配置
# config-wechatmp.json - 微信公众号通道配置
# config-wework.json - 企业微信通道配置
# config-wechatcom.json - 微信客服通道配置
# config-feishu.json - 飞书通道配置
# config-dingtalk.json - 钉钉通道配置
# config-website.json - 网站通道配置
# config-complete.json - 完整配置示例

# 例如，使用终端配置
cp config-template/config-terminal.json config.json

# 或者使用完整配置模板
# cp config-template/config-complete.json config.json
```

### 配置说明

以下是主要配置项说明：

1. **通道配置**:
   ```json
   "services": {
     "channel_type": "terminal", // 通道类型：terminal, wechatmp, wework, wechatcom, feishu, dingtalk, website
     "agent_type": "coze",       // 智能体类型：coze, zhipu, gemini, openai等
     "terminal": {               // 特定通道的配置
       "stream_output": true,
       "show_welcome": true,
       "welcome_message": "欢迎使用 NKU Wiki 智能助手!"
     }
   }
   ```

2. **智能体配置**:
   ```json
   "core": {
     "agent": {
       "coze": {                 // Coze智能体配置
         "base_url": "https://api.coze.cn",
         "api_key": "",
         "bot_id": ["your_bot_id_here"]
       }
     }
   }
   ```

3. **ETL配置**:
   ```json
   "etl": {
     "data": {
       "base_path": "./etl/data",
       "qdrant": {
         "url": "http://localhost:6333",
         "collection": "main_index"
       },
       "mysql": {
         "host": "127.0.0.1",
         "port": 3306,
         "user": "root",
         "password": "",
         "name": "mysql"
       }
     },
     "retrieval": {
       "retrieval_type": 3,
       "f_topk": 128
     },
     "embedding": {
       "name": "BAAI/bge-large-zh-v1.5"
     }
   }
   ```

完整的可用配置和注释请参见[config.py](../config.py)的`available_setting`和`config-template/config-complete.json`。

## 通道配置示例

### 终端通道

适用于开发调试，配置简单：

```bash
# 1. 复制终端配置模板
cp config-template/config-terminal.json config.json

# 2. 修改配置文件，设置bot_id和api_key

# 3. 运行服务
python app.py
```

### 微信公众号通道

用于在微信公众号中部署智能问答服务：

```bash
# 1. 复制微信公众号配置模板
cp config-template/config-wechatmp.json config.json

# 2. 修改配置文件，设置必要的参数
# - 设置bot_id和api_key
# - 设置微信公众号相关配置：app_id, app_secret, token, encoding_aes_key

# 3. 运行服务
python app.py
```

### 企业微信通道

用于在企业微信中部署智能问答服务：

```bash
# 1. 复制企业微信配置模板
cp config-template/config-wework.json config.json

# 2. 修改配置文件，设置必要的参数
# - 设置bot_id和api_key
# - 设置企业微信相关配置：corp_id, corp_secret, token, encoding_aes_key

# 3. 运行服务
python app.py
```

### 飞书/钉钉/网站通道

同样的方式，使用对应的配置模板，修改相关参数后运行服务。

更多通道配置详情请参考`config-template`目录下的模板文件和`config.py`的说明。 