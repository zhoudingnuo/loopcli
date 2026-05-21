# Skill: 启停 Agent

控制 Agent 的启用/禁用状态，节省 token。

## 禁用 Agent（无任务时关闭）
将 AGENT 文件内容改为 disabled：
```bash
Set-Content -Path "D:\loopcli\<agent名>\AGENT" -Value "disabled"
```
禁用后 loopcli 下一轮自动跳过该 Agent，不再消耗 token。

## 启用 Agent（有任务时打开）
```bash
Set-Content -Path "D:\loopcli\<agent名>\AGENT" -Value "type: main"
```
启用后 loopcli 下一轮自动启动该 Agent。

## 原则
- Agent 任务全部完成且没有新任务计划 → 立即禁用
- 需要派发任务时 → 先启用再派发
- 自己（main）永远不被禁用
