import re, unicodedata

class TextualAgent:
    def clean_text(self, item: dict) -> dict:
        text = unicodedata.normalize("NFKC", item.get("text", ""))
        item["text"] = re.sub(r"\s+", " ", text).strip()
        return item
