# Fact-Check Test Rehberi

## Test URL'leri

### PolitiFact - False (Sahte)
```
https://www.politifact.com/factchecks/2025/nov/17/tiktok-posts/Donald-Trump-Bill-Clinton-Bubba-touch-crotch-video/
```
**Beklenen:** FAKE, %95 confidence

### Test Adımları

1. Web arayüzünde URL'yi girin
2. "Analiz Et" butonuna tıklayın
3. Kontrol edin:
   - Fact-check badge görünüyor mu?
   - Verdict: FAKE mi?
   - Confidence: %95 civarı mı?
   - Tüm 7 kategori gösteriliyor mu?
   - Renkler: Kırmızı tonları mı?

## Sorun Giderme

### Eğer hala %50 skor veriyorsa:

1. **Fact-check algılanmıyor olabilir**
   - API loglarını kontrol edin: `tail -f /tmp/api.log`
   - "Fact-check detected" mesajını arayın

2. **Rating çıkarılamıyor olabilir**
   - HTML yapısı değişmiş olabilir
   - Fact-check detector'ı güncellemek gerekebilir

3. **Preprocessing fact-check'i siliyor olabilir**
   - `agents/preprocessing_agent.py` dosyasında fact_check korunuyor mu kontrol edin

## Manuel Test

```python
from agents.url_crawler_agent import URLCrawlerAgent

crawler = URLCrawlerAgent()
url = "https://www.politifact.com/factchecks/2025/nov/17/tiktok-posts/Donald-Trump-Bill-Clinton-Bubba-touch-crotch-video/"
result = crawler.fetch_news(url)
print("Fact-check:", result.get("fact_check"))
```

