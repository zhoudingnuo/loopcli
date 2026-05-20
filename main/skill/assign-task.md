# Skill: 派发任务

给已有 Agent 添加新任务。

## 用法
```bash
loopcli task <agent目录名> "任务标题" --desc "任务描述"
```

## 执行逻辑
1. 找到 D:\loopcli\<agent名>/memory/tasks.json
2. 追加新任务：{ id: 自增, status: "pending", title, description, created, assignee }
3. 写回 tasks.json

## 示例
```bash
loopcli task engineering-frontend-developer "优化首页加载" --desc "Lighthouse 60分 → 90+"
loopcli task main "部署到生产环境" --desc "合并 staging 分支并部署"
```
