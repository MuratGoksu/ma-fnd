"""
Optimizer Agent (OA)
Görev: Sistem performans optimizasyonu
"""
from typing import Dict, Any, List, Optional
import random
from .base_agent import BaseAgent


class OptimizerAgent(BaseAgent):
    """
    Optimizer Agent - Sistem performans optimizasyonu
    PSO, DE gibi optimizasyon algoritmaları için hazır
    """
    
    def __init__(self):
        super().__init__("OA")
        self.performance_history: List[Dict[str, Any]] = []
        self.current_weights: Dict[str, float] = {
            "evidence_strength": 0.30,
            "source_credibility": 0.25,
            "argument_quality": 0.25,
            "consistency_score": 0.20
        }
        self.best_weights: Dict[str, float] = self.current_weights.copy()
        self.best_score: float = 0.0
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ana işleme metodu"""
        performance_metrics = data.get("performance_metrics", {})
        meta_feedback = data.get("meta_feedback", {})
        
        # Performans kaydı
        self.performance_history.append({
            "metrics": performance_metrics,
            "feedback": meta_feedback,
            "timestamp": self._get_timestamp()
        })
        
        # Optimizasyon
        optimization = self.optimize_weights(performance_metrics, meta_feedback)
        
        result = {
            "status": "optimized",
            "optimization": optimization,
            "new_weights": optimization.get("new_weights", self.current_weights)
        }
        
        # Mesaj gönder
        self.send_message(
            message_type="feedback",
            content={
                "type": "optimization_update",
                "data": result
            },
            target_agents=["JA"]
        )
        
        return result
    
    def optimize_weights(
        self,
        performance_metrics: Dict[str, Any],
        meta_feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ağırlık optimizasyonu"""
        
        # Mevcut performans skoru
        current_score = self._calculate_performance_score(
            performance_metrics,
            meta_feedback
        )
        
        # Basit gradient-free optimizasyon (gerçek uygulamada PSO/DE kullanılır)
        new_weights = self._adjust_weights(
            self.current_weights,
            performance_metrics,
            meta_feedback
        )
        
        # Yeni skor
        # (Gerçek uygulamada yeni ağırlıklarla test edilir)
        new_score = current_score * 1.01  # Placeholder
        
        # En iyi ağırlıkları güncelle
        if new_score > self.best_score:
            self.best_score = new_score
            self.best_weights = new_weights.copy()
        
        self.current_weights = new_weights
        
        return {
            "current_score": current_score,
            "new_score": new_score,
            "new_weights": new_weights,
            "best_weights": self.best_weights,
            "best_score": self.best_score,
            "improvement": new_score - current_score
        }
    
    def _calculate_performance_score(
        self,
        performance_metrics: Dict[str, Any],
        meta_feedback: Dict[str, Any]
    ) -> float:
        """Performans skoru hesaplama"""
        score = 0.5  # Base score
        
        # Accuracy bonusu
        accuracy = performance_metrics.get("accuracy", 0.5)
        score += accuracy * 0.3
        
        # Precision bonusu
        precision = performance_metrics.get("precision", 0.5)
        score += precision * 0.2
        
        # Recall bonusu
        recall = performance_metrics.get("recall", 0.5)
        score += recall * 0.2
        
        # Meta feedback bonusu
        meta_quality = meta_feedback.get("overall_quality", 0.5)
        score += meta_quality * 0.3
        
        return min(1.0, max(0.0, score))
    
    def _adjust_weights(
        self,
        current_weights: Dict[str, float],
        performance_metrics: Dict[str, Any],
        meta_feedback: Dict[str, Any]
    ) -> Dict[str, float]:
        """Ağırlık ayarlama"""
        new_weights = current_weights.copy()
        
        # Meta feedback'e göre ayarlama
        bias_analysis = meta_feedback.get("bias_analysis", {})
        if bias_analysis.get("is_biased"):
            # Bias varsa ağırlıkları dengele
            total = sum(new_weights.values())
            for key in new_weights:
                new_weights[key] = total / len(new_weights)
        
        # Performans metriklerine göre ayarlama
        if performance_metrics.get("false_positive_rate", 0) > 0.3:
            # False positive yüksekse source_credibility'yi artır
            new_weights["source_credibility"] = min(0.4, new_weights["source_credibility"] + 0.05)
            # Diğerlerini azalt
            remaining = 1.0 - new_weights["source_credibility"]
            other_keys = [k for k in new_weights if k != "source_credibility"]
            for key in other_keys:
                new_weights[key] = remaining / len(other_keys)
        
        # Normalize et
        total = sum(new_weights.values())
        for key in new_weights:
            new_weights[key] = new_weights[key] / total
        
        return new_weights
    
    def get_optimal_weights(self) -> Dict[str, float]:
        """Optimal ağırlıkları döndür"""
        return self.best_weights.copy()
    
    def _get_timestamp(self) -> str:
        """Timestamp oluştur"""
        from datetime import datetime
        return datetime.utcnow().isoformat()

