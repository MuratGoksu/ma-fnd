# agents/url_crawler_agent.py
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup
import sys
import os

# Add parent directory to path for fact_check_detector
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from fact_check_detector import FactCheckDetector
    FACT_CHECK_AVAILABLE = True
except ImportError:
    FACT_CHECK_AVAILABLE = False

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "close",
}

def _download(url: str, headers: dict | None = None, timeout: int = 20, retries: int = 3, backoff: float = 1.5) -> bytes:
    """Retry’li indirici: 429 ve 5xx’te yeniden dener, diğer 4xx’te doğrudan hatayı yükseltir."""
    last_err = None
    hdrs = {**DEFAULT_HEADERS, **(headers or {})}
    for attempt in range(retries):
        try:
            req = Request(url, headers=hdrs)
            with urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                last_err = e
                time.sleep(backoff * (attempt + 1))
                continue
            raise
        except URLError as e:
            last_err = e
            time.sleep(backoff * (attempt + 1))
            continue
        except Exception as e:
            last_err = e
            time.sleep(backoff * (attempt + 1))
            continue
    if last_err:
        raise last_err
    raise RuntimeError(f"Failed to download {url} for unknown reasons.")

class URLCrawlerAgent:
    """Haber sayfasından (URL) başlık ve metni çeker (retry + fallback ile dayanıklı)."""
    def __init__(self):
        if FACT_CHECK_AVAILABLE:
            self.fact_check_detector = FactCheckDetector()
        else:
            self.fact_check_detector = None
    
    def fetch_news(self, url: str) -> dict:
        # 1) Önce standart URL’yi dene
        html_bytes = None
        primary_error = None
        try:
            html_bytes = _download(url)
        except Exception as e:
            primary_error = e

        # 2) Olmazsa text-only fallback (JS/anti-bot kaynaklı 500/429 için)
        used_fallback = False
        if html_bytes is None:
            try:
                stripped = url.replace("https://", "").replace("http://", "")
                fallback_url = f"https://r.jina.ai/http://{stripped}"
                html_bytes = _download(fallback_url, headers={"Accept": "text/plain"})
                used_fallback = True
            except Exception:
                if primary_error:
                    raise RuntimeError(f"Failed to fetch {url}: {primary_error}") from primary_error
                raise

        html = html_bytes.decode("utf-8", errors="replace")
        
        # Check for fact-check result FIRST (before parsing)
        fact_check_result = None
        if self.fact_check_detector:
            fact_check_result = self.fact_check_detector.extract_fact_check_result(url, html)

        headline = ""
        text = ""

        if not used_fallback:
            soup = BeautifulSoup(html, "html.parser")
            # Başlık - multiple strategies
            headline = ""
            # Strategy 1: Title tag
            if soup.title and soup.title.string:
                headline = soup.title.string.strip()
            # Strategy 2: H1 tag
            if not headline:
                h1 = soup.find("h1")
                if h1 and h1.get_text(strip=True):
                    headline = h1.get_text(strip=True)
            # Strategy 3: Meta og:title
            if not headline:
                og_title = soup.find("meta", property="og:title")
                if og_title and og_title.get("content"):
                    headline = og_title.get("content").strip()
            # Strategy 4: Meta title
            if not headline:
                meta_title = soup.find("meta", attrs={"name": "title"})
                if meta_title and meta_title.get("content"):
                    headline = meta_title.get("content").strip()
            headline = headline or "Untitled"

            # Metin - multiple strategies
            parts = []
            # Strategy 1: Article tag
            article = soup.find("article")
            if article:
                for p in article.find_all("p"):
                    txt = p.get_text(" ", strip=True)
                    if txt and len(txt) > 20:  # Filter very short paragraphs
                        parts.append(txt)
            # Strategy 2: Main content areas
            if not parts or len(" ".join(parts)) < 200:
                for selector in ["main", ".article-body", ".post-content", ".entry-content", "[role='main']"]:
                    main_content = soup.select_one(selector)
                    if main_content:
                        for p in main_content.find_all("p"):
                            txt = p.get_text(" ", strip=True)
                            if txt and len(txt) > 20:
                                parts.append(txt)
                        if len(" ".join(parts)) > 200:
                            break
            # Strategy 3: All paragraphs (fallback)
            if not parts or len(" ".join(parts)) < 200:
                for p in soup.find_all("p"):
                    txt = p.get_text(" ", strip=True)
                    if txt and len(txt) > 20:
                        parts.append(txt)
            text = " ".join(parts)[:8000]
        else:
            # Text-only: ilk satırı başlık kabul etmeye çalış, kalanını metin yap
            lines = [ln.strip() for ln in html.splitlines() if ln.strip()]
            if lines:
                cand = lines[0]
                headline = cand if len(cand) <= 200 else "Untitled"
                text = " ".join(lines[1:])[:8000] if headline != "Untitled" else " ".join(lines)[:8000]
            headline = headline or "Untitled"
            text = text or html[:8000]

        result = {
            "id": url,
            "headline": headline,
            "text": text,
            "link": url
        }
        
        # Add fact-check result if found
        if fact_check_result:
            result["fact_check"] = fact_check_result
            # If fact-check says it's fake, add indicators to text
            if fact_check_result.get("verdict") == "FAKE":
                result["text"] = f"[FACT-CHECK: {fact_check_result.get('site_name')} rated this as {fact_check_result.get('rating')}] " + result["text"]
            elif fact_check_result.get("verdict") == "REAL":
                result["text"] = f"[FACT-CHECK: {fact_check_result.get('site_name')} rated this as {fact_check_result.get('rating')}] " + result["text"]
        
        return result