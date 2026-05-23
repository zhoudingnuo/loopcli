# Prompt — 抖音小游戏测试 Agent

## 任务
测试两款抖音小游戏，确保能在手机上正常运行。

### 测试清单

#### 三消游戏 (D:/game-projects/douyin-match3/)
1. 读取 GDD.md 和源码
2. 检查所有交互是否使用 touch 事件
3. 检查 Canvas resize 适配逻辑
4. 检查抖音 API 调用是否正确（tt.* API）
5. 编写自动化测试
6. 修复发现的兼容性问题

#### 成语闯关 (D:/game-projects/douyin-idiom/)
1. 同上
2. 检查文字输入在手机端的适配
3. 检查滚动列表在触摸屏的表现

### 输出
完成后将测试报告写入 `D:/loopcli/main/inbox/game-tester-mobile-report.md`
格式：每个游戏一个部分，列出通过/失败的测试项、发现的 bug、修复内容。

## 执行规则
- 读取 SOUL.md 获取身份
- 直接开始工作，不要问问题
- 完成后更新 memory/state.json
