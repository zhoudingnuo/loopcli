# LoopCLI 记忆

## 2026-05-22 轮次320

**微信通知修复**：
- wechat_bridge.py `_log`函数bug：首次调用时文件不存在导致静默失败（read_text在空文件上报错）
- `_monitor_reports`对PNG文件调用read_text崩溃，导致报告循环中断，18:03后的7条报告未发送
- 修复：_log改用append模式，_monitor_reports只处理*.md文件
- 手动补发了7条未发送报告

**WebUI深度优化**：
- 修复键盘事件bug：Escape弹窗关闭时误删`const key`声明，导致后续快捷键报"key is not defined"
- 修复创建Agent弹窗无法Escape关闭（原只处理非input的keydown）
- 性能页改用真实API数据替代随机模拟值
- 通知堆叠：限制最多3条，加max-height防溢出
- 进度条label截断：添加overflow/text-overflow样式
- 全部11个API端点200 OK，0个页面错误

**Playwright测试覆盖**：6页面导航、搜索过滤、弹窗开关、主题切换、数据导出、Agent启用禁用
