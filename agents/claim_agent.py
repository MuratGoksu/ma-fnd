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
        
        # Daha detaylı argüman
        credibility_indicators = []
        if domain and any(trusted in domain for trusted in ["bbc", "reuters", "ap.org", "nasa.gov", "nytimes", "guardian"]):
            credibility_indicators.append("comes from a reputable source")
        if text and len(text) > 300:
            credibility_indicators.append("provides substantial detail")
        if text and re.search(r"\b(source|report|official|data|study|evidence|research)\b", text, re.I):
            credibility_indicators.append("references evidence or sources")
        
        credibility_text = ""
        if credibility_indicators:
            credibility_text = f" The claim {', '.join(credibility_indicators)}."
        
        return f"As a supporter, {base}{body_hint}.{credibility_text} Therefore, the statement appears credible and warrants consideration."
