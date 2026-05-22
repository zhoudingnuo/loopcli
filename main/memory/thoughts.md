# LoopCLI 记忆

## 2026-05-22 轮次317

**WebUI v8.3优化**：
- 修复`SERVER_START_TIME`未定义bug，/api/health端点正常工作
- 安装psutil，Settings页显示真实系统资源（CPU/内存/磁盘）
- 清理7个旧HTML文件（index_v2~v7, enhanced等），省300KB
- 清理6个僵尸server.py进程
- Playwright测试：6/6页面导航通过，7/7按钮交互通过，零console错误
- 端口注意：WebUI端口是8080不是5000

**成本控制**：所有agent保持disabled，仅webui/server.py运行
