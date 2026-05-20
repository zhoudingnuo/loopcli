# Skill: 召开会议

Main 专用。创建一个会议目录，所有相关 Agent 将意见写入其中。

## 用法
创建会议：
```bash
mkdir D:\loopcli\meeting\<会议名>
```

写入议题：
```
D:\loopcli\meeting\<会议名>\agenda.md    # 议题（main 写入）
D:\loopcli\meeting\<会议名>\decisions.md  # 决议（main 写入）
```

Agent 参会：将意见写入 `D:\loopcli\meeting\<会议名>\<agent名>.md`

结束会议：main 总结决议后删除会议目录
```bash
Remove-Item D:\loopcli\meeting\<会议名> -Recurse -Force
```

## 示例
```
D:\loopcli\meeting\code-review-20260521\
├── agenda.md                          # main 提出的议题
├── decisions.md                       # main 最终决议
├── engineering-code-reviewer.md       # 代码审查员意见
└── engineering-security-engineer.md   # 安全工程师意见
```
