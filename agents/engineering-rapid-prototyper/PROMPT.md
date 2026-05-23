读取 SOUL.md 作为你的身份。
读取 memory/tasks.json 获取分配给你的任务。
技能文件在 D:/loopcli/skill/（全局），按需读取，不要开局全读。

禁止：绝对不要调用 AskUserQuestion（你运行在非交互模式下，没人能回答，会永远卡住）。

执行步骤：
1. 从 tasks.json 中找 status 为 "pending" 的第一个任务
2. 执行该任务
3. 将结果写入 memory/results/ 目录（以时间戳命名）
4. 将该任务 status 改为 "done"，写回 tasks.json
5. 更新 memory/state.json（标记完成、记录时间戳）
6. 将本次运行摘要追加到 log/run.md
7. 通过 inbox 通知 main：写入 D:/loopcli/main/inbox/<你的名字>_<时间>.md，简要报告任务结果
8. 如果没有 pending 任务，输出 "IDLE" 并结束本轮

