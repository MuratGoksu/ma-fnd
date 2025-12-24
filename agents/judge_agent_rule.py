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
        """Kanıt gücü skoru"""
        score = 0.5  # Base score
        
        # Claim argümanı uzunluğu ve detayı
        if claim_arg:
            claim_length = len(claim_arg.split())
            if claim_length > 20:
                score += 0.1
            if "evidence" in claim_arg.lower() or "source" in claim_arg.lower():
                score += 0.1
        
        # Challenge argümanı zayıfsa
        if challenge_arg:
            challenge_lower = challenge_arg.lower()
            weak_indicators = ["might", "could", "possibly", "unverified"]
            if any(indicator in challenge_lower for indicator in weak_indicators):
                score += 0.1
        
        # Refutation varsa ve güçlüyse
        if refutation and refutation.get("confidence", 0) > 0.6:
            score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def _calculate_source_credibility(self, source_analysis: Dict[str, Any]) -> float:
        """Kaynak güvenilirlik skoru"""
        if not source_analysis:
            return 0.5
        
        # source_analysis yapısı: {source_info: {...}, authority_score: float}
        source_info = source_analysis.get("source_info", {})
        credibility = source_info.get("credibility_score", 0.5)
        authority = source_analysis.get("authority_score", 0.5)
        
        return (credibility + authority) / 2.0
    
    def _calculate_argument_quality(
        self,
        claim_arg: str,
        challenge_arg: str,
        refutation: Dict[str, Any]
    ) -> float:
        """Argüman kalitesi skoru"""
        score = 0.5
        
        # Claim argümanı kalitesi
        if claim_arg:
            if len(claim_arg.split()) > 15:
                score += 0.1
            if any(word in claim_arg.lower() for word in ["because", "evidence", "source", "data"]):
                score += 0.1
        
        # Challenge argümanı kalitesi (ters - güçlü challenge düşük skor)
        if challenge_arg:
            if len(challenge_arg.split()) > 20:
                score -= 0.1
            if any(word in challenge_arg.lower() for word in ["evidence", "proof", "verified"]):
                score -= 0.1
        
        # Refutation kalitesi
        if refutation:
            ref_confidence = refutation.get("confidence", 0.5)
            if ref_confidence > 0.7:
                score += 0.1
        
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
        """Karar verme"""
        lower, upper = confidence_interval
        
        # Yüksek güven ve yüksek skor -> REAL
        if score >= 0.7 and lower >= 0.6:
            return "REAL"
        
        # Düşük güven veya düşük skor -> FAKE
        if score <= 0.4 or upper <= 0.5:
            return "FAKE"
        
        # Belirsiz durum
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

