# 工作记忆

## 2026-05-23 轮次491 (迭代65)

### 本轮行动
- 收到用户微信消息"对应qq邮箱的"，确认密码162530zdn对应1163155015@qq.com
- 用tmg和tma分别尝试邮箱登录，均报"账号或密码错误"
- 尝试手机号18108431035发验证码，报"手机号错误"
- 结论：用户账号在developer.open-douyin.com（新平台）注册，而非developer.toutiao.com（旧平台），CLI工具用的旧平台认证
- 已推送微信报告，建议用户生成Token（方案1）或提供正确密码（方案2）
- 归档已处理的inbox消息

### 关键发现
- tmg/tma CLI 只认 developer.toutiao.com 的账号体系
- 用户的手机号和邮箱在旧平台都没有注册
- Token认证是最可靠的方案，无需密码

### 待办
- 等用户回复Token或新密码
- 收到Token后：`tma set-app-config tte7a1911c79c6fc8302 --token <token>` 然后上传游戏
