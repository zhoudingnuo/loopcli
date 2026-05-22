# LoopCLI 记忆

## 2026-05-22 轮次302

**WebUI长期任务加载Bug修复**：
- 问题：长期任务文件存在但主页显示"加载中..."
- 根因：init()函数未调用loadLongTask()，只在设置页面才加载
- 修复：index.html的init()中添加loadLongTask()调用
- 文件：webui/index.html:2553

## 2026-05-22 轮次295-300

**WebUI深度优化（已完成）**：
- 综合测试91.7%，性能测试100%
- 移动端优化，创建test_api_endpoints.py等工具
- 所有Agent已禁用，成本控制良好
