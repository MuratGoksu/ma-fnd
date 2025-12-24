# agents/url_crawler_agent.py
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup

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

        headline = ""
        text = ""

        if not used_fallback:
            soup = BeautifulSoup(html, "html.parser")
            # Başlık
            if soup.title and soup.title.string:
                headline = soup.title.string.strip()
            if not headline:
                h1 = soup.find("h1")
                if h1 and h1.get_text(strip=True):
                    headline = h1.get_text(strip=True)
            headline = headline or "Untitled"

            # Metin
            parts = []
            article = soup.find("article")
            if article:
                for p in article.find_all("p"):
                    txt = p.get_text(" ", strip=True)
                    if txt:
                        parts.append(txt)
            if not parts:
                for p in soup.find_all("p"):
                    txt = p.get_text(" ", strip=True)
                    if txt:
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

        return {"id": url, "headline": headline, "text": text}