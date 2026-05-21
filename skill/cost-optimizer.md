# Skill: 成本优化器（Token Optimizer）

## 概述
基于 alexgreensh/token-optimizer 的成本优化技能，提供完整的 token 使用可见性和成本控制。

## 功能
- **每轮 token 明细**：输入、输出、缓存读/写，检测上下文突增
- **缓存分析**：输入 vs 输出 vs 缓存读/写 拆分，TTL 混合（1h vs 5m），命中率
- **成本追踪**：4 个定价层级（Anthropic API、Vertex Global、Vertex Regional、AWS Bedrock）
- **质量评分**：绿色健康、黄色降级、红色警告
- **子 Agent 成本拆分**：协调器 vs worker 花费，按成本排名的前 5 名
- **技能采用趋势**：实际调用的技能 vs 已安装的技能
- **CLAUDE.md 和 MEMORY.md 健康卡**：行数、孤立条目数、状态
- **节省追踪器**：来自优化的累计节省美元

## 安装
```bash
# 克隆仓库
git clone https://github.com/alexgreensh/token-optimizer.git ~/.claude/token-optimizer

# 或通过插件市场（推荐）
/plugin marketplace add alexgreensh/token-optimizer
/plugin install token-optimizer@alexgreensh-token-optimizer
```

## 使用
```bash
# 启动守护进程（可收藏 URL：http://localhost:24842/token-optimizer）
python3 measure.py setup-daemon

# 一次性通过 HTTP 提供仪表板
python3 measure.py dashboard --serve
```

## 价值
- **运行时浪费**：冗长的命令输出淹没上下文（15-25%）
- **结构性浪费**：臃肿的 CLAUDE.md、未使用的技能、重复的系统提醒、陈旧的 MEMORY.md（75-85%）

Token Optimizer 处理两者，并在压缩触发前检查点会话并恢复摘要删除的内容。

## 来源
- GitHub: https://github.com/alexgreensh/token-optimizer
- SkillsLLM: https://skillsllm.com/skill/token-optimizer
- Stars: 465+

## 成本影响
该技能本身不消耗 token，提供零上下文成本的仪表板，可在会话结束后自动更新。
