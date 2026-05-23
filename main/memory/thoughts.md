# 工作记忆

## 2026-05-23 轮次495 (迭代67)

### 本轮行动
- 收到用户微信消息：提供注册密码 "116.abcabc"（对应QQ邮箱）
- 尝试 tmg login-e 和 tma login-e 登录 → 均报"账号或密码错误"
- 尝试直接 API 登录（developer.toutiao.com）→ 报"该应用无权限"
- Edge 浏览器未运行，无法通过 Playwright CDP 获取 cookie
- 已推送微信报告建议用户：1) 生成 Token；2) 重新打开 Edge

### 发布准备状态
- 消消消大作战：构建完成，等用户 Token 上传抖音
- 成语闯关：构建完成，需创建抖音游戏获取 AppID
- 修仙工厂：release/win-unpacked/ 可用，需 Steamworks 账号
- 深夜便利店：release/win-unpacked/ 可用，需 Steamworks 账号

### 阻塞项
- 抖音发布：用户密码登录失败（两个密码都试过），等 Token 或重新打开 Edge
- Steam 发布：需用户注册 Steamworks + 缴纳 $100
