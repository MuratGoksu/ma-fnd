"""
Preprocessing Agent (PP-A)
Görev: Veri normalizasyonu ve temizlik
"""
import re
import unicodedata
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from .textual_agent import TextualAgent


class PreprocessingAgent(BaseAgent):
    """
    Preprocessing Agent - Veri normalizasyonu ve temizlik
    Mevcut TextualAgent'ı genişletir
    """
    
    def __init__(self):
        super().__init__("PP-A")
        self.textual_agent = TextualAgent()
        self.processed_items: List[str] = []  # Duplicate detection için
        # Limit cache size to prevent memory issues
        self.max_cache_size = 100
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ana işleme metodu"""
        # Duplicate kontrolü
        if self._is_duplicate(data):
            return {
                "status": "duplicate",
                "original_data": data
            }
        
        # Dil tespiti
        language = self._detect_language(data)
        
        # Metin temizliği
        cleaned = self.textual_agent.clean_text(data)
        
        # Spam/bot içerik filtreleme
        is_spam = self._detect_spam(cleaned)
        if is_spam:
            return {
                "status": "spam",
                "original_data": data
            }
        
        # Normalizasyon
        normalized = self._normalize(cleaned, language)
        
        # Görsel kalite değerlendirmesi (varsa)
        image_quality = None
        if "image_url" in data or "image" in data:
            image_quality = self._assess_image_quality(data)
        
        result = {
            "status": "processed",
            "cleaned_data": normalized,
            "language": language,
            "is_spam": False,
            "image_quality": image_quality,
            "processing_timestamp": self._get_timestamp()
        }
        
        # Mesaj gönder
        self.send_message(
            message_type="analysis",
            content={
                "type": "preprocessing_complete",
                "data": result
            },
            target_agents=["VVA", "TCA", "STA"]
        )
        
        # Duplicate listesine ekle (limited cache)
        item_id = data.get("id", "")
        if item_id:
            self.processed_items.append(item_id)
            # Limit cache size
            if len(self.processed_items) > self.max_cache_size:
                self.processed_items = self.processed_items[-self.max_cache_size:]
        
        return result
    
    def _is_duplicate(self, item: Dict[str, Any]) -> bool:
        """Duplicate detection - Very lenient to allow re-analysis"""
        # DISABLED: Allow re-analysis of same URLs
        # Users may want to re-analyze the same URL to see updated results
        # or verify consistency
        return False
        
        # Old code (disabled):
        # item_id = item.get("id", "")
        # if item_id in self.processed_items[-10:]:
        #     return True
        # return False
    
    def _detect_language(self, item: Dict[str, Any]) -> str:
        """Dil tespiti (basit implementasyon)"""
        text = (item.get("text", "") + " " + item.get("headline", "")).lower()
        
        # Türkçe karakterler
        turkish_chars = set("çğıöşü")
        # İngilizce yaygın kelimeler
        english_words = {"the", "and", "is", "are", "was", "were", "this", "that"}
        
        text_chars = set(text)
        has_turkish = bool(turkish_chars & text_chars)
        has_english = any(word in text for word in english_words)
        
        if has_turkish:
            return "tr"
        elif has_english:
            return "en"
        else:
            return "unknown"
    
    def _detect_spam(self, item: Dict[str, Any]) -> bool:
        """Spam/bot içerik tespiti"""
        text = item.get("text", "").lower()
        headline = item.get("headline", "").lower()
        
        # Spam göstergeleri
        spam_indicators = [
            len(text) < 50,  # Çok kısa içerik
            text.count("!") > 5,  # Aşırı ünlem
            text.count("http") > 3,  # Çok fazla link
            "click here" in text or "click here" in headline,
            "free money" in text or "free money" in headline,
            len(set(text.split())) < 10,  # Çok az unique kelime
        ]
        
        return any(spam_indicators)
    
    def _normalize(self, item: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Metin normalizasyonu"""
        # Fact-check bilgisini koru (önemli!)
        fact_check = item.get("fact_check")
        
        # Unicode normalizasyonu
        if "text" in item:
            item["text"] = unicodedata.normalize("NFKC", item["text"])
        if "headline" in item:
            item["headline"] = unicodedata.normalize("NFKC", item["headline"])
        
        # Fazla boşlukları temizle
        if "text" in item:
            item["text"] = re.sub(r"\s+", " ", item["text"]).strip()
        if "headline" in item:
            item["headline"] = re.sub(r"\s+", " ", item["headline"]).strip()
        
        # Dil bilgisini ekle
        item["detected_language"] = language
        
        # Fact-check bilgisini geri ekle
        if fact_check:
            item["fact_check"] = fact_check
        
        return item
    
    def _assess_image_quality(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Görsel kalite değerlendirmesi (basit)"""
        # Gerçek uygulamada OpenCV kullanılır
        return {
            "has_image": True,
            "quality_score": 0.7,  # Placeholder
            "is_manipulated": False,  # Placeholder
            "note": "Full image analysis requires VVA"
        }
    
    def _get_timestamp(self) -> str:
        """Timestamp oluştur"""
        from datetime import datetime
        return datetime.utcnow().isoformat()

