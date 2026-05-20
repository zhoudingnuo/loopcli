# Skill: 收件箱

每个 Agent 有自己的收件箱，用于接收消息和任务结果。

## 位置
`D:\loopcli\<agent名>\inbox\`

## 用法
发送消息给某 Agent：
```
写入 D:\loopcli\<agent名>\inbox\<来源>_<时间戳>.md
```

格式：
```markdown
# 来自 <来源> 的消息
- 类型：任务结果 / 通知 / 协作请求
- 内容：...
```

## 示例
- `main\inbox\code-reviewer_20260521.md` — 代码审查员发给 main 的审查报告
- `frontend-dev\inbox\main_20260521.md` — main 给前端开发者的新需求
