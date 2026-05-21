# 微信桥接集成使用指南

本文档说明如何使用 LoopCLI 的微信桥接功能，通过微信个人号与本地 Agent 系统进行交互。

## 功能概述

微信桥接模块允许你：

1. **接收微信消息**：从微信发送的消息会自动写入 `D:\loopcli\main\inbox` 目录
2. **发送报告到微信**：`D:\loopcli\main\report` 目录中的新文件会自动发送到微信

## 前置要求

1. **微信 ilink bot token**：需要从微信 ilink 服务获取 Bearer token
2. **Python 环境**：需要安装 `requests` 库

```bash
pip install requests
```

## 快速开始

### 1. 设置微信 Token

首先保存你的微信 ilink bot token：

```bash
python run.py weixin --token YOUR_TOKEN_HERE
```

Token 会保存到 `D:\loopcli\.wechat_config.json` 文件中。

### 2. 验证配置

查看当前配置：

```bash
python run.py weixin --show
```

### 3. 启动 LoopCLI（启用微信）

```bash
python run.py run
```

如果配置文件中有 token，微信桥接会自动启动。

或者通过命令行参数指定：

```bash
python run.py run --wechat-token YOUR_TOKEN_HERE
```

### 4. 使用微信发送指令

在微信中向机器人发送消息，消息会自动写入 `inbox` 目录，格式如下：

```markdown
# 来自微信的消息

- 类型：指令
- 来源：微信 (user_id@im.wechat)
- 时间：2026-05-22 18:30:00
- 消息ID：123456

## 内容

你好，请帮我分析一下日志文件
```

### 5. 接收 Agent 报告

当 Agent 生成报告到 `D:\loopcli\main\report` 目录时，报告内容会自动发送到微信。

## 配置选项

### 命令行参数

- `--wechat-token`: 微信 ilink bot token
- `--wechat-inbox`: inbox 目录路径（默认：`D:/loopcli/main/inbox`）
- `--wechat-report`: report 目录路径（默认：`D:/loopcli/main/report`）

### 配置文件

配置文件位置：`D:\loopcli\.wechat_config.json`

```json
{
  "token": "your_token_here",
  "inbox_dir": "D:/loopcli/main/inbox",
  "report_dir": "D:/loopcli/main/report"
}
```

## 工作原理

### 消息接收流程

```
微信消息 → ilink API → WeChatBridge → WeChatInboxHandler → inbox/*.md
```

1. 微信消息通过 ilink API 长轮询接收
2. 消息被解析并保存为 markdown 文件到 `inbox` 目录
3. LoopCLI 主循环处理 `inbox` 中的消息

### 报告发送流程

```
report/*.md → WeChatInboxHandler 监控 → WeChatBridge → ilink API → 微信
```

1. 后台线程监控 `report` 目录
2. 检测到新文件后读取内容
3. 格式化后通过微信发送
4. 标记文件为已处理，避免重复发送

## 故障排查

### 微信桥接启动失败

**错误**：`微信桥接启动失败: ...`

**解决方法**：
1. 检查 token 是否正确
2. 检查网络连接
3. 查看详细错误信息

### 无法接收微信消息

**可能原因**：
1. Token 无效或过期
2. 用户 ID 不在允许列表中
3. 网络连接问题

**解决方法**：
1. 重新获取 token
2. 检查 `allow_from` 配置
3. 检查防火墙设置

### 报告未发送到微信

**可能原因**：
1. report 目录路径不正确
2. 缺少有效的 context_token
3. 文件已被处理过

**解决方法**：
1. 确认 report 目录路径
2. 先发送一条消息建立会话
3. 检查 `processed_reports.json` 状态文件

## 安全建议

1. **保护 Token**：不要将 token 提交到版本控制系统
2. **限制用户**：配置 `allow_from` 限制可以使用的用户
3. **使用 HTTPS**：确保 API 通信加密

## 高级配置

### 自定义允许用户列表

修改 `wechat_bridge.py` 中的 `allow_from` 参数：

```python
bridge = WeChatBridge(
    token="your_token",
    allow_from="user1@im.wechat,user2@im.wechat",  # 只允许这些用户
)
```

### 调整轮询间隔

```python
bridge = WeChatBridge(
    token="your_token",
    long_poll_timeout_ms=35000,  # 长轮询超时时间
)
```

## 常见问题

**Q: 如何获取微信 ilink bot token？**

A: 需要通过微信 ilink 服务或相关渠道获取。参考 cc-connect 的微信接入文档。

**Q: 支持哪些消息类型？**

A: 目前支持文本消息和语音转文字。图片和文件支持正在开发中。

**Q: 可以同时连接多个微信账号吗？**

A: 当前版本每个 LoopCLI 实例只支持一个微信账号。多账号支持可以通过运行多个实例实现。

**Q: 消息发送有长度限制吗？**

A: 微信单条消息限制约 3800 字符，超过会自动分段发送。

## 相关文件

- `wechat_bridge.py`: 微信桥接核心模块
- `run.py`: 主程序，包含微信集成
- `.wechat_config.json`: 微信配置文件
- `~/.loopcli/wechat/`: 微信状态目录

## 参考资源

- [cc-connect 项目](https://github.com/chenhg5/cc-connect)
- [微信 ilink API 文档](https://github.com/chenhg5/cc-connect/blob/main/docs/weixin.md)
