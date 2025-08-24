# 企业微信自建应用通道

本模块实现了与企业微信自建应用的集成，允许通过企业微信应用接收和回复消息。

## 特性

- 支持企业微信自建应用API集成

- 支持私聊和群聊消息

- 支持文本消息收发

- 支持HTTP回调接口

- 支持多线程消息处理

- 支持token自动刷新

## 前置条件

1. 已创建企业微信账号和企业

2. 已在企业微信管理后台创建自建应用

3. 已获取企业ID(corp_id)、应用Secret(corp_secret)和应用ID(agent_id)

## 配置说明

在`config.json`中配置企业微信自建应用通道：

```json
{
  "services": {
    "channel_type": "weworktop",
    "weworktop": {
      "corp_id": "your_corp_id",
      "corp_secret": "your_corp_secret",
      "agent_id": 1000001,
      "port": 5001,
      "token": "your_token",
      "aes_key": "your_aes_key",
      "single_chat_prefix": [""],
      "single_chat_reply_prefix": "",
      "group_chat_prefix": ["小知", "@小知"],
      "group_name_white_list": ["南开知识社区", "南开百科测试群"],
      "image_create_prefix": ["画", "生成图片", "创建图像"],
      "speech_recognition": true,
      "conversation_max_tokens": 4000,
      "max_single_msg_tokens": 1000
    }
  }
}

```text

### 配置参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| corp_id | string | 企业ID |
| corp_secret | string | 应用Secret |
| agent_id | int | 应用ID |
| port | int | HTTP回调服务端口 |
| token | string | 企业微信回调Token |
| aes_key | string | 消息加解密密钥 |
| single_chat_prefix | array | 私聊触发前缀 |
| single_chat_reply_prefix | string | 私聊回复前缀 |
| group_chat_prefix | array | 群聊触发前缀 |
| group_name_white_list | array | 群聊白名单 |
| image_create_prefix | array | 图像生成触发前缀 |
| speech_recognition | bool | 是否开启语音识别 |
| conversation_max_tokens | int | 会话最大token数 |
| max_single_msg_tokens | int | 单条消息最大token数 |

## 使用方法

1. 在企业微信管理后台创建自建应用并获取必要参数

2. 在`config.json`中配置企业微信自建应用通道

3. 设置应用的接收消息服务器：
   - URL: `http://your_server_ip:your_port/wework_callback`
   - Token: 与配置中的token保持一致
   - EncodingAESKey: 与配置中的aes_key保持一致

4. 设置`channel_type`为`weworktop`

5. 启动服务：`python app.py`

## 部署注意事项

1. 确保服务器能够被企业微信访问（公网IP或内网穿透）

2. 确保端口已开放并且没有被防火墙阻止

3. 如果使用HTTPS，需要配置证书

## 对比个人微信号(wework)通道

| 功能 | weworktop | wework |
|------|-----------|--------|
| 适用场景 | 企业内部应用 | 个人使用 |
| 实现方式 | 官方API | 非官方API |
| 稳定性 | 高 | 受微信升级影响 |
| 功能限制 | 较少 | 较多 |
| 支持平台 | 跨平台 | 仅Windows |
| 认证方式 | API密钥 | 扫码登录 |
