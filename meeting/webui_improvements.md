# WebUI 改进任务

## 任务目标
优化 webui 界面，改进长期任务管理和用户体验

## 具体需求

### 1. 长期任务管理功能
- **修改功能**：允许用户编辑现有长期任务内容
- **取消功能**：提供清除/取消长期任务的按钮
- **界面位置**：将长期任务模块放到主页最醒目的位置

### 2. 界面优化要求
- 长期任务应该显示在主页顶部或显著位置
- 提供编辑和取消按钮
- 确认操作需要二次确认防止误操作

### 3. 测试要求
- 使用 playwright 测试所有新增功能
- 测试按钮交互
- 截图验证界面效果

## 相关文件
- `D:/loopcli/main/webui/server.py` - 后端API
- `D:/loopcli/main/webui/templates/index.html` - 前端页面
- `D:/loopcli/longtask.md` - 长期任务存储

## API端点（已存在）
- GET `/api/longtask` - 获取长期任务
- POST `/api/longtask/update` - 更新长期任务
- POST `/api/longtask/clear` - 清除长期任务

## 预期成果
1. 前端界面修改完成，长期任务显示在醒目位置
2. 编辑和取消功能正常工作
3. playwright 测试通过并截图
