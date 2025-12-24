# X (Twitter) Entegrasyonu Kurulumu

## Twitter API Credentials Alma

### 1. Twitter Developer Portal'a Git
1. https://developer.twitter.com adresine git
2. Twitter hesabınla giriş yap
3. "Developer Portal"a git

### 2. Yeni App Oluştur
1. "Projects & Apps" > "Create Project"
2. Proje adı ve kullanım amacını belirt
3. App oluştur

### 3. API Keys ve Tokens Al

#### Yöntem 1: Bearer Token (Önerilen - Daha Basit)
1. App'in "Keys and Tokens" sekmesine git
2. "Bearer Token" bölümünden token'ı kopyala
3. `.env` dosyasına ekle:
   ```
   TWITTER_BEARER_TOKEN=your_bearer_token_here
   ```

#### Yöntem 2: OAuth 1.0a (Tam Erişim)
1. "API Key and Secret" oluştur
2. "Access Token and Secret" oluştur
3. `.env` dosyasına ekle:
   ```
   TWITTER_API_KEY=your_api_key
   TWITTER_API_SECRET=your_api_secret
   TWITTER_ACCESS_TOKEN=your_access_token
   TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
   ```

## Kullanım

### CLI ile:

#### Belirli bir tweet'i analiz et:
```bash
python main.py --source twitter --input "1234567890123456789"
# veya tweet URL'i:
python main.py --source twitter --input "https://twitter.com/username/status/1234567890123456789"
```

#### Kullanıcının son tweet'ini analiz et:
```bash
python main.py --source twitter --input "@username"
```

#### Tweet araması yap:
```bash
python main.py --source twitter --input "fake news"
```

### Python ile:

```python
from agents import TwitterCrawlerAgent
from orchestrator import Orchestrator

# Twitter'dan tweet çek
crawler = TwitterCrawlerAgent()

# Yöntem 1: Tweet ID ile
tweet = crawler.fetch_news(tweet_id="1234567890123456789")

# Yöntem 2: Kullanıcı adı ile
tweet = crawler.fetch_news(username="username")

# Yöntem 3: Arama ile
tweet = crawler.fetch_news(query="fake news")

# Analiz et
orchestrator = Orchestrator()
result = orchestrator.process_news_item(tweet)
print(f"Verdict: {result['verdict']}")
```

## Notlar

- **Rate Limits**: Twitter API'nin rate limit'leri var. Çok fazla istek yaparsan beklemen gerekebilir.
- **Bearer Token**: Sadece okuma işlemleri için yeterli (tweet okuma, arama)
- **OAuth 1.0a**: Tam erişim için gerekli (tweet gönderme, beğeni, vb.)
- **API v2**: Sistem Twitter API v2 kullanıyor (daha modern ve güçlü)

## Sorun Giderme

### "tweepy is required" hatası:
```bash
pip install tweepy
```

### "Twitter API credentials not found" hatası:
- `.env` dosyasında credentials'ların doğru olduğundan emin ol
- Bearer Token VEYA OAuth credentials'larından birini kullan

### "Rate limit exceeded" hatası:
- Bir süre bekle (15 dakika genellikle yeterli)
- Daha az istek yap

### "User not found" hatası:
- Kullanıcı adının doğru olduğundan emin ol
- @ işareti olmadan kullanıcı adını gir

