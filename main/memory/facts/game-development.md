# 游戏开发方向

## 决策（2026-05-23）
用户偏好从 HTML5 小游戏转向 **抖音小游戏 + Steam 独立游戏** 双线并行。

## 当前进展
- HTML5 调研已完成（参考：`D:/game-projects/research/html5-games-blueprint.md`）
- 抖音小游戏调研已完成 → `D:/game-projects/research/douyin-mini-games-blueprint.md`
  - 推荐：三消益智（3-4周，20K DAU月收¥288K）+ 成语闯关（2-3周）
- Steam 独立游戏调研已完成 → `D:/game-projects/research/steam-indie-market-2026-05-23.md`
  - 推荐：恐怖模拟经营、中国悬疑解谜、放置自动化
- **GDD 已完成**：「消消消大作战」抖音三消立项文档 → `D:/game-projects/douyin-match3/GDD.md`
  - 11章+3附录，含核心玩法、50关设计、变现方案、技术方案、美术规范、4周排期
- **抖音小游戏官方文档**：https://developer.open-douyin.com/docs/resource/zh-CN/mini-game/develop/guide/dev-guide/bytedance-mini-game
- **Phase 1 完成**（W1）：核心玩法 MVP — 7模块（Board/MatchEngine/Renderer/InputHandler/ScoreSystem/Animation/Game）
- **Phase 2 完成**（W2）：完整单局 — 障碍物(冰块/锁链/巧克力)+Boss系统+音效+20关+5种目标类型
- **Phase 3a 完成**：元进度系统 — 6模块1050行(DataManager/CoinSystem/Characters/MapScreen/ShopUI/Navigation)
- **Phase 3b 进行中**：每日系统+关卡21-50+宝箱+社交UI框架
- **下一步**：Phase 3b 完成后 → Phase 4（变现+上线）

## 关键约束
- 游戏项目放在 D 盘（`D:/game-projects/`），不放在 loopcli 根目录
- 保存好项目进度，方便下一轮迭代继续
- 可同时开发多款
- 多 agent 协作：调研、立项、美术、创意
