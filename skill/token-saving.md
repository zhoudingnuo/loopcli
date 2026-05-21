# Skill: 节省 Token

每个 Agent 运行都消耗 token。请遵守：

- 任务完成后立即报告结果到 main 的 inbox，不要多做额外工作
- 没有任务时输出 IDLE，不要自行探索
- 保持输出简洁，不要输出冗余信息
- 被禁用（AGENT 文件含 disabled）时正常退出
