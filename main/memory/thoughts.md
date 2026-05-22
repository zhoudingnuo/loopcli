# LoopCLI 记忆

## 2026-05-22 轮次323

**WebUI用量统计增强**：
- 后端query_usage_summary()新增weekly字段（7天Token/调用统计），独立try不影响主数据
- 前端新增彩色进度条（barColor用硬编码hex色值，不用CSS变量以确保可见性）
- 显示：24h调用/Token、7天Token/调用、MCP月度配额(130/4000分钟=3%)、两个Token 5h配额(17%、29%)
- MCP配额详情显示"分钟"单位，Token配额API返回current=0/total=?所以不显示详情
- 前端用rgba(128,128,128,0.2)做进度条背景，确保在任何主题下可见

**经验**：进度条CSS变量(var(--green))在某些场景下不可见，用硬编码hex色值更可靠

## 2026-05-22 轮次320

**微信通知修复**：
- wechat_bridge.py `_log`函数bug：首次调用时文件不存在导致静默失败
- `_monitor_reports`对PNG文件调用read_text崩溃，修复：只处理*.md文件

**WebUI深度优化**：
- 修复键盘事件bug、性能页改用真实API数据、通知堆叠限制、进度条label截断
- 全部11个API端点200 OK，Playwright测试覆盖6页面
