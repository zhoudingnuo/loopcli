# WebUI 长期任务管理改进

## 任务分配
来自主 agent 的任务分配，参考 `D:/loopcli/meeting/webui_improvements.md`

## 用户明确需求
1. **长期任务修改功能**：允许用户编辑现有长期任务
2. **长期任务取消功能**：提供清除/取消按钮
3. **界面位置**：长期任务放到主页最醒目的位置（不要在设置里）
4. **测试要求**：使用 playwright 测试所有功能，截图验证

## 技术要点
- 后端 API 已存在：`/api/longtask`、`/api/longtask/update`、`/api/longtask/clear`
- 主要工作在前端界面修改
- 必须用 playwright 测试并截图

## 完成标准
1. 长期任务显示在主页醒目位置
2. 编辑和取消功能可用
3. playwright 测试通过
4. 截图确认界面效果

完成后请向主 agent inbox 反馈结果。
