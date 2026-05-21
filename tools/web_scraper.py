"""
Web Scraper - Low-cost web scraping tool
Level 1: Static pages with known HTML structure (10-100 tokens)
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, List, Any
from datetime import datetime
import json
import time
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / "main" / "memory" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

class SimpleScraper:
    """Cost-optimized web scraper for static pages"""

    def __init__(self, cache_ttl: int = 60):
        self.cache_ttl = cache_ttl
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _get_cache_path(self, url: str) -> Path:
        import hashlib
        safe_name = hashlib.md5(url.encode()).hexdigest()
        return CACHE_DIR / f"scrape_{safe_name}.json"

    def _load_cache(self, url: str) -> Optional[Dict]:
        cache_path = self._get_cache_path(url)
        if not cache_path.exists():
            return None

        try:
            data = json.loads(cache_path.read_text())
            cache_time = datetime.fromisoformat(data['timestamp'])
            if (datetime.now() - cache_time).seconds < self.cache_ttl:
                return data['content']
        except:
            pass
        return None

    def _save_cache(self, url: str, content: Dict):
        cache_path = self._get_cache_path(url)
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'content': content
        }
        cache_path.write_text(json.dumps(cache_data, ensure_ascii=False))

    def scrape(
        self,
        url: str,
        selector: Optional[str] = None,
        extract: str = "text",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Scrape a static webpage

        Args:
            url: Target URL
            selector: CSS selector (optional)
            extract: What to extract - "text", "html", "attr", "all"
            use_cache: Use cached response if available

        Returns:
            {
                'url': str,
                'title': str,
                'content': str | List[str],
                'timestamp': str,
                'cached': bool
            }
        """
        if use_cache:
            cached = self._load_cache(url)
            if cached:
                return {**cached, 'cached': True}

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            result = {
                'url': url,
                'title': soup.title.string if soup.title else '',
                'timestamp': datetime.now().isoformat(),
                'cached': False
            }

            if selector:
                elements = soup.select(selector)
                if extract == "text":
                    result['content'] = [e.get_text(strip=True) for e in elements]
                elif extract == "html":
                    result['content'] = [str(e) for e in elements]
                elif extract == "attr":
                    result['content'] = [e.attrs for e in elements]
                else:  # all
                    result['content'] = [
                        {'text': e.get_text(strip=True), 'attrs': e.attrs}
                        for e in elements
                    ]
            else:
                result['content'] = soup.get_text(strip=True)

            if use_cache:
                self._save_cache(url, result)

            return result

        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'cached': False
            }

    def scrape_list(
        self,
        urls: List[str],
        selector: Optional[str] = None,
        delay: float = 1.0
    ) -> List[Dict]:
        """Scrape multiple URLs with rate limiting"""
        results = []
        for url in urls:
            results.append(self.scrape(url, selector))
            if delay > 0:
                time.sleep(delay)
        return results


# CLI interface
if __name__ == "__main__":
    import sys

    scraper = SimpleScraper()

    if len(sys.argv) > 1:
        url = sys.argv[1]
        selector = sys.argv[2] if len(sys.argv) > 2 else None

        result = scraper.scrape(url, selector)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Usage: python web_scraper.py <url> [css_selector]")
