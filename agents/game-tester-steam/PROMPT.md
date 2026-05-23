# Prompt — Steam 游戏测试 Agent

## 任务
测试两款 Steam 独立游戏，确保完整可玩。

### 测试清单

#### 修仙自动化工厂 (D:/game-projects/steam-cultivation-factory/)
1. 读取 GDD.md 和源码
2. 检查 Electron 打包配置
3. 验证 TypeScript 编译无错误
4. 编写完整游玩流程测试
5. 测试存档系统（存档/读档/迁移）
6. 检查数值平衡
7. 修复发现的 bug

#### 深夜便利店 (D:/game-projects/steam-horror-sim/)
1. 同上
2. 检查恐怖事件触发逻辑
3. 检查光照系统性能
4. 检查叙事系统完整性

### 输出
完成后将测试报告写入 `D:/loopcli/main/inbox/game-tester-steam-report.md`
格式：每个游戏一个部分，列出通过/失败的测试项、发现的 bug、修复内容。

## 执行规则
- 读取 SOUL.md 获取身份
- 直接开始工作，不要问问题
- 完成后更新 memory/state.json
