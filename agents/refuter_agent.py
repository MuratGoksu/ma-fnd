"""
Refuter Agent (RA)
Görev: İtirazlara karşı savunma
"""
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent


class RefuterAgent(BaseAgent):
    """
    Refuter Agent - İtirazlara karşı savunma
    Dialectical argumentation için
    """
    
    def __init__(self):
        super().__init__("RA")
        self.argument_history: List[Dict[str, Any]] = []
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ana işleme metodu"""
        claim_argument = data.get("claim_argument", "")
        challenge_argument = data.get("challenge_argument", "")
        original_item = data.get("item", {})
        
        # İtirazlara karşı savunma
        refutation = self.generate_refutation(
            claim_argument,
            challenge_argument,
            original_item
        )
        
        result = {
            "status": "refuted",
            "refutation": refutation,
            "confidence": refutation.get("confidence", 0.5)
        }
        
        # Mesaj gönder
        self.send_message(
            message_type="argument",
            content={
                "type": "refutation",
                "data": result
            },
            target_agents=["CA", "CHA", "JA"]
        )
        
        return result
    
    def generate_refutation(
        self,
        claim_arg: str,
        challenge_arg: str,
        item: Dict[str, Any]
    ) -> Dict[str, Any]:
        """İtirazlara karşı savunma argümanı oluştur"""
        
        # Challenge argümanındaki zayıf noktaları tespit et
        weaknesses = self._identify_weaknesses(challenge_arg)
        
        # Mantıksal hataları tespit et
        fallacies = self._detect_fallacies(challenge_arg)
        
        # Kanıt önceliklendirme
        evidence_ranking = self._rank_evidence(item, claim_arg)
        
        # Karşı-karşı argüman oluştur
        counter_argument = self._build_counter_argument(
            claim_arg,
            challenge_arg,
            weaknesses,
            fallacies,
            evidence_ranking
        )
        
        # Güven skoru
        confidence = self._calculate_refutation_confidence(
            weaknesses,
            fallacies,
            evidence_ranking
        )
        
        return {
            "counter_argument": counter_argument,
            "identified_weaknesses": weaknesses,
            "detected_fallacies": fallacies,
            "evidence_ranking": evidence_ranking,
            "confidence": confidence,
            "supports_claim": True
        }
    
    def _identify_weaknesses(self, challenge_arg: str) -> List[str]:
        """Challenge argümanındaki zayıf noktaları tespit et"""
        weaknesses = []
        challenge_lower = challenge_arg.lower()
        
        # Zayıflık göstergeleri
        weak_indicators = {
            "speculation": ["might", "could", "possibly", "perhaps", "maybe"],
            "lack_of_evidence": ["no proof", "unverified", "unconfirmed"],
            "ad_hominem": ["fake", "liar", "fraud"],
            "emotional_appeal": ["scary", "terrifying", "shocking"]
        }
        
        for weakness_type, keywords in weak_indicators.items():
            if any(keyword in challenge_lower for keyword in keywords):
                weaknesses.append(weakness_type)
        
        return weaknesses
    
    def _detect_fallacies(self, challenge_arg: str) -> List[Dict[str, str]]:
        """Mantıksal hataları tespit et"""
        fallacies = []
        challenge_lower = challenge_arg.lower()
        
        # Mantıksal hata pattern'leri
        fallacy_patterns = {
            "strawman": ["misrepresents", "distorts", "twists"],
            "false_dilemma": ["either", "or else", "only two options"],
            "slippery_slope": ["will lead to", "inevitably cause"],
            "appeal_to_emotion": ["fear", "anger", "outrage"],
            "ad_hominem": ["liar", "fraud", "fake"]
        }
        
        for fallacy_type, keywords in fallacy_patterns.items():
            if any(keyword in challenge_lower for keyword in keywords):
                fallacies.append({
                    "type": fallacy_type,
                    "description": f"Detected {fallacy_type} fallacy"
                })
        
        return fallacies
    
    def _rank_evidence(
        self,
        item: Dict[str, Any],
        claim_arg: str
    ) -> List[Dict[str, Any]]:
        """Kanıt önceliklendirme"""
        evidence = []
        
        # Kaynak kanıtı
        if item.get("link"):
            evidence.append({
                "type": "source",
                "content": item.get("link"),
                "weight": 0.3,
                "reliability": "medium"
            })
        
        # Metin kanıtı
        if item.get("text"):
            evidence.append({
                "type": "text_content",
                "content": item.get("text")[:200],
                "weight": 0.4,
                "reliability": "medium"
            })
        
        # Headline kanıtı
        if item.get("headline"):
            evidence.append({
                "type": "headline",
                "content": item.get("headline"),
                "weight": 0.3,
                "reliability": "high"
            })
        
        # Ağırlığa göre sırala
        evidence.sort(key=lambda x: x["weight"], reverse=True)
        
        return evidence
    
    def _build_counter_argument(
        self,
        claim_arg: str,
        challenge_arg: str,
        weaknesses: List[str],
        fallacies: List[Dict[str, str]],
        evidence_ranking: List[Dict[str, Any]]
    ) -> str:
        """Karşı-karşı argüman oluştur"""
        parts = []
        
        # Claim argümanını destekle
        parts.append(f"The original claim argument: '{claim_arg[:100]}...'")
        
        # Zayıf noktaları belirt
        if weaknesses:
            parts.append(f"The challenge argument has weaknesses: {', '.join(weaknesses)}")
        
        # Mantıksal hataları belirt
        if fallacies:
            fallacy_types = [f["type"] for f in fallacies]
            parts.append(f"Detected logical fallacies: {', '.join(fallacy_types)}")
        
        # Kanıtları vurgula
        if evidence_ranking:
            top_evidence = evidence_ranking[0]
            parts.append(f"Strong evidence supports the claim: {top_evidence['type']}")
        
        # Sonuç
        parts.append("Therefore, the original claim remains credible despite the challenges.")
        
        return " ".join(parts)
    
    def _calculate_refutation_confidence(
        self,
        weaknesses: List[str],
        fallacies: List[Dict[str, str]],
        evidence_ranking: List[Dict[str, Any]]
    ) -> float:
        """Refutation güven skoru"""
        base_confidence = 0.5
        
        # Zayıf nokta bonusu
        weakness_bonus = len(weaknesses) * 0.1
        
        # Mantıksal hata bonusu
        fallacy_bonus = len(fallacies) * 0.15
        
        # Kanıt bonusu
        evidence_bonus = len(evidence_ranking) * 0.05
        
        confidence = base_confidence + weakness_bonus + fallacy_bonus + evidence_bonus
        return min(1.0, max(0.0, confidence))

