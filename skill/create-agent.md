# Skill: 创建 Agent

从模板库创建新 Agent，自动注册到 loopcli。

## 用法
```bash
loopcli create <模板ID> --task "任务描述"
```

## 模板位置
D:\loopcli\subagent\，按部门分目录。模板文件格式：`<部门>/<模板ID>.md`
例如：`engineering/engineering-frontend-developer.md`

## 执行逻辑
1. 从 subagent/<部门>/<模板ID>.md 读取模板内容
2. 在 D:\loopcli\<模板ID>/ 下创建目录结构：
   - AGENT（标记文件，内容为 `type: main`）
   - SOUL.md（模板内容）
   - PROMPT.md（自动生成：读取 SOUL.md，读取 memory/tasks.json，执行任务，更新状态）
   - memory/tasks.json（含传入的任务）
   - memory/state.json（初始状态）
   - log/run.md（空日志）
3. loopcli 下一轮自动发现并启动该 Agent

## 示例
```bash
loopcli create engineering-frontend-developer --task "开发登录页面"
loopcli create engineering-code-reviewer --task "审查 PR #42"
loopcli create design-ui-designer --task "设计仪表盘界面"
```
