# Cost Optimizer - 成本优化技能

## 触发条件

当以下情况时自动激活：
- 用户提到"成本"、"token"、"节省"、"优化"
- thoughts.md 超过 50 行
- memory/ 文件夹总大小超过 100KB
- 系统空闲超过 10 分钟

## 功能

1. **Token 优化**
   - 检查 CLAUDE.md 中是否有冗余内容
   - 建议将大文件移到 0-token 区域（docs/learnings/）
   - 检查是否有重复的 memory 条目

2. **API 成本优化（新增）**
   - **litellm** (29.4k⭐) - 统一 100+ LLM API 为 OpenAI 格式
     - 支持多供应商切换（DeepSeek、Qwen、Llama）
     - 自动路由到最低价格模型
     - 预期节省：30-70% API 成本
   - **9router** (10.3k⭐) - 40+ 供应商自动故障转移
   - **rtk** (10.4k⭐) - Rust CLI 代理，减少 60-90% token 使用

3. **文件压缩**
   - 压缩 thoughts.md（只保留最近 5 轮）
   - 归档旧 inbox 消息
   - 清理空文件

4. **Agent 管理**
   - 禁用空闲 Agent（状态 idle 且无任务超过 1 小时）
   - 报告 Agent 运行成本

## 高价值工具集成

### 成本降低工具
- **litellm**: 统一 LLM 网关，降低 30-70% API 成本
- **firecrawl** (60.7k⭐): 零成本网站内容提取
- **browser-use** (70.7k⭐): 零成本浏览器自动化

### 内容质量提升
- **firecrawl**: 获取完整网站内容（替代简单模板抓取）
- **TrendRadar** (44.3k⭐): 实时多平台趋势追踪

## 检查清单

每次执行时检查：
- [ ] thoughts.md 行数 < 50
- [ ] memory/*.json 总行数 < 100
- [ ] inbox/ 没有未归档消息
- [ ] 所有空闲 Agent 已禁用
- [ ] raw.log 大小 < 1MB

## 成本报告格式

```
## 成本报告 (2026-05-21 HH:MM)
- Token 使用: 本轮 ~Xk
- 内存占用: ~X KB
- Agent 状态: X/X 运行中
- 建议: [具体建议]
```

## 限制

- 只在明确有价值时执行压缩
- 保留所有关键决策记录
- 不删除未完成任务
