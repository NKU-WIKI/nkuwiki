# nkuwiki 问答服务使用指南

## 简介

nkuwiki 问答服务是南开百科知识平台的智能问答系统，支持通过多种渠道访问，包括命令行终端、微信公众号等。本指南介绍如何配置和使用问答服务。

## 启动问答服务

问答服务可通过以下命令启动：

```bash
python app.py --qa
```

参数说明：

- `--qa`: 启动问答服务

## 渠道配置

问答服务支持多种交互渠道，可在配置文件中指定使用的渠道：

```json
{
  "services": {
    "channel_type": "terminal"  // 可选值: terminal, wechatmp, website
  }
}
```

### 支持的渠道

1. **终端渠道 (terminal)**

   适用于开发测试和本地使用，通过命令行直接与智能体交互。

2. **微信公众号渠道 (wechatmp)**

   通过微信公众号提供服务，需要配置相关的微信公众号参数：

   ```json
   {
     "services": {
       "wechatmp": {
         "appid": "your_appid",
         "appsecret": "your_appsecret",
         "token": "your_token"
       }
     }
   }
   ```

3. **网站渠道 (website)**

   通过网站提供服务，需要配置相关的网站参数。

## 渠道实现

问答服务使用工厂模式创建渠道实例：

```python
from services.channel_factory import create_channel

channel_type = config.get("services.channel_type", "terminal")
channel = create_channel(channel_type)
if channel:
    channel.startup()
```

所有渠道都实现了统一的接口，包括：

- `startup()`: 启动渠道服务
- `shutdown()`: 关闭渠道服务
- `send_message()`: 发送消息
- `receive_message()`: 接收消息

## 智能体配置

问答服务使用智能体处理用户查询，可以在配置文件中指定智能体类型和参数：

```json
{
  "core": {
    "agent": {
      "type": "coze",  // 智能体类型，可选值: coze, openai, hiagent
      "parameters": {
        // 智能体特定参数
      }
    }
  }
}
```

## 会话管理

问答服务使用会话管理器处理用户会话：

1. 会话初始化
2. 会话持久化
3. 会话上下文管理
4. 会话超时处理

## 使用示例

### 终端渠道

启动问答服务后，可在终端中直接与系统交互：

```text
User: 南开大学的校训是什么？
nkuwiki: 南开大学的校训是"允公允能，日新月异"。

User: 这句校训的含义是什么？
nkuwiki: "允公允能，日新月异"出自《礼记·大学》，意为既要有公德心，也要有能力；要日日更新，不断进步。
```

### 微信公众号渠道

用户关注配置好的微信公众号后，可直接在公众号中发送消息与系统交互。支持：

1. 文本消息交互
2. 语音消息识别与回复
3. 图片处理
4. 菜单导航

## 高级功能

### 插件系统

问答服务支持插件扩展，可通过配置插件增强系统功能：

```json
{
  "core": {
    "plugins": {
      "enabled": ["translate", "voice"]
    }
  }
}
```

### 多模态交互

除文本交互外，系统还支持：

1. 语音识别与合成
2. 图片理解与生成
3. 文档解析

## 故障排查

如遇到问题，请：

1. 检查配置文件是否正确
2. 查看日志文件获取详细错误信息
3. 确认网络连接状态
4. 验证智能体服务状态

## 问答服务指南

详细的问答服务使用指南。
