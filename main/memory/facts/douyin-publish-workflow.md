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
- 游戏控制台URL: `https://developer.open-douyin.com/game-console/1065926/game-manage`
- 阻塞: 等待用户回复手机验证码或邮箱密码

## 用户信息
- 手机: 18108431035
- 邮箱: 1163155015@qq.com

## 踩坑记录（2026-05-23）
- 新版控制台游戏管理页（`console/miniapp/{appId}/version`）显示"网站升级中"，不可用
- 正确的游戏管理入口: `/game-console/1065926/game-manage`（从HTML中提取的href）
- `tmg` CLI 的 cookie 存储路径: `~/.tmg-cli/.cookies`（第一行是cookie字符串）
- 浏览器 cookies 对 API 服务器无效（域名不同：open-douyin.com vs toutiao.com）
- `tmg` 的上传 API 端点: `developer.toutiao.com/api/developer/ide/microgame/v1/testing`
- 发送验证码 API: `developer.toutiao.com/passport/web/send_code/`（返回 mobile_ticket）
- 游戏管理页面有4个iframe（summon.bytedance.com），游戏数据在主frame中但可能异步加载
