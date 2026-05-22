# 任务 #24: 修复 P0 Bug 并准备抖音提审

**优先级**: P0 - 最高（阻塞提审，直接关系收入）
**预计时间**: 2-3 小时
**截止目标**: 今日完成

## 背景

三消游戏已完成全量测试，发现 3 个 P0 级 Bug 和若干提审材料缺失。这是通往收入的最快路径，必须优先完成。

## 子任务

### 1. 修复 P0 Bug（1-2小时）

**BUG-1: DailySystem clear_obstacle 事件双倍计数**
- 文件: `Board.js:262-263`
- 问题: `shuffle()` 假设所有格子都有 tile 对象，但巧克力障碍物会清空格子（grid[r][c] = null）。访问 null.color 会抛 TypeError。
- 修复: shuffle 前过滤掉 null 格子，或仅收集非 null 的颜色。

**BUG-3: ScoreSystem.useMove 允许第0步时继续操作**
- 文件: `ScoreSystem.js:70-73`
- 问题: `return this.getRemainingMoves() >= 0` — 当剩余步数为0时仍返回true，允许在最后一步之后再操作一次。
- 修复: 改为 `> 0` 或在 addMove 之后检查。

### 2. 创建抖音小游戏配置文件（30分钟）

创建以下文件：
- `game.json` - 游戏配置
- `project.config.json` - 项目配置
- 隐私政策页面
- SDK适配层（如果需要）

### 3. 调整关卡难度（15分钟）

- Level 35 Boss HP: 200 → 120
- Level 50 Boss HP: 300 → 180

## 验收标准

1. P0 Bug 全部修复，代码静态审查通过
2. 游戏可以正常启动（如果有运行环境）
3. 抖音提审材料齐全
4. 关卡难度平衡合理

## 报告输出

完成后将修复清单和配置文件保存到 `memory/results/` 并发送报告到 main inbox。
