# Hızlı Başlangıç Kılavuzu

## Python ile Çalıştırma

### 1. Gereksinimleri Yükleyin

```bash
cd ma-fnd
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Basit Kullanım

#### Yöntem 1: Örnek Script ile

```bash
python run_example.py
```

Bu script 4 farklı kullanım örneği gösterir.

#### Yöntem 2: Python Kodunda Doğrudan Kullanım

```python
from orchestrator import Orchestrator

# Orchestrator'ı başlat
orchestrator = Orchestrator()

# Haber öğesi oluştur
news_item = {
    "id": "001",
    "headline": "Haber başlığı",
    "text": "Haber metni buraya gelir...",
    "link": "https://example.com/haber"
}

# Analiz et
result = orchestrator.process_news_item(news_item)

# Sonuçları göster
print(f"Verdict: {result['verdict']}")
print(f"Confidence: {result['confidence']}")
print(f"İşlem Süresi: {result['processing_time']} saniye")
```

#### Yöntem 3: Legacy CLI ile (Eski Sistem Uyumluluğu)

```bash
# Mock haber ile
python main.py --source mock

# RSS feed ile
python main.py --source rss --input "https://example.com/feed.xml"

# URL ile
python main.py --source url --input "https://example.com/article"

# JSON dosyası ile
python main.py --source file --input data/news.json

# LLM Judge ile
python main.py --source mock --judge llm --model gpt-4o-mini
```

### 3. API ile Çalıştırma

```bash
# API'yi başlat
python api.py

# Başka bir terminalde test et
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "headline": "Test haber başlığı",
    "text": "Test haber metni"
  }'
```

### 4. Docker ile Çalıştırma

```bash
# Tüm servisleri başlat (PostgreSQL, Neo4j, Redis, API)
docker-compose up -d

# API'ye eriş
curl http://localhost:8000/health
```

## Örnek Senaryolar

### Senaryo 1: Basit Haber Analizi

```python
from orchestrator import Orchestrator

orchestrator = Orchestrator()

item = {
    "headline": "Bilim insanları yeni keşif yaptı",
    "text": "Araştırmacılar önemli bir bulgu açıkladı...",
    "link": "https://haber.com/makale"
}

result = orchestrator.process_news_item(item)
print(result['verdict'])  # REAL, FAKE, veya UNSURE
```

### Senaryo 2: Görsel İçeren Haber

```python
item = {
    "headline": "Fotoğrafla kanıtlanan olay",
    "text": "Görselde görüldüğü gibi...",
    "image_url": "https://example.com/image.jpg"
}

result = orchestrator.process_news_item(item)
# Görsel analizi otomatik yapılır
```

### Senaryo 3: Detaylı Sonuçları İnceleme

```python
result = orchestrator.process_news_item(item)

# Tüm fazların sonuçları
phases = result['phases']

# Kaynak analizi
source_info = phases['source_tracking']['source_info']
print(f"Kaynak güvenilirlik: {source_info['credibility_score']}")

# Metin analizi
textual = phases['textual_analysis']
print(f"Metin güven skoru: {textual['overall_confidence']}")

# Judge kararı
judge = phases['judge_decision']['decision']
print(f"Karar: {judge['verdict']}")
print(f"Güven: {judge['confidence']}")

# Meta değerlendirme
meta = phases['meta_evaluation']['meta_evaluation']
print(f"Öneri: {meta['recommendation']}")  # accept, review, reject
```

### Senaryo 4: Toplu İşleme

```python
news_items = [
    {"headline": "Haber 1", "text": "..."},
    {"headline": "Haber 2", "text": "..."},
    {"headline": "Haber 3", "text": "..."}
]

results = []
for item in news_items:
    result = orchestrator.process_news_item(item)
    results.append(result)

# İstatistikler
stats = orchestrator.get_pipeline_statistics()
print(f"Toplam işlenen: {stats['total_processed']}")
print(f"Verdict dağılımı: {stats['verdict_distribution']}")
```

## Sorun Giderme

### Import Hatası

```bash
# Proje dizininde olduğunuzdan emin olun
cd ma-fnd

# Virtual environment aktif mi kontrol edin
which python  # .venv/bin/python göstermeli

# Gerekirse yeniden yükleyin
pip install -r requirements.txt
```

### OpenAI API Hatası

`.env` dosyası oluşturun:
```bash
cp .env.example .env
# .env dosyasını düzenleyip OPENAI_API_KEY ekleyin
```

### Database Bağlantı Hatası

Database'ler opsiyoneldir. Sistem database olmadan da çalışır, sadece sonuçlar kaydedilmez.

## Daha Fazla Bilgi

- Detaylı dokümantasyon: `README.md`
- API dokümantasyonu: `http://localhost:8000/docs` (API çalışırken)
- Örnek kodlar: `run_example.py`

