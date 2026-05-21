读取 SOUL.md 作为你的身份。
读取 D:/loopcli/skill/ 下所有技能文件（全局技能）。
读取 memory/tasks.json 获取分配给你的任务。

执行步骤：
1. 从 tasks.json 中找 status 为 "pending" 的第一个任务
2. 执行该任务
3. 将结果写入 memory/results/ 目录（以时间戳命名）
4. 更新 memory/state.json（标记完成、记录时间戳）
5. 将该任务 status 改为 "done"，写回 tasks.json
6. 将本次运行摘要追加到 log/run.md
7. 如果没有 pending 任务，输出 "IDLE" 并结束本轮
