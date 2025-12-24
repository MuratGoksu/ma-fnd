"""
Meta-Evaluator Agent (MEA)
Görev: Judge kararının meta-analizi
"""
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent


class MetaEvaluatorAgent(BaseAgent):
    """
    Meta-Evaluator Agent - Judge kararının meta-analizi
    Bias detection ve self-critique
    """
    
    def __init__(self):
        super().__init__("MEA")
        self.evaluation_history: List[Dict[str, Any]] = []
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ana işleme metodu"""
        judge_decision = data.get("judge_decision", {})
        all_analyses = data.get("all_analyses", {})
        
        # Meta-analiz
        meta_evaluation = self.evaluate_decision(judge_decision, all_analyses)
        
        result = {
            "status": "evaluated",
            "meta_evaluation": meta_evaluation,
            "recommendation": meta_evaluation.get("recommendation", "accept")
        }
        
        # Mesaj gönder
        self.send_message(
            message_type="feedback",
            content={
                "type": "meta_evaluation",
                "data": result
            },
            target_agents=["JA", "OA"]
        )
        
        # Geçmişe ekle
        self.evaluation_history.append(result)
        
        return result
    
    def evaluate_decision(
        self,
        judge_decision: Dict[str, Any],
        all_analyses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Judge kararının meta-analizi"""
        
        # Bias analizi
        bias_analysis = self._detect_bias(judge_decision, all_analyses)
        
        # Güven kalibrasyonu
        confidence_calibration = self._calibrate_confidence(judge_decision)
        
        # Hata pattern tespiti
        error_patterns = self._detect_error_patterns(judge_decision, all_analyses)
        
        # İyileştirme önerileri
        improvements = self._suggest_improvements(
            judge_decision,
            bias_analysis,
            confidence_calibration,
            error_patterns
        )
        
        # Meta karar
        recommendation = self._make_recommendation(
            judge_decision,
            bias_analysis,
            confidence_calibration,
            error_patterns
        )
        
        return {
            "bias_analysis": bias_analysis,
            "confidence_calibration": confidence_calibration,
            "error_patterns": error_patterns,
            "improvements": improvements,
            "recommendation": recommendation,
            "overall_quality": self._calculate_overall_quality(
                bias_analysis,
                confidence_calibration,
                error_patterns
            )
        }
    
    def _detect_bias(
        self,
        judge_decision: Dict[str, Any],
        all_analyses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Bias tespiti"""
        biases = []
        
        verdict = judge_decision.get("verdict", "UNSURE")
        criteria_scores = judge_decision.get("criteria_scores", {})
        
        # Aşırı güven bias'ı
        confidence = judge_decision.get("confidence", 0.5)
        if confidence > 0.9:
            biases.append({
                "type": "overconfidence",
                "severity": "medium",
                "description": "Judge shows overconfidence in decision"
            })
        
        # Kriter ağırlık bias'ı
        if criteria_scores:
            scores = list(criteria_scores.values())
            if max(scores) - min(scores) > 0.5:
                biases.append({
                    "type": "criterion_imbalance",
                    "severity": "low",
                    "description": "Large variance in criterion scores"
                })
        
        # Verdict bias'ı (sürekli aynı karar)
        if len(self.evaluation_history) > 5:
            recent_verdicts = [
                eval.get("meta_evaluation", {}).get("recommendation", "")
                for eval in self.evaluation_history[-5:]
            ]
            if len(set(recent_verdicts)) == 1:
                biases.append({
                    "type": "verdict_bias",
                    "severity": "low",
                    "description": "Pattern of similar verdicts detected"
                })
        
        return {
            "detected_biases": biases,
            "bias_score": len(biases) * 0.2,  # Her bias 0.2 puan
            "is_biased": len(biases) > 0
        }
    
    def _calibrate_confidence(self, judge_decision: Dict[str, Any]) -> Dict[str, Any]:
        """Güven kalibrasyonu"""
        confidence = judge_decision.get("confidence", 0.5)
        confidence_interval = judge_decision.get("confidence_interval", (0.0, 1.0))
        
        lower, upper = confidence_interval
        interval_width = upper - lower
        
        # Geniş aralık -> düşük kalibrasyon
        if interval_width > 0.4:
            calibration_score = 0.6
            calibration_status = "low"
        elif interval_width > 0.2:
            calibration_score = 0.8
            calibration_status = "medium"
        else:
            calibration_score = 0.9
            calibration_status = "high"
        
        # Güven skoru ile aralık tutarlılığı
        if lower <= confidence <= upper:
            consistency = 1.0
        else:
            consistency = 0.7
        
        return {
            "calibration_score": calibration_score,
            "calibration_status": calibration_status,
            "interval_width": interval_width,
            "consistency": consistency,
            "calibrated_confidence": confidence * calibration_score
        }
    
    def _detect_error_patterns(
        self,
        judge_decision: Dict[str, Any],
        all_analyses: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Hata pattern tespiti"""
        patterns = []
        
        # Çelişkili analizler
        visual_analysis = all_analyses.get("visual_analysis", {})
        textual_analysis = all_analyses.get("textual_analysis", {})
        
        if visual_analysis and textual_analysis:
            vis_conf = visual_analysis.get("confidence", 0.5)
            text_conf = textual_analysis.get("overall_confidence", 0.5)
            
            if abs(vis_conf - text_conf) > 0.4:
                patterns.append({
                    "type": "contradictory_analyses",
                    "severity": "medium",
                    "description": "Visual and textual analyses show significant disagreement"
                })
        
        # Eksik analiz
        required_analyses = ["source_analysis", "textual_analysis"]
        missing = [req for req in required_analyses if req not in all_analyses]
        
        if missing:
            patterns.append({
                "type": "missing_analyses",
                "severity": "low",
                "description": f"Missing analyses: {', '.join(missing)}"
            })
        
        # Düşük güven ama yüksek verdict
        confidence = judge_decision.get("confidence", 0.5)
        verdict = judge_decision.get("verdict", "UNSURE")
        
        if confidence < 0.5 and verdict != "UNSURE":
            patterns.append({
                "type": "confidence_verdict_mismatch",
                "severity": "medium",
                "description": "Low confidence but definitive verdict"
            })
        
        return patterns
    
    def _suggest_improvements(
        self,
        judge_decision: Dict[str, Any],
        bias_analysis: Dict[str, Any],
        confidence_calibration: Dict[str, Any],
        error_patterns: List[Dict[str, Any]]
    ) -> List[str]:
        """İyileştirme önerileri"""
        improvements = []
        
        # Bias önerileri
        if bias_analysis.get("is_biased"):
            improvements.append("Consider re-evaluating with adjusted weights to reduce bias")
        
        # Kalibrasyon önerileri
        if confidence_calibration.get("calibration_status") == "low":
            improvements.append("Widen confidence interval or reduce confidence score")
        
        # Hata pattern önerileri
        for pattern in error_patterns:
            if pattern["type"] == "contradictory_analyses":
                improvements.append("Reconcile visual and textual analysis discrepancies")
            elif pattern["type"] == "missing_analyses":
                improvements.append("Gather missing analyses before final decision")
            elif pattern["type"] == "confidence_verdict_mismatch":
                improvements.append("Consider changing verdict to UNSURE given low confidence")
        
        return improvements
    
    def _make_recommendation(
        self,
        judge_decision: Dict[str, Any],
        bias_analysis: Dict[str, Any],
        confidence_calibration: Dict[str, Any],
        error_patterns: List[Dict[str, Any]]
    ) -> str:
        """Meta karar önerisi"""
        # Ciddi sorunlar varsa reddet
        if bias_analysis.get("bias_score", 0) > 0.5:
            return "reject"
        
        if any(p["severity"] == "high" for p in error_patterns):
            return "reject"
        
        # Orta seviye sorunlar varsa gözden geçir
        if bias_analysis.get("is_biased") or len(error_patterns) > 2:
            return "review"
        
        # Sorun yoksa kabul et
        return "accept"
    
    def _calculate_overall_quality(
        self,
        bias_analysis: Dict[str, Any],
        confidence_calibration: Dict[str, Any],
        error_patterns: List[Dict[str, Any]]
    ) -> float:
        """Genel kalite skoru"""
        # Bias skoru (ters - bias varsa kalite düşer)
        bias_penalty = bias_analysis.get("bias_score", 0)
        
        # Kalibrasyon skoru
        calibration_score = confidence_calibration.get("calibration_score", 0.5)
        
        # Hata pattern cezası
        error_penalty = len(error_patterns) * 0.1
        
        quality = calibration_score - bias_penalty - error_penalty
        return max(0.0, min(1.0, quality))

