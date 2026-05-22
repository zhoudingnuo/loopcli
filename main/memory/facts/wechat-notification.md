---
name: wechat-notification
type: rule
tags: [wechat, notification, report, push, message]
created: 2026-05-22
---

# 微信通知规则

report/ 目录文件自动发送到用户微信。

## 必须推送
- 用户微信指令的执行结果
- Agent 执行失败/报错
- 系统关键状态变更

## 禁止推送
- 日常运行状态、维护操作
- 空闲 Agent 禁用
- 周期性检查结果

## 格式
`D:/loopcli/main/report/report_YYYYMMDD_HHMM.md`，≤200字。

**Related:** [[cost-control]]
