"""
Textual Context Agent (TCA)
Görev: Metinsel analiz
"""
from typing import Dict, Any, List, Optional
import re
from .base_agent import BaseAgent


class TextualContextAgent(BaseAgent):
    """
    Textual Context Agent - Metinsel analiz
    mBERT, XLM-R, NLI modelleri için hazır
    """
    
    def __init__(self):
        super().__init__("TCA")
        self.entity_cache: Dict[str, List[str]] = {}
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ana işleme metodu"""
        text = data.get("text", "")
        headline = data.get("headline", "")
        
        # Metinsel analizler
        analysis = {
            "fact_consistency": self.check_fact_consistency(data),
            "emotional_manipulation": self.detect_emotional_manipulation(data),
            "source_attribution": self.analyze_source_attribution(data),
            "temporal_consistency": self.check_temporal_consistency(data),
            "named_entities": self.extract_named_entities(data),
            "sentiment": self.analyze_sentiment(data),
            "nli_score": self.natural_language_inference(data)
        }
        
        # Genel metin güven skoru
        overall_score = self._calculate_text_confidence(analysis)
        
        result = {
            "status": "analyzed",
            "analysis": analysis,
            "overall_confidence": overall_score,
            "is_suspicious": overall_score < 0.5
        }
        
        # Mesaj gönder
        self.send_message(
            message_type="analysis",
            content={
                "type": "textual_analysis",
                "data": result
            },
            target_agents=["CA", "CHA", "JA"]
        )
        
        return result
    
    def check_fact_consistency(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Gerçek tutarlılık kontrolü"""
        text = item.get("text", "")
        headline = item.get("headline", "")
        
        # Basit heuristikler (gerçek uygulamada NLI modeli kullanılır)
        inconsistencies = []
        
        # Sayısal tutarsızlıklar
        numbers_in_headline = re.findall(r'\d+', headline)
        numbers_in_text = re.findall(r'\d+', text)
        
        if numbers_in_headline and numbers_in_text:
            # Headline ve text'teki sayılar farklı mı?
            headline_nums = set(numbers_in_headline)
            text_nums = set(numbers_in_text)
            if not headline_nums.issubset(text_nums):
                inconsistencies.append("Numeric inconsistency between headline and text")
        
        # Tarih tutarsızlıkları
        dates_in_headline = re.findall(r'\d{4}', headline)
        dates_in_text = re.findall(r'\d{4}', text)
        
        if dates_in_headline and dates_in_text:
            if set(dates_in_headline) != set(dates_in_text):
                inconsistencies.append("Date inconsistency detected")
        
        consistency_score = 1.0 - (len(inconsistencies) * 0.2)
        consistency_score = max(0.0, min(1.0, consistency_score))
        
        return {
            "score": consistency_score,
            "inconsistencies": inconsistencies,
            "is_consistent": len(inconsistencies) == 0
        }
    
    def detect_emotional_manipulation(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Duygusal manipülasyon tespiti"""
        text = (item.get("text", "") + " " + item.get("headline", "")).lower()
        
        # Manipülasyon göstergeleri
        manipulation_indicators = {
            "urgency": ["immediately", "urgent", "breaking", "shocking", "you won't believe"],
            "fear": ["warning", "danger", "threat", "scary", "terrifying"],
            "anger": ["outrage", "furious", "angry", "disgusting"],
            "clickbait": ["this one trick", "doctors hate", "secret", "hidden truth"]
        }
        
        detected_manipulation = []
        manipulation_score = 0.0
        
        for category, keywords in manipulation_indicators.items():
            count = sum(1 for keyword in keywords if keyword in text)
            if count > 0:
                detected_manipulation.append(category)
                manipulation_score += count * 0.1
        
        manipulation_score = min(1.0, manipulation_score)
        
        return {
            "score": manipulation_score,
            "detected_types": detected_manipulation,
            "is_manipulative": manipulation_score > 0.5
        }
    
    def analyze_source_attribution(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Kaynak atıf analizi"""
        text = item.get("text", "")
        
        # Kaynak atıf göstergeleri
        attribution_patterns = [
            r"according to (.+?)",
            r"reported by (.+?)",
            r"source: (.+?)",
            r"(.+?) said",
            r"(.+?) stated",
            r"(.+?) confirmed"
        ]
        
        sources = []
        for pattern in attribution_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            sources.extend(matches)
        
        has_attribution = len(sources) > 0
        attribution_score = min(1.0, len(sources) * 0.3)
        
        return {
            "score": attribution_score,
            "sources_mentioned": list(set(sources)),
            "has_attribution": has_attribution
        }
    
    def check_temporal_consistency(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Zamansal tutarlılık kontrolü"""
        text = item.get("text", "")
        
        # Tarih bulma
        dates = re.findall(r'\d{4}', text)
        years = [int(d) for d in dates if 1900 <= int(d) <= 2100]
        
        if not years:
            return {
                "score": 0.5,
                "is_consistent": True,
                "note": "No dates found"
            }
        
        # Tarih tutarlılığı (gelecek tarihler, mantıksız sıralamalar)
        from datetime import datetime
        current_year = datetime.now().year
        
        inconsistencies = []
        for year in years:
            if year > current_year + 1:  # Gelecek tarih (1 yıl tolerans)
                inconsistencies.append(f"Future date: {year}")
        
        consistency_score = 1.0 - (len(inconsistencies) * 0.3)
        consistency_score = max(0.0, min(1.0, consistency_score))
        
        return {
            "score": consistency_score,
            "is_consistent": len(inconsistencies) == 0,
            "inconsistencies": inconsistencies,
            "years_mentioned": years
        }
    
    def extract_named_entities(self, item: Dict[str, Any]) -> List[Dict[str, str]]:
        """İsimli varlık çıkarımı (NER)"""
        text = item.get("text", "")
        
        # Basit NER (gerçek uygulamada spaCy veya mBERT kullanılır)
        entities = []
        
        # Büyük harfle başlayan kelimeler (basit yaklaşım)
        words = text.split()
        capitalized = [w for w in words if w and w[0].isupper() and len(w) > 2]
        
        # Yaygın entity pattern'leri
        person_pattern = r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b'  # İsim Soyisim
        org_pattern = r'\b([A-Z][A-Z]+)\b'  # Kısaltmalar
        
        persons = re.findall(person_pattern, text)
        orgs = re.findall(org_pattern, text)
        
        for person in persons[:5]:  # İlk 5 kişi
            entities.append({"text": person, "type": "PERSON"})
        
        for org in orgs[:5]:  # İlk 5 organizasyon
            entities.append({"text": org, "type": "ORG"})
        
        return entities
    
    def analyze_sentiment(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Sentiment analizi"""
        text = (item.get("text", "") + " " + item.get("headline", "")).lower()
        
        # Basit sentiment (gerçek uygulamada transformer modeli kullanılır)
        positive_words = ["good", "great", "excellent", "positive", "success", "win", "happy"]
        negative_words = ["bad", "terrible", "negative", "fail", "loss", "sad", "angry"]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        total = positive_count + negative_count
        if total == 0:
            sentiment_score = 0.5  # Neutral
        else:
            sentiment_score = positive_count / total
        
        return {
            "score": sentiment_score,
            "label": "positive" if sentiment_score > 0.6 else "negative" if sentiment_score < 0.4 else "neutral",
            "positive_indicators": positive_count,
            "negative_indicators": negative_count
        }
    
    def natural_language_inference(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Doğal dil çıkarımı (NLI)"""
        headline = item.get("headline", "")
        text = item.get("text", "")
        
        # Basit NLI (gerçek uygulamada mBERT NLI modeli kullanılır)
        # Headline ve text arasındaki ilişkiyi değerlendir
        
        if not headline or not text:
            return {
                "score": 0.5,
                "relationship": "unknown",
                "note": "Insufficient data"
            }
        
        # Ortak kelimeler
        headline_words = set(headline.lower().split())
        text_words = set(text.lower().split())
        common_words = headline_words & text_words
        
        overlap = len(common_words) / max(len(headline_words), 1)
        
        # Yüksek overlap -> entailment (headline text tarafından destekleniyor)
        if overlap > 0.3:
            relationship = "entailment"
            score = min(1.0, overlap * 2)
        else:
            relationship = "contradiction"
            score = 1.0 - overlap
        
        return {
            "score": score,
            "relationship": relationship,
            "overlap": overlap
        }
    
    def _calculate_text_confidence(self, analysis: Dict[str, Any]) -> float:
        """Metin güven skoru hesaplama"""
        weights = {
            "fact_consistency": 0.25,
            "emotional_manipulation": 0.20,
            "source_attribution": 0.15,
            "temporal_consistency": 0.15,
            "nli_score": 0.25
        }
        
        confidence = 0.0
        
        # Fact consistency
        fact_score = analysis["fact_consistency"].get("score", 0.5)
        confidence += fact_score * weights["fact_consistency"]
        
        # Emotional manipulation (ters - manipülasyon varsa skor düşer)
        manip_score = 1.0 - analysis["emotional_manipulation"].get("score", 0.0)
        confidence += manip_score * weights["emotional_manipulation"]
        
        # Source attribution
        attr_score = analysis["source_attribution"].get("score", 0.5)
        confidence += attr_score * weights["source_attribution"]
        
        # Temporal consistency
        temp_score = analysis["temporal_consistency"].get("score", 0.5)
        confidence += temp_score * weights["temporal_consistency"]
        
        # NLI score
        nli_score = analysis["nli_score"].get("score", 0.5)
        confidence += nli_score * weights["nli_score"]
        
        return max(0.0, min(1.0, confidence))

