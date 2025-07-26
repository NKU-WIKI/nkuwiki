# Services 模块

## 模块概述

Services模块是nkuwiki平台的服务模块，负责提供多渠道服务接口。该模块实现了多种渠道（如终端、微信公众号、企业微信等）的交互功能，为用户提供统一的访问入口。

## 子模块

### 1. terminal - 终端服务

提供命令行终端交互界面，主要用于开发和调试。

### 2. wechatmp - 微信公众号服务

提供微信公众号接入功能。

- **active_reply.py** - 主动回复功能
- **passive_reply.py** - 被动回复功能
- **wechatmp_channel.py** - 微信公众号渠道

### 3. wework - 企业微信服务

提供企业微信接入功能。

### 4. weworktop - 企业微信桌面版服务

提供企业微信桌面版接入功能。

### 5. website - 网站服务

提供网站接入功能。

## 核心文件

### 1. channel.py - 渠道基类

定义了所有渠道的基础接口，包括：

```python
class Channel:
    """渠道基类"""
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
    
    def startup(self):
        """启动渠道服务"""
        pass
    
    def shutdown(self):
        """关闭渠道服务"""
        pass
    
    def send_message(self, message):
        """发送消息"""
        pass
    
    def receive_message(self):
        """接收消息"""
        pass
```

### 2. chat_channel.py - 聊天渠道实现

提供了聊天渠道的具体实现，处理消息接收和处理逻辑。

### 3. chat_message.py - 消息数据模型

定义了消息的数据模型，包括文本、图片、语音等多种消息类型。

### 4. channel_factory.py - 渠道工厂

负责创建各种类型的渠道实例：

```python
def create_channel(channel_type="terminal"):
    """创建渠道实例"""
    if channel_type == "terminal":
        from services.terminal.terminal_channel import TerminalChannel
        return TerminalChannel(config, logger)
    elif channel_type == "wechatmp":
        from services.wechatmp.wechatmp_channel import WechatMPChannel
        return WechatMPChannel(config, logger)
    elif channel_type == "website":
        from services.website.website_channel import WebsiteChannel
        return WebsiteChannel(config, logger)
    # ... 其他渠道类型
    else:
        logger.error(f"不支持的渠道类型: {channel_type}")
        return None
```

## 配置

Services模块的配置项存储在config.json文件中，路径前缀为`services`：

```json
{
  "services": {
    "channel_type": "terminal",
    "wechatmp": {
      "appid": "your_appid",
      "appsecret": "your_appsecret",
      "token": "your_token"
    },
    "wework": {
      // 企业微信配置
    },
    "website": {
      // 网站配置
    }
  }
}
```

## 使用方法

### 创建渠道实例

```python
from services.channel_factory import create_channel

# 创建终端渠道
channel = create_channel("terminal")

# 启动渠道
channel.startup()

# 发送消息
channel.send_message("你好，这是一条测试消息")
```

### 自定义渠道

```python
from services.channel import Channel

class MyCustomChannel(Channel):
    def startup(self):
        self.logger.info("自定义渠道启动")
    
    def send_message(self, message):
        self.logger.info(f"发送消息: {message}")
    
    def receive_message(self):
        return "收到消息"
```

## 日志

使用debug级别记录详细信息，info级别记录重要信息。
