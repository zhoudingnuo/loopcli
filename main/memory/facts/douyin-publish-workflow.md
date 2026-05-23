# 抖音小游戏发布流程

## 工具链
- **CLI工具**: `tmg` (tt-minigame-ide-cli) — `npm install -g tt-minigame-ide-cli`
- **备选CLI**: `tma` (tt-ide-cli) — `npm install -g tt-ide-cli`，支持token认证和提审
- **IDE**: `D:/tools/DouyinDevTools/抖音开发者工具.exe` — GUI，支持CLI但需先登录

## 认证方式
1. **邮箱登录**: `tmg login-e <email> <password>` — 需要密码
2. **手机登录**: `tmg login -m` — 交互式，需要验证码
3. **Token认证** (推荐CI/CD):
   - 在 developer.open-douyin.com 控制台 → 开发 → 开发配置 生成Token
   - `tma set-app-config <appId> --token <token>`

## 上传命令
```bash
tmg upload -v 1.0.0 -c "版本说明" D:/games/match3-xiaoxiaoxiao
```

## 发布后流程
1. 上传后到控制台「版本管理」查看开发版
2. 设为体验版本测试
3. 提审: `tma audit --host douyin tte7a1911c79c6fc8302`
4. 审核通过后发布

## 当前状态
- AppID: `tte7a1911c79c6fc8302`
- 游戏: 消消消大作战（三消）
- 项目路径: `D:/games/match3-xiaoxiaoxiao`
- 阻塞: 等待用户提供密码或Token

## 用户信息
- 手机: 18108431035
- 邮箱: 1163155015@qq.com
