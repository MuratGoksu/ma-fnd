import re

class ChallengeAgent:
    def generate_argument(self, item: dict) -> str:
        """
        İçerikten türetilen şüpheci argüman üretir.
        Headline/text yoksa önceki şablona düşer.
        """
        headline = item.get("headline") or ""
        text = (item.get("text") or "").strip()

        if not headline and not text:
            return (
                f"As a skeptic, I doubt the headline '{item.get('headline','')}'. "
                "There are no peer-reviewed papers or official NASA press releases supporting it."
            )

        concerns = []
        red_flags = []
        
        # Headline analizi
        if headline:
            headline_lower = headline.lower()
            if any(word in headline_lower for word in ["shocking", "secret", "exposed", "revealed", "breaking"]):
                red_flags.append("uses sensational language typical of clickbait")
            if "!" in headline or headline.isupper():
                red_flags.append("uses excessive punctuation or capitalization")
            if len(headline.split()) > 15:
                concerns.append(f"the headline '{headline}' is unusually long and may be exaggerated")
        
        # İçerik analizi
        if text:
            text_lower = text.lower()
            if len(text) < 200:
                concerns.append("the body text is very short and lacks substantive details")
            if not re.search(r"\b(source|report|official|data|study|evidence|research|according to)\b", text, re.I):
                concerns.append("there is no explicit evidence, official source, or citation provided")
            if re.search(r"\b(allegedly|rumor|unconfirmed|speculation)\b", text_lower, re.I):
                red_flags.append("contains language indicating uncertainty or unverified claims")
            if text.count("!") > 3:
                red_flags.append("uses excessive exclamation marks suggesting emotional manipulation")
        
        prefix = "As a skeptic, "
        all_concerns = concerns + red_flags
        
        if all_concerns:
            return prefix + "; ".join(all_concerns) + ". I would require corroboration from multiple reputable, independent sources before accepting this claim."
        return prefix + "key details, evidence, and corroborating sources are unclear or missing. Independent verification from multiple reputable outlets is required."
