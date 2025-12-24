import time
import feedparser
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

class RSSCrawlerAgent:
    """RSS feed'ten en son girdiyi çeker (dayanıklı/parsing fallback + retry)."""
    def fetch_news(self, feed_url: str) -> dict:
        # 0) Önce feedparser'ı doğrudan URL ile deneriz (çoğu durumda yeterli)
        parsed = feedparser.parse(feed_url)
        ok = bool(getattr(parsed, "entries", [])) and not (getattr(parsed, "bozo", False) and not parsed.entries)

        if not ok:
            # 1) Retry + manual fetch (Content-Type hataları/bozo durumları için)
            last_err = None
            for attempt in range(3):
                try:
                    req = Request(feed_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urlopen(req, timeout=20) as resp:
                        content = resp.read()
                    parsed = feedparser.parse(content)
                    if getattr(parsed, "entries", []):
                        ok = True
                        break
                    last_err = RuntimeError("Empty entries after manual fetch")
                except (HTTPError, URLError, Exception) as e:
                    last_err = e
                time.sleep(1.5 * (attempt + 1))  # basit backoff

            if not ok:
                raise RuntimeError(f"RSS fetch/parse failed for {feed_url}: {last_err}")

        entry = parsed.entries[0]
        headline = (getattr(entry, "title", "") or "Untitled").strip()

        # Metin seçimi (summary > content > description)
        text = ""
        if getattr(entry, "summary", None):
            text = entry.summary
        elif getattr(entry, "content", None):
            try:
                if entry.content and len(entry.content) > 0:
                    text = entry.content[0].value
            except Exception:
                text = ""
        elif getattr(entry, "description", None):
            text = entry.description

        text = (text or "").strip()
        uid = getattr(entry, "id", None) or getattr(entry, "link", None) or f"rss-{int(time.time())}"
        return {"id": uid, "headline": headline, "text": text}