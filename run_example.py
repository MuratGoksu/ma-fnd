"""
Örnek Kullanım: Multi-Agent Fake News Detection Sistemi
Python ile nasıl kullanılacağını gösterir
"""
from orchestrator import Orchestrator


def example_1_basic_usage():
    """Temel kullanım örneği"""
    print("=" * 60)
    print("Örnek 1: Temel Kullanım")
    print("=" * 60)
    
    # Orchestrator'ı başlat
    orchestrator = Orchestrator()
    
    # Örnek haber öğesi
    news_item = {
        "id": "example-001",
        "headline": "NASA confirms aliens landed on Mars",
        "text": (
            "NASA has announced that extraterrestrial structures are visible "
            "in recent Mars images, confirming alien presence on the red planet. "
            "Scientists are amazed by this groundbreaking discovery."
        ),
        "link": "https://example.com/nasa-aliens"
    }
    
    # Haberi analiz et
    print(f"\nAnaliz ediliyor: {news_item['headline']}")
    result = orchestrator.process_news_item(news_item)
    
    # Sonuçları göster
    print(f"\n✅ Analiz Tamamlandı!")
    print(f"Verdict: {result['verdict']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"İşlem Süresi: {result['processing_time']:.2f} saniye")
    
    return result


def example_2_with_image():
    """Görsel içeren haber örneği"""
    print("\n" + "=" * 60)
    print("Örnek 2: Görsel İçeren Haber")
    print("=" * 60)
    
    orchestrator = Orchestrator()
    
    news_item = {
        "id": "example-002",
        "headline": "Breaking: Major scientific discovery",
        "text": "Scientists have made a major breakthrough in quantum computing.",
        "link": "https://example.com/quantum",
        "image_url": "https://example.com/image.jpg"
    }
    
    print(f"\nAnaliz ediliyor: {news_item['headline']}")
    result = orchestrator.process_news_item(news_item)
    
    print(f"\n✅ Analiz Tamamlandı!")
    print(f"Verdict: {result['verdict']}")
    print(f"Confidence: {result['confidence']:.2%}")
    
    # Görsel analiz sonuçları
    if 'visual_analysis' in result.get('phases', {}):
        vis_analysis = result['phases']['visual_analysis']
        print(f"Görsel Analiz: {vis_analysis.get('status', 'N/A')}")
    
    return result


def example_3_detailed_results():
    """Detaylı sonuçları göster"""
    print("\n" + "=" * 60)
    print("Örnek 3: Detaylı Sonuçlar")
    print("=" * 60)
    
    orchestrator = Orchestrator()
    
    news_item = {
        "id": "example-003",
        "headline": "Local news: City council approves new park",
        "text": (
            "The city council has unanimously approved the construction of "
            "a new public park in the downtown area. The project will cost "
            "$2 million and is expected to be completed by next year."
        ),
        "link": "https://localnews.com/park-approval"
    }
    
    result = orchestrator.process_news_item(news_item)
    
    print(f"\n📊 Detaylı Sonuçlar:")
    print(f"  Verdict: {result['verdict']}")
    print(f"  Confidence: {result['confidence']:.2%}")
    
    phases = result.get('phases', {})
    
    # Kaynak analizi
    if 'source_tracking' in phases:
        source = phases['source_tracking']
        print(f"\n📰 Kaynak Analizi:")
        print(f"  Domain: {source.get('source_info', {}).get('domain', 'N/A')}")
        print(f"  Credibility: {source.get('source_info', {}).get('credibility_score', 0):.2%}")
    
    # Metin analizi
    if 'textual_analysis' in phases:
        textual = phases['textual_analysis']
        print(f"\n📝 Metin Analizi:")
        print(f"  Confidence: {textual.get('overall_confidence', 0):.2%}")
        analysis = textual.get('analysis', {})
        if 'fact_consistency' in analysis:
            print(f"  Fact Consistency: {analysis['fact_consistency'].get('score', 0):.2%}")
    
    # Judge kararı
    if 'judge_decision' in phases:
        judge = phases['judge_decision']
        decision = judge.get('decision', {})
        print(f"\n⚖️  Judge Kararı:")
        print(f"  Verdict: {decision.get('verdict', 'N/A')}")
        print(f"  Confidence: {decision.get('confidence', 0):.2%}")
        if 'criteria_scores' in decision:
            print(f"  Kriter Skorları:")
            for criterion, score in decision['criteria_scores'].items():
                print(f"    - {criterion}: {score:.2%}")
    
    # Meta değerlendirme
    if 'meta_evaluation' in phases:
        meta = phases['meta_evaluation']
        eval_data = meta.get('meta_evaluation', {})
        print(f"\n🔍 Meta Değerlendirme:")
        print(f"  Recommendation: {eval_data.get('recommendation', 'N/A')}")
        print(f"  Overall Quality: {eval_data.get('overall_quality', 0):.2%}")
    
    return result


def example_4_statistics():
    """İstatistikleri göster"""
    print("\n" + "=" * 60)
    print("Örnek 4: İstatistikler")
    print("=" * 60)
    
    orchestrator = Orchestrator()
    
    # Birkaç örnek haber işle
    news_items = [
        {
            "id": "stat-001",
            "headline": "First news item",
            "text": "This is the first test news item.",
            "link": "https://example.com/1"
        },
        {
            "id": "stat-002",
            "headline": "Second news item",
            "text": "This is the second test news item.",
            "link": "https://example.com/2"
        }
    ]
    
    for item in news_items:
        orchestrator.process_news_item(item)
    
    # İstatistikleri al
    stats = orchestrator.get_pipeline_statistics()
    
    print(f"\n📈 Pipeline İstatistikleri:")
    print(f"  Toplam İşlenen: {stats['total_processed']}")
    print(f"  Ortalama İşlem Süresi: {stats['average_processing_time']:.2f} saniye")
    
    if 'verdict_distribution' in stats:
        print(f"\n  Verdict Dağılımı:")
        for verdict, count in stats['verdict_distribution'].items():
            print(f"    - {verdict}: {count}")


if __name__ == "__main__":
    print("\n🚀 Multi-Agent Fake News Detection Sistemi")
    print("Python Kullanım Örnekleri\n")
    
    try:
        # Örnek 1: Temel kullanım
        example_1_basic_usage()
        
        # Örnek 2: Görsel içeren haber
        example_2_with_image()
        
        # Örnek 3: Detaylı sonuçlar
        example_3_detailed_results()
        
        # Örnek 4: İstatistikler
        example_4_statistics()
        
        print("\n" + "=" * 60)
        print("✅ Tüm örnekler başarıyla tamamlandı!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Hata oluştu: {e}")
        import traceback
        traceback.print_exc()

