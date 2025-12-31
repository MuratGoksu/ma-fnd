# Web Arayüzü Kullanım Kılavuzu

## Özellikler

### 1. Haber Analizi
- Haber URL'sini girerek analiz yapabilirsiniz
- Sistem otomatik olarak içeriği çeker ve analiz eder
- Gerçek haber ise: "✅ Bu gerçek bir haberdir" mesajı gösterilir
- Sahte haber ise: 7 kategori altında detaylı skorlama yapılır

### 2. Sahte Haber Kategorileri

Sistem sahte haberleri 7 alt kategoride değerlendirir:

1. **Dezenformasyon** - Kasıtlı yanlış bilgi yayma
2. **Mezenformasyon** - Yanlış ama kasıtsız bilgi
3. **Propaganda** - Tek taraflı, manipülatif içerik
4. **Şaka/Gırgır** - Mizahi ama yanıltıcı içerik
5. **Hiciv** - Parodi ve alay içerik
6. **Tıklama Yemi** - Abartılı başlık, içerik uyumsuzluğu
7. **Çerçöp Haber** - Düşük kaliteli, güvenilmez içerik

Her kategori için 0-100 arası skor gösterilir ve yatay çubuk grafikle görselleştirilir.

### 3. En Son Kontrol Edilen Haberler
- Kontrol çubuğunun altında en son 5 haber gösterilir
- Her haber için başlık, verdict ve zaman bilgisi görüntülenir

### 4. Bu Hafta En Çok Kontrol Edilen Haberler
- Sistemin alt kısmında bu hafta en çok kontrol edilen haberler listelenir
- Her haber için kontrol sayısı gösterilir

## Kullanım

### API'yi Başlat
```bash
python api.py
```

### Web Arayüzüne Eriş
Tarayıcınızda şu adrese gidin:
```
http://localhost:8000
```

### Analiz Yap
1. Haber URL'sini input alanına yapıştırın
2. "Analiz Et" butonuna tıklayın
3. Sonuçları bekleyin (birkaç saniye sürebilir)
4. Sonuçları görüntüleyin

## API Endpoint'leri

### POST /analyze-url
Haber URL'sinden analiz yapar.

**Request:**
```json
{
  "url": "https://example.com/news/article"
}
```

**Response:**
```json
{
  "verdict": "FAKE",
  "is_fake": true,
  "categories": {
    "dezenformasyon": 45.0,
    "mezenformasyon": 30.0,
    "propaganda": 60.0,
    ...
  },
  "primary_category": "propaganda",
  "overall_score": 45.0
}
```

### GET /recent-checks
En son kontrol edilen haberleri döner.

**Response:**
```json
{
  "checks": [
    {
      "headline": "Haber başlığı",
      "verdict": "FAKE",
      "timestamp": "2024-01-01T12:00:00"
    }
  ]
}
```

### GET /weekly-top
Bu hafta en çok kontrol edilen haberleri döner.

**Response:**
```json
{
  "top_urls": [
    {
      "url": "https://...",
      "headline": "Haber başlığı",
      "count": 15,
      "verdict": "FAKE"
    }
  ]
}
```

## Teknik Detaylar

- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Backend**: FastAPI (Python)
- **Storage**: JSON dosyası tabanlı (logs/news_checks.json)
- **Grafik**: CSS tabanlı yatay çubuk grafikler

## Notlar

- İlk analiz biraz uzun sürebilir (model yükleme)
- URL'ler geçerli haber sitelerinden olmalı
- Storage dosyası otomatik oluşturulur (logs/news_checks.json)
- Son 1000 kontrol kaydedilir (eski kayıtlar otomatik silinir)

