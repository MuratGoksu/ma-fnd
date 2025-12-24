class CrawlerAgent:
    """Deterministik mock crawler (ağ erişimi yok)."""
    def fetch_news(self) -> dict:
        return {
            "id": "001",
            "headline": "NASA confirms aliens landed on Mars.",
            "text": (
                "NASA has announced extraterrestrial structures are visible "
                "in recent Mars images, confirming alien presence."
            ),
        }
