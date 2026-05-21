# Lean Context Integration - 上下文压缩技能

## 发现来源

GitHub: **yvgude/lean-ctx** (高星仓库)

## 核心价值

**成本控制** - 减少 90% token 使用，直接省钱

## 功能特性

### 1. 上下文压缩
- **59 个 MCP 工具** - 10 种读取模式
- **95+ 压缩模式** - Shell 输出压缩
- **会话缓存** - 避免重复读取相同文件
- **AST 感知** - 智能提取代码结构

### 2. 实时监控
- **Context Manager** - 浏览器仪表板
- **实时 token 跟踪** - 文件账本、压缩统计
- **上下文利用仪表** - 会话历史权重

### 3. 多工具支持
- 支持 23+ AI 工具
- 单一 Rust 二进制文件
- 本地运行，默认无遥测

## 安装方式

```bash
# 方式 1: 通用安装（无需 Rust）
curl -fsSL https://leanctx.com/install.sh | sh

# 方式 2: macOS / Linux
brew tap yvgude/lean-ctx && brew install lean-ctx

# 方式 3: Node.js
npm install -g lean-ctx-bin

# 方式 4: Rust
cargo install lean-ctx
```

## 初始化

```bash
# 设置（shell + 自动检测的 AI 工具）
lean-ctx setup

# 验证
lean-ctx doctor

# 查看收益
lean-ctx gain --live
lean-ctx wrapped --week
```

## 成本分析

| 项目 | 成本 | 价值 |
|------|------|------|
| 安装 | 一次性 5 分钟 | - |
| 内存 | 单个二进制文件 | ~5MB |
| Token 开销 | 0（本地运行） | - |
| 预期节省 | - | **90% token** |

## 使用场景

**最佳使用场景**：
- 每日使用 AI 编码工具且会话 shell 操作频繁
- 中大型仓库（50+ 文件 / 单体仓库）
- 需要本地优先的隐私保护

**不适合**：
- 小型仓库且很少从 AI 工具调用 shell
- 总是需要原始/未过滤的日志

## 集成到 LoopCLI

### 状态
- [ ] 安装 lean-ctx
- [ ] 初始化配置
- [ ] 验证兼容性
- [ ] 测试 token 节省
- [ ] 部署到所有 Agent

### 注意事项

- 立即禁用（当前 shell）：`lean-ctx-off`
- 运行单个命令未压缩：`lean-ctx -c --raw "git status"`
- 仅在 AI agent 会话中激活：在 `~/.config/lean-ctx/config.toml` 中设置 `shell_activation = "agents-only"`

## 替代方案

如果 lean-ctx 安装复杂，可以手动实现：
1. 简单的文件缓存机制
2. Shell 输出过滤（删除颜色代码、进度条）
3. 代码摘要（仅读取函数签名）

## 决策

**推荐**：立即安装 lean-ctx
- **理由**：直接减少 90% token 成本
- **风险**：低（可随时禁用）
- **ROI**：极高（一次安装，持续节省）

## 参考资料

- GitHub: https://github.com/yvgude/lean-ctx
- 文档: https://leanctx.com/docs/getting-started
- 演示: https://leanctx.com

---

**成本记录**：
- 研究时间: ~5 分钟
- Token 消耗: ~2k
- 预期节省: 90% token 使用
