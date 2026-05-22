---
name: webui-pitfalls
type: experience
tags: [webui, dark-theme, css, layout, bug-fix, frontend]
created: 2026-05-23
---

# WebUI 踩坑记录

## 深色主题白色背景
- **问题**：用户报告深色主题主背景仍为白色
- **根因**：`html` 元素和 `.main` 容器缺少显式 `background: var(--bg)`
- **修复**：为 `html` 和 `.main` 都添加 `background: var(--bg)`
- **教训**：CSS 变量继承不等于显式声明，浏览器默认白色会透出

## 搜索框与导出按钮重叠 (v8.6)
- **修复**：flex 布局 + `min-width:0` + `white-space:nowrap`

## 长期任务编辑区错位 (v8.6)
- **修复**：longtask-edit 移入 settings-section 内

## 统计卡片标签对比度
- `--text2` 从 `#9ca3af` 提升至 `#b0b8c4`

**Related:** [[current-architecture]]
