#!/usr/bin/env python3
"""
En basit test scripti - Hızlı başlangıç için
"""
from orchestrator import Orchestrator

def main():
    print("🚀 Multi-Agent Fake News Detection Sistemi")
    print("-" * 50)
    
    # Orchestrator başlat
    orchestrator = Orchestrator()
    
    # Test haber öğesi
    test_news = {
        "id": "test-001",
        "headline": "NASA confirms aliens landed on Mars",
        "text": "NASA has announced that extraterrestrial structures are visible in recent Mars images.",
        "link": "https://example.com/test"
    }
    
    print(f"\n📰 Analiz ediliyor: {test_news['headline']}\n")
    
    # Analiz et
    result = orchestrator.process_news_item(test_news)
    
    # Sonuçları göster
    print("\n" + "=" * 50)
    print("✅ SONUÇLAR")
    print("=" * 50)
    print(f"Verdict: {result['verdict']}")
    print(f"Confidence: {result['confidence']:.1%}")
    print(f"İşlem Süresi: {result['processing_time']:.2f} saniye")
    print("=" * 50)
    
    return result

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        import traceback
        traceback.print_exc()

