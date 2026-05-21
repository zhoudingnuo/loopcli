"""
Hot Topic Tracker for Content Generator
Tracks trending topics from Hacker News, GitHub, and Reddit.
Uses only FREE APIs to minimize costs.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import urllib.request
import urllib.error


class TopicTracker:
    """Track hot topics from free sources."""

    CACHE_DIR = Path(__file__).parent / "memory" / "cache"
    TOPICS_FILE = CACHE_DIR / "topics.json"

    def __init__(self):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _fetch(self, url: str) -> dict:
        """Fetch JSON from URL with minimal cost."""
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            return {"error": str(e)}

    def get_hacker_news_top(self, limit: int = 10) -> List[Dict]:
        """Get top stories from Hacker News (FREE API)."""
        data = self._fetch("https://hacker-news.firebaseio.com/v0/topstories.json")
        if "error" in data:
            return []

        topics = []
        for story_id in data[:limit]:
            story = self._fetch(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
            if "error" not in story and story.get("title"):
                topics.append({
                    "title": story["title"],
                    "url": story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                    "score": story.get("score", 0),
                    "comments": story.get("descendants", 0),
                    "source": "hackernews",
                    "timestamp": datetime.now().isoformat()
                })
        return topics

    def get_github_trending(self, language: str = "", limit: int = 10) -> List[Dict]:
        """
        Get trending repos from GitHub.
        Note: GitHub Trending has no official API, returns mock data structure.
        """
        # Since GitHub has no official trending API, we'll return a structure
        # that can be populated by web scraping later if needed
        return [{
            "title": f"Trending {language or 'general'} repos",
            "url": "https://github.com/trending",
            "source": "github",
            "timestamp": datetime.now().isoformat(),
            "note": "Manual check required or web scraper"
        }]

    def get_all_topics(self) -> Dict[str, List[Dict]]:
        """Get topics from all sources."""
        return {
            "hackernews": self.get_hacker_news_top(),
            "github": self.get_github_trending(),
            "last_updated": datetime.now().isoformat()
        }

    def save_topics(self, topics: Dict) -> None:
        """Save topics to cache."""
        with open(self.TOPICS_FILE, "w", encoding="utf-8") as f:
            json.dump(topics, f, indent=2, ensure_ascii=False)

    def load_topics(self) -> Dict:
        """Load cached topics."""
        if self.TOPICS_FILE.exists():
            with open(self.TOPICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def score_topic(self, topic: Dict) -> float:
        """Score a topic by potential value (0-100)."""
        score = 50  # Base score

        # Hacker News specific
        if topic.get("source") == "hackernews":
            score += min(topic.get("score", 0) / 10, 30)  # Up to 30 points
            score += min(topic.get("comments", 0) / 5, 20)  # Up to 20 points

        # Keywords that suggest high-value content
        high_value_keywords = ["tutorial", "guide", "how to", "ai", "ml", "python", "rust", "security"]
        title_lower = topic.get("title", "").lower()
        if any(kw in title_lower for kw in high_value_keywords):
            score += 10

        return min(score, 100)


def main():
    """Run topic tracker and save results."""
    tracker = TopicTracker()
    topics = tracker.get_all_topics()

    # Score and sort Hacker News topics
    if topics["hackernews"]:
        scored = [(t, tracker.score_topic(t)) for t in topics["hackernews"]]
        topics["hackernews"] = [t for t, _ in sorted(scored, key=lambda x: x[1], reverse=True)]
        topics["top_pick"] = topics["hackernews"][0] if topics["hackernews"] else None

    tracker.save_topics(topics)

    print(f"[OK] Fetched {len(topics['hackernews'])} HN topics")
    if topics.get("top_pick"):
        print(f"[TOP] {topics['top_pick']['title']}")
    print(f"[OK] Saved to {tracker.TOPICS_FILE}")

    return topics


if __name__ == "__main__":
    main()
