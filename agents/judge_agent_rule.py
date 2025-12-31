"""
Judge Agent (JA) - Rule-based
Görev: Final karar verme
"""
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent


class JudgeAgent(BaseAgent):
    """
    Judge Agent - Final karar verme
    Multi-criteria decision analysis
    """
    
    def __init__(self):
        super().__init__("JA")
        self.decision_history: List[Dict[str, Any]] = []
        
        # Load training adjustments if available
        try:
            from agent_trainer import get_agent_trainer
            trainer = get_agent_trainer()
            adjustments = trainer.get_agent_adjustments("JA")
            
            # Apply threshold adjustments if available
            if adjustments.get("threshold_adjustment") == "increase_sensitivity":
                # Increase sensitivity (lower thresholds for FAKE detection)
                self._threshold_adjustment = "sensitive"
            else:
                self._threshold_adjustment = "normal"
        except Exception:
            self._threshold_adjustment = "normal"
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ana işleme metodu"""
        # Tüm analiz sonuçlarını topla
        claim_arg = data.get("claim_argument", "")
        challenge_arg = data.get("challenge_argument", "")
        refutation = data.get("refutation", {})
        visual_analysis = data.get("visual_analysis", {})
        textual_analysis = data.get("textual_analysis", {})
        source_analysis = data.get("source_analysis", {})
        item = data.get("item", {})
        
        # Karar verme
        decision = self.evaluate(
            claim_arg=claim_arg,
            challenge_arg=challenge_arg,
            refutation=refutation,
            visual_analysis=visual_analysis,
            textual_analysis=textual_analysis,
            source_analysis=source_analysis,
            item=item
        )
        
        result = {
            "status": "decided",
            "decision": decision,
            "verdict": decision.get("verdict", "UNSURE"),
            "confidence": decision.get("confidence", 0.5)
        }
        
        # Mesaj gönder
        self.send_message(
            message_type="decision",
            content={
                "type": "judgment",
                "data": result
            },
            target_agents=["MEA", "COA"]
        )
        
        # Geçmişe ekle
        self.decision_history.append(result)
        
        return result
    
    def evaluate(
        self,
        claim_arg: str = "",
        challenge_arg: str = "",
        refutation: Dict[str, Any] = None,
        visual_analysis: Dict[str, Any] = None,
        textual_analysis: Dict[str, Any] = None,
        source_analysis: Dict[str, Any] = None,
        item: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Multi-criteria decision analysis
        Eski API uyumluluğu için item parametresi de alır
        """
        if item is None:
            item = {}
        
        # FACT-CHECK SONUCU VARSA ÖNCELİK VER
        fact_check = item.get("fact_check")
        if fact_check and fact_check.get("is_fact_check"):
            verdict = fact_check.get("verdict", "UNSURE")
            confidence = fact_check.get("confidence", 0.95)
            rating = fact_check.get("rating", "Unknown")
            site_name = fact_check.get("site_name", "Fact-check site")
            
            return {
                "verdict": verdict,
                "confidence": confidence,
                "fact_check_used": True,
                "fact_check_site": site_name,
                "fact_check_rating": rating,
                "rationale": f"Fact-checked by {site_name} as {rating}. Verdict: {verdict}",
                "criteria_scores": {
                    "evidence_strength": confidence,
                    "source_credibility": 0.95,  # Fact-check sites are highly credible
                    "argument_quality": confidence,
                    "consistency_score": confidence
                },
                "weights": {
                    "evidence_strength": 0.30,
                    "source_credibility": 0.25,
                    "argument_quality": 0.25,
                    "consistency_score": 0.20
                }
            }
        
        # Kriter skorları
        criteria_scores = {
            "evidence_strength": self._calculate_evidence_strength(
                claim_arg, challenge_arg, refutation
            ),
            "source_credibility": self._calculate_source_credibility(source_analysis),
            "argument_quality": self._calculate_argument_quality(
                claim_arg, challenge_arg, refutation
            ),
            "consistency_score": self._calculate_consistency_score(
                visual_analysis, textual_analysis
            )
        }
        
        # Ağırlıklar
        weights = {
            "evidence_strength": 0.30,
            "source_credibility": 0.25,
            "argument_quality": 0.25,
            "consistency_score": 0.20
        }
        
        # Ağırlıklı ortalama
        weighted_score = sum(
            criteria_scores[key] * weights[key]
            for key in criteria_scores
        )
        
        # Güven aralığı
        confidence_interval = self._calculate_confidence_interval(criteria_scores)
        
        # Karar
        verdict = self._determine_verdict(weighted_score, confidence_interval)
        
        
        result = {
            "verdict": verdict,
            "confidence": weighted_score,
            "confidence_interval": confidence_interval,
            "criteria_scores": criteria_scores,
            "weights": weights,
            "rationale": self._generate_rationale(verdict, criteria_scores)
        }
        
        # Backward compatibility: if called with simple args, return just the verdict string
        # Check if this is a simple call (only claim_arg and challenge_arg provided)
        is_simple_call = (
            refutation is None and
            visual_analysis is None and
            textual_analysis is None and
            source_analysis is None and
            (item is None or item == {})
        )
        
        if is_simple_call:
            return verdict
        
        return result
    
    def _calculate_evidence_strength(
        self,
        claim_arg: str,
        challenge_arg: str,
        refutation: Dict[str, Any]
    ) -> float:
        """Kanıt gücü skoru - Dengeli yaklaşım"""
        score = 0.6  # Daha yüksek base score (gerçek haberler için daha adil)
        
        # Claim argümanı analizi
        if claim_arg:
            claim_lower = claim_arg.lower()
            claim_length = len(claim_arg.split())
            
            # Pozitif göstergeler
            if claim_length > 30:
                score += 0.15
            if any(word in claim_lower for word in ["evidence", "source", "study", "research", "data", "official"]):
                score += 0.15
            if any(word in claim_lower for word in ["verified", "confirmed", "proven", "fact"]):
                score += 0.1
            
            # Negatif göstergeler (sahte haber işaretleri)
            if any(word in claim_lower for word in ["shocking", "secret", "hidden", "exposed", "revealed"]):
                score -= 0.2
            if "!" in claim_arg or claim_arg.isupper():
                score -= 0.15
            if any(word in claim_lower for word in ["allegedly", "rumor", "unconfirmed"]):
                score -= 0.1
        
        # Challenge argümanı analizi (güçlü challenge = düşük skor)
        if challenge_arg:
            challenge_lower = challenge_arg.lower()
            challenge_length = len(challenge_arg.split())
            
            # Güçlü challenge göstergeleri
            if challenge_length > 25:
                score -= 0.15
            if any(word in challenge_lower for word in ["evidence", "proof", "verified", "fact-check"]):
                score -= 0.15
            if any(word in challenge_lower for word in ["false", "misleading", "inaccurate", "debunked"]):
                score -= 0.2
            if any(word in challenge_lower for word in ["no source", "unverified", "lacks evidence"]):
                score -= 0.1
            
            # Zayıf challenge (pozitif)
            weak_indicators = ["might", "could", "possibly", "uncertain"]
            if any(indicator in challenge_lower for indicator in weak_indicators):
                score += 0.1
        
        # Refutation analizi
        if refutation:
            ref_confidence = refutation.get("confidence", 0.5)
            if ref_confidence > 0.7:
                score += 0.15
            elif ref_confidence < 0.4:
                score -= 0.1
        
        return min(1.0, max(0.0, score))
    
    def _calculate_source_credibility(self, source_analysis: Dict[str, Any]) -> float:
        """Kaynak güvenilirlik skoru - Güvenilir kaynaklara daha yüksek skor"""
        if not source_analysis:
            return 0.65  # Bilinmeyen kaynaklar için daha yüksek default
        
        # source_analysis yapısı: {source_info: {...}, authority_score: float}
        source_info = source_analysis.get("source_info", {})
        credibility = source_info.get("credibility_score", 0.65)  # Default artırıldı
        authority = source_analysis.get("authority_score", 0.65)  # Default artırıldı
        
        # Güvenilir kaynaklar için bonus
        source_type = source_info.get("source_type", "")
        if source_type == "established_media" or source_type == "news_agency":
            credibility = max(credibility, 0.75)
            authority = max(authority, 0.75)
        
        return (credibility + authority) / 2.0
    
    def _calculate_argument_quality(
        self,
        claim_arg: str,
        challenge_arg: str,
        refutation: Dict[str, Any]
    ) -> float:
        """Argüman kalitesi skoru - Dengeli yaklaşım"""
        score = 0.6  # Daha yüksek başlangıç (gerçek haberler için daha adil)
        
        # Claim argümanı kalitesi
        if claim_arg:
            claim_lower = claim_arg.lower()
            claim_words = claim_arg.split()
            
            # Detay ve kalite göstergeleri
            if len(claim_words) > 20:
                score += 0.15
            if any(word in claim_lower for word in ["because", "evidence", "source", "data", "study", "research"]):
                score += 0.15
            if any(word in claim_lower for word in ["according to", "reports", "official", "verified"]):
                score += 0.1
            
            # Kalite sorunları
            if len(claim_words) < 10:
                score -= 0.1
            if any(word in claim_lower for word in ["maybe", "perhaps", "might be", "could be"]):
                score -= 0.1
        
        # Challenge argümanı kalitesi (güçlü challenge = düşük skor)
        if challenge_arg:
            challenge_lower = challenge_arg.lower()
            challenge_words = challenge_arg.split()
            
            # Güçlü challenge göstergeleri
            if len(challenge_words) > 25:
                score -= 0.15
            if any(word in challenge_lower for word in ["evidence", "proof", "verified", "fact-check", "debunked"]):
                score -= 0.2
            if any(word in challenge_lower for word in ["false", "misleading", "inaccurate", "untrue"]):
                score -= 0.15
            if any(word in challenge_lower for word in ["no source", "unverified", "lacks", "missing"]):
                score -= 0.1
        
        # Refutation kalitesi
        if refutation:
            ref_confidence = refutation.get("confidence", 0.5)
            if ref_confidence > 0.75:
                score += 0.15
            elif ref_confidence < 0.35:
                score -= 0.1
        
        return min(1.0, max(0.0, score))
    
    def _calculate_consistency_score(
        self,
        visual_analysis: Dict[str, Any],
        textual_analysis: Dict[str, Any]
    ) -> float:
        """Tutarlılık skoru"""
        scores = []
        
        if visual_analysis:
            vis_confidence = visual_analysis.get("confidence", 0.5)
            scores.append(vis_confidence)
        
        if textual_analysis:
            text_confidence = textual_analysis.get("overall_confidence", 0.5)
            scores.append(text_confidence)
        
        if not scores:
            return 0.5
        
        return sum(scores) / len(scores)
    
    def _calculate_confidence_interval(self, criteria_scores: Dict[str, float]) -> tuple:
        """Güven aralığı hesaplama"""
        scores = list(criteria_scores.values())
        if not scores:
            return (0.0, 1.0)
        
        mean_score = sum(scores) / len(scores)
        std_dev = (sum((s - mean_score) ** 2 for s in scores) / len(scores)) ** 0.5
        
        lower = max(0.0, mean_score - std_dev)
        upper = min(1.0, mean_score + std_dev)
        
        return (lower, upper)
    
    def _determine_verdict(self, score: float, confidence_interval: tuple) -> str:
        """Karar verme - Çok dengeli eşikler (gerçek haberleri korur)"""
        lower, upper = confidence_interval
        
        # Apply training adjustments if available
        if hasattr(self, '_threshold_adjustment') and self._threshold_adjustment == "sensitive":
            # More sensitive thresholds (better fake detection)
            # Yüksek güven ve yüksek skor -> REAL
            if score >= 0.72 and lower >= 0.62:
                return "REAL"
            
            # Orta-yüksek skor ve güven -> REAL
            if score >= 0.67 and lower >= 0.57:
                return "REAL"
            
            # Orta skor ve orta güven -> REAL
            if score >= 0.62 and lower >= 0.52:
                return "REAL"
            
            # Çok düşük güven veya çok düşük skor -> FAKE (more sensitive)
            if score <= 0.38 or (upper <= 0.48 and score < 0.48):
                return "FAKE"
            
            # Orta-düşük skor ve düşük güven -> FAKE
            if score < 0.48 and upper < 0.58:
                return "FAKE"
        else:
            # Normal thresholds
            # Yüksek güven ve yüksek skor -> REAL
            if score >= 0.70 and lower >= 0.60:
                return "REAL"
            
            # Orta-yüksek skor ve güven -> REAL
            if score >= 0.65 and lower >= 0.55:
                return "REAL"
            
            # Orta skor ve orta güven -> REAL (gerçek haberler için tolerans)
            if score >= 0.60 and lower >= 0.50:
                return "REAL"
            
            # Çok düşük güven veya çok düşük skor -> FAKE (çok konservatif)
            if score <= 0.35 or (upper <= 0.45 and score < 0.45):
                return "FAKE"
            
            # Orta-düşük skor ve düşük güven -> FAKE (daha konservatif)
            if score < 0.45 and upper < 0.55:
                return "FAKE"
        
        # Belirsiz durum - gerçek haberler için çok toleranslı
        # 0.45-0.60 arası skorlar UNSURE olarak kalır (gerçek haberler için güvenli)
        return "UNSURE"
    
    def _generate_rationale(
        self,
        verdict: str,
        criteria_scores: Dict[str, float]
    ) -> str:
        """Gerekçe oluşturma"""
        parts = [f"Verdict: {verdict}"]
        
        for criterion, score in criteria_scores.items():
            parts.append(f"{criterion}: {score:.2f}")
        
        return ". ".join(parts)

