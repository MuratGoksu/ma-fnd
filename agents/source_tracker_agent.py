"""
Source Tracker Agent (STA)
Görev: Kaynak analizi ve takibi
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from urllib.parse import urlparse
from .base_agent import BaseAgent


class SourceTrackerAgent(BaseAgent):
    """
    Source Tracker Agent - Kaynak analizi ve takibi
    Graph database entegrasyonu için hazır
    """
    
    def __init__(self):
        super().__init__("STA")
        self.source_credibility_db: Dict[str, float] = {}
        self.publication_timeline: List[Dict[str, Any]] = []
        self.source_relationships: Dict[str, List[str]] = {}
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ana işleme metodu"""
        source_info = self.analyze_source(data)
        timeline_entry = self.track_publication(data)
        relationships = self.map_relationships(data)
        
        result = {
            "source_info": source_info,
            "timeline": timeline_entry,
            "relationships": relationships,
            "authority_score": self.calculate_authority_score(source_info)
        }
        
        # Mesaj gönder
        self.send_message(
            message_type="analysis",
            content={
                "type": "source_analysis",
                "data": result
            },
            target_agents=["PP-A", "TCA", "JA"]
        )
        
        return result
    
    def analyze_source(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Kaynak analizi"""
        link = item.get("link") or item.get("id", "")
        domain = self._extract_domain(link)
        
        # Kaynak güvenilirlik skoru (0-1)
        credibility = self._get_credibility_score(domain)
        
        # Kaynak tipi tespiti
        source_type = self._classify_source_type(domain)
        
        return {
            "domain": domain,
            "url": link,
            "credibility_score": credibility,
            "source_type": source_type,
            "is_verified": credibility > 0.7,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    def track_publication(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Yayın zaman çizelgesi takibi"""
        entry = {
            "id": item.get("id", ""),
            "domain": self._extract_domain(item.get("link", "")),
            "headline": item.get("headline", ""),
            "timestamp": datetime.utcnow().isoformat(),
            "first_seen": datetime.utcnow().isoformat()
        }
        
        self.publication_timeline.append(entry)
        return entry
    
    def map_relationships(self, item: Dict[str, Any]) -> Dict[str, List[str]]:
        """Kaynak ilişkilerini haritalama"""
        domain = self._extract_domain(item.get("link", ""))
        
        # Benzer kaynakları bul (basit implementasyon)
        related_sources = self._find_related_sources(domain)
        
        if domain not in self.source_relationships:
            self.source_relationships[domain] = []
        
        self.source_relationships[domain].extend(related_sources)
        
        return {
            "primary_source": domain,
            "related_sources": list(set(related_sources)),
            "propagation_pattern": "initial"  # initial, viral, limited
        }
    
    def calculate_authority_score(self, source_info: Dict[str, Any]) -> float:
        """Kaynak otorite skoru hesaplama"""
        credibility = source_info.get("credibility_score", 0.5)
        source_type = source_info.get("source_type", "unknown")
        
        # Kaynak tipine göre ağırlıklandırma
        type_weights = {
            "news_agency": 1.0,
            "established_media": 0.9,
            "blog": 0.5,
            "social_media": 0.3,
            "unknown": 0.4
        }
        
        weight = type_weights.get(source_type, 0.5)
        authority = credibility * weight
        
        return min(1.0, max(0.0, authority))
    
    def _extract_domain(self, url: str) -> str:
        """URL'den domain çıkar"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # www. önekini kaldır
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return ""
    
    def _get_credibility_score(self, domain: str) -> float:
        """Kaynak güvenilirlik skoru - trust_sites.json kullanır"""
        if domain in self.source_credibility_db:
            return self.source_credibility_db[domain]
        
        # trust_sites.json'dan yükle
        try:
            import json
            import os
            config_path = os.path.join(os.path.dirname(__file__), "..", "config", "trust_sites.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    trust_config = json.load(f)
                    trusted_sites = trust_config.get("trusted", {})
                    
                    # Tam eşleşme
                    if domain in trusted_sites:
                        score = trusted_sites[domain] / 3.0  # 0-3 arası skoru 0-1'e çevir
                        self.source_credibility_db[domain] = score
                        return score
                    
                    # Kısmi eşleşme (domain içinde)
                    for trusted_domain, trust_level in trusted_sites.items():
                        if trusted_domain in domain or domain in trusted_domain:
                            score = trust_level / 3.0
                            self.source_credibility_db[domain] = score
                            return score
        except Exception:
            pass
        
        # Bilinen güvenilir kaynaklar (fallback)
        trusted_domains = {
            "bbc.com": 0.95, "bbc.co.uk": 0.95,
            "reuters.com": 0.95,
            "ap.org": 0.95, "apnews.com": 0.95,
            "nasa.gov": 0.95,
            "nytimes.com": 0.90,
            "theguardian.com": 0.90,
            "washingtonpost.com": 0.90,
            "hurriyet.com.tr": 0.75,  # Türk medyası için orta-yüksek güven
            "milliyet.com.tr": 0.75,
            "ntv.com.tr": 0.75,
            "aa.com.tr": 0.85,
            "trthaber.com": 0.80,
        }
        
        # Kısmi eşleşme kontrolü
        for trusted, score in trusted_domains.items():
            if trusted in domain or domain in trusted:
                self.source_credibility_db[domain] = score
                return score
        
        # Varsayılan skor - bilinmeyen kaynaklar için daha yüksek (gerçek haberler için)
        default_score = 0.65  # 0.5'ten 0.65'e çıkarıldı
        self.source_credibility_db[domain] = default_score
        return default_score
    
    def _classify_source_type(self, domain: str) -> str:
        """Kaynak tipini sınıflandır"""
        if not domain:
            return "unknown"
        
        # Basit kurallar (gerçek uygulamada ML modeli kullanılabilir)
        if any(x in domain for x in [".gov", ".edu", ".org"]):
            return "established_media"
        elif any(x in domain for x in ["news", "media", "press"]):
            return "news_agency"
        elif any(x in domain for x in ["blog", "medium", "substack"]):
            return "blog"
        elif any(x in domain for x in ["twitter", "facebook", "instagram"]):
            return "social_media"
        else:
            return "unknown"
    
    def _find_related_sources(self, domain: str) -> List[str]:
        """İlişkili kaynakları bul"""
        # Basit implementasyon - gerçek uygulamada graph database kullanılır
        related = []
        for other_domain in self.source_relationships.keys():
            if other_domain != domain:
                # Aynı kategorideki kaynaklar
                if self._classify_source_type(domain) == self._classify_source_type(other_domain):
                    related.append(other_domain)
        return related[:5]  # En fazla 5 ilişkili kaynak

