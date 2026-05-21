#!/usr/bin/env python3
"""
自动化内容生成器
基于 topic_tracker 的热点数据生成技术分析文章
"""

import json
import os
from datetime import datetime
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "memory" / "cache"
OUTPUT_DIR = Path(__file__).parent / "output"

def load_topics():
    """加载最新热点数据"""
    topics_file = CACHE_DIR / "topics.json"
    if not topics_file.exists():
        return None
    with open(topics_file, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_article(topic):
    """基于热点话题生成技术分析文章"""
    title = topic["title"]
    url = topic["url"]
    score = topic["score"]
    comments = topic["comments"]

    # 简洁的内容生成模板
    article = f"""# {title}

## 热度分析

- **HN 评分**: {score} 点
- **评论数**: {comments} 条
- **来源**: [原文链接]({url})
- **抓取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 技术要点

这是一个在 HackerNews 上获得高关注度的技术话题。

### 关键信息

1. **热度指标**: {score} 分表明该话题在技术社区引发了强烈反响
2. **讨论深度**: {comments} 条评论显示社区对此有深入探讨
3. **技术影响**: 该话题涉及的技术领域可能对行业产生重要影响

### 行业启示

- 该技术趋势值得关注和跟进
- 可能对相关技术栈产生影响
- 建议深入研究其技术细节

## 相关资源

- [原文链接]({url})
- HackerNews 讨论

---

*本文由 LoopCLI 自动化内容生成系统基于热点数据自动生成*
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    return article

def save_article(title, content):
    """保存生成的文章"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 生成文件名（使用时间戳和标题简写）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    safe_title = title[:50].replace(" ", "_").replace("/", "-").replace(":", "-")
    filename = f"{timestamp}_{safe_title}.md"

    output_file = OUTPUT_DIR / filename
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

    return output_file

def main():
    """主流程"""
    print("[Content Gen] 启动自动化内容生成...")

    # 1. 加载热点数据
    data = load_topics()
    if not data:
        print("[Error] 未找到热点数据，请先运行 topic_tracker.py")
        return

    # 2. 获取最高分话题
    top_pick = data.get("top_pick")
    if not top_pick:
        print("[Error] 热点数据格式错误")
        return

    print(f"[Top Pick] {top_pick['title']} ({top_pick['score']}分)")

    # 3. 生成文章
    article = generate_article(top_pick)

    # 4. 保存文章
    output_file = save_article(top_pick['title'], article)

    print(f"[Success] 文章已生成: {output_file}")
    print(f"[Stats] 字数: {len(article)} 字符")

    return output_file

if __name__ == "__main__":
    main()
