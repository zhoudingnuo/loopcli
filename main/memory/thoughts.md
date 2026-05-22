# LoopCLI 工作记忆

## 2026-05-23 轮次342

**记忆系统迭代优化**：
- PROMPT.md 回忆触发规则从模糊的"根据任务需要"改为 5 条具体触发规则（修改代码前、遇到报错、调度Agent、用户提往事、发现wiki-link）
- 9 个 fact 文件全部添加 tags 标签（frontmatter），提高 Grep 搜索命中率
- 链式回忆限制最多 3 层，防止过度消耗 token
- 系统核心能力：Hot索引(~300 tokens/轮) → 按需Grep → wiki-link链式 → 3层截断
