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
- **Phase 3b 完成**：DailySystem(396行)+SocialSystem(363行)+关卡21-50
- **Phase 4 完成**（W4）：AdManager(穿山甲SDK存根+6广告位+频率控制)+Analytics(11种事件埋点)，包体320KB
- **P1/P2修复+提审准备完成**（Task #25）：包体283KB，待补充图标/截图/隐私政策/SDK适配/JS压缩
- **成语闯关 W1 MVP 完成**（2026-05-23）：`D:/game-projects/douyin-idiom/`
  - 1040条成语DB + 出题引擎 + 答题判定 + 连击系统 + 20关 + 新手引导 + 音效
  - 国风主题UI：主菜单→关卡地图→答题→结算 完整导航
  - 提示系统+续命机制（广告存根）
- **成语闯关 W2 完成**（2026-05-23）：6新模块(TimedChallenge/IdiomCollection/DailySystem/PKMode/SocialManager/Characters)+关卡21-50
- **三消提审材料完成**（Task #28）：图标/截图/隐私政策/SDK适配/压缩/配置，待用户填appid+广告位ID
- **成语闯关 W3 派发**（Task #29）：穿山甲SDK+6广告位+埋点+提审材料+包体优化
- **Steam项目启动**：修仙自动化工厂 — 放置/自动化+修仙主题
- **GDD已完成**(Task #30)：`D:/game-projects/steam-cultivation-factory/GDD.md`（~28000字，16章）
  - 6大境界、6级自动化、12区域、7种丹药、14周开发计划
  - 技术栈：HTML5 Canvas + Electron + TypeScript + Vite
- **M1已完成**(Task #31)：基础框架搭建（Vite+TS+Electron+Canvas渲染+地图+建筑放置+手动采集）
- **M2已完成**(Task #32)：炼气期完整体验（境界突破、丹炉、修为、背包、音效、存档迁移），v0.2.0
- **M3已完成**(Task #33)：筑基+金丹 — 传送带、傀儡分拣、多区域地图、灵符系统，v0.3.0
- **M4已完成**(Task #34)：元婴+化神 — 跨区域传送、高级丹方、终局内容，v0.4.0 ✅
  - 5新地图+12新建筑+3丹方+4资源+跨区域传送+飞升挑战+39成就+存档迁移
- **M5 Phase1 已完成**（Task #35）：v0.5.0，Steam集成+Electron打包+UI优化
- **M5 Phase2 已完成**（Task #36）：v1.0.0 正式版 ✅
  - 14个bug修复（6 Critical/High + 4 Medium + 4 Low）
  - 平衡性调整（修炼速率提升2-4倍、傀儡减速、expGrowth降低）
  - Steam商店页面材料完成
  - TypeScript零错误编译、Vite构建96KB JS
- **修仙工厂 v1.0.0 正式版开发完成** — 下一步：Steam上传+发布
- **Steam恐怖模拟经营 — GDD已完成**：《深夜便利店》
  - GDD：D:/game-projects/steam-horror-sim/GDD.md（~28K字，16章）
  - **M1已完成**（Task #37）：项目搭建+Canvas渲染+30x25地图+WASD移动+E交互+光照+6阶段状态机
  - **M2已完成**（Task #38）：经营系统6模块完成，v0.1.0→v0.2.0
  - **M3已派发**（Task #39）：日循环系统 — DayCycle+光照升级+店铺升级+日结算+存档
  - 技术栈：Canvas+Electron+TS+Vite（与修仙工厂相同）
  - 参考：Lethal Company + Schedule I
  - 8周排期：M1→M2(经营)→M3(日循环)→M4(恐怖核心)→M5(深度恐怖)→M6(叙事)→M7(打磨)
- [[current-architecture]]

## 关键约束
- 游戏项目放在 D 盘（`D:/game-projects/`），不放在 loopcli 根目录
- 保存好项目进度，方便下一轮迭代继续
- 可同时开发多款
- 多 agent 协作：调研、立项、美术、创意
