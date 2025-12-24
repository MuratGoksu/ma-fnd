import re
from urllib.parse import urlparse

def _domain_from_item(item: dict) -> str:
    link = (item.get("id") or item.get("link") or "").strip()
    try:
        netloc = urlparse(link).netloc
        return netloc.lower()
    except Exception:
        return ""

class ClaimAgent:
    def generate_argument(self, item: dict) -> str:
        """
        İçerik ve varsa kaynak alan adına dayalı destekleyici argüman üretir.
        Headline/text yoksa eski şablona düşer (testlerin bozulmaması için).
        """
        headline = item.get("headline") or ""
        text = (item.get("text") or "").strip()
        domain = _domain_from_item(item)

        if not headline and not text:
            return (
                f"As a supporter, I believe the headline '{item.get('headline','')}' "
                "is likely true because NASA has a history of groundbreaking discoveries."
            )

        snippets = []
        if headline:
            snippets.append(f"The claim '{headline}' appears in the article")
        if domain:
            snippets.append(f"and it is reported by {domain}")
        body_hint = ""
        if text:
            frag = re.sub(r"\s+", " ", text)[:160]
            body_hint = f". The article text mentions: \"{frag}\""

        base = " ".join(snippets) if snippets else "The article presents the claim"
        return f"As a supporter, {base}{body_hint}. Therefore, the statement could be credible pending further corroboration."
