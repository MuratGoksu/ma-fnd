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
        if headline:
            concerns.append(f"the headline '{headline}' may be sensational")
        if text and len(text) < 200:
            concerns.append("the body text is very short and lacks details")
        if text and not re.search(r"\b(source|report|official|data|study|evidence)\b", text, re.I):
            concerns.append("there is no explicit evidence or official source cited")

        prefix = "As a skeptic, "
        if concerns:
            return prefix + "; ".join(concerns) + ". I would look for corroboration from multiple reputable outlets."
        return prefix + "key details and corroborating sources are unclear. Independent verification is required."
