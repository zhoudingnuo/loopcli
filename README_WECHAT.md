# LoopCLI 微信桥接功能

微信桥接模块允许通过微信个人号与 LoopCLI Agent 系统进行交互。

## 快速开始

### 1. 安装依赖

```bash
pip install requests
```

### 2. 配置微信 Token

```bash
python run.py weixin --token YOUR_TOKEN_HERE
```

### 3. 启动 LoopCLI

```bash
python run.py run
```

微信桥接会自动启动，你就可以通过微信发送指令了！

## 功能特性

- ✅ **双向通信**：接收微信消息并自动发送报告
- ✅ **自动集成**：与 LoopCLI inbox/report 系统无缝集成
- ✅ **后台运行**：独立线程处理，不影响主循环
- ✅ **状态持久化**：保存连接状态和已处理文件记录
- ✅ **错误恢复**：自动重连和错误处理

## 文件结构

```
D:\loopcli\
├── wechat_bridge.py          # 微信桥接核心模块
├── run.py                     # 主程序（已集成微信）
├── .wechat_config.json        # 微信配置文件
├── examples/
│   └── wechat_example.py      # 使用示例
└── docs/
    └── wechat-integration.md  # 详细文档
```

## 使用场景

1. **远程控制**：通过微信发送指令给本地 Agent
2. **报告推送**：Agent 生成的报告自动发送到微信
3. **监控告警**：系统异常时实时通知
4. **移动办公**：随时随地与 Agent 交互

## 命令参考

### 配置命令

```bash
# 设置 token
python run.py weixin --token YOUR_TOKEN

# 查看配置
python run.py weixin --show
```

### 运行命令

```bash
# 使用配置文件中的 token
python run.py run

# 使用命令行参数
python run.py run --wechat-token YOUR_TOKEN

# 自定义目录
python run.py run --wechat-inbox /path/to/inbox --wechat-report /path/to/report
```

## 技术架构

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  微信客户端  │ ←──→ │  ilink API   │ ←──→ │ WeChatBridge │
└─────────────┘      └──────────────┘      └─────────────┘
                                                     ↓
                                              ┌──────────────┐
                                              │ InboxHandler │
                                              └──────────────┘
                                                     ↓
                                              ┌──────────────┐
                                              │ inbox/*.md   │
                                              └──────────────┘
```

## 安全建议

1. **保护 Token**：不要将 token 提交到版本控制
2. **限制用户**：配置 `allow_from` 限制授权用户
3. **使用 HTTPS**：确保 API 通信加密
4. **定期更新**：及时更新 token 和依赖

## 故障排查

### 连接失败
- 检查 token 是否正确
- 检查网络连接
- 确认 ilink 服务可用

### 消息未接收
- 检查用户权限设置
- 确认防火墙配置
- 查看日志输出

### 报告未发送
- 确认 report 目录路径
- 检查 context_token 是否有效
- 查看已处理文件记录

## 更多信息

详细使用说明请参考：[docs/wechat-integration.md](docs/wechat-integration.md)

## 许可证

MIT License - 与 LoopCLI 主项目一致
