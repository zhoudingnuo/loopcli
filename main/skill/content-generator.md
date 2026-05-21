# Skill: Content Generator

## 功能

自动生成有价值的技术内容，积累数字资产。

## 工作流

```bash
# 1. 追踪热点话题
cd D:/loopcli/content-generator && python topic_tracker.py

# 2. 生成内容
python auto_content_gen.py

# 3. 输出位置
D:/loopcli/content-generator/output/*.md
```

## 成本

- **Token**: 0（使用免费API）
- **时间**: ~5秒/篇文章
- **网络**: 最小（仅HackerNews API）

## 价值

- **内容资产**: 每篇625+字符的技术分析
- **热点捕捉**: 基于HN 1187+分话题
- **自动化**: 一键生成

## 使用场景

- 每日热点追踪
- 技术趋势分析
- 内容库积累

## 集成到主循环

每轮可执行：
```python
import subprocess
subprocess.run(["python", "D:/loopcli/content-generator/topic_tracker.py"])
subprocess.run(["python", "D:/loopcli/content-generator/auto_content_gen.py"])
```
