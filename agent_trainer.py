"""
Agent Training and Performance Improvement System
Tracks agent errors and retrains underperforming agents
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict
from metrics import get_metrics_collector


class AgentTrainer:
    """
    Agent Training System
    Monitors agent performance and retrains underperforming agents
    """
    
    def __init__(self, training_file: str = "logs/agent_training.json"):
        self.training_file = training_file
        self.metrics = get_metrics_collector()
        self.agent_performance_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.agent_adjustments: Dict[str, Dict[str, Any]] = {}
        self.error_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Performance thresholds
        self.min_success_rate = 0.70  # Minimum 70% success rate
        self.max_error_rate = 0.30  # Maximum 30% error rate
        self.min_accuracy = 0.65  # Minimum accuracy for verdicts
        
        # Load previous training data
        self._load_training_data()
    
    def _load_training_data(self):
        """Load previous training data"""
        try:
            if os.path.exists(self.training_file):
                with open(self.training_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.agent_adjustments = data.get("adjustments", {})
                    self.error_patterns = data.get("error_patterns", {})
        except Exception:
            pass
    
    def _save_training_data(self):
        """Save training data"""
        try:
            os.makedirs(os.path.dirname(self.training_file), exist_ok=True)
            with open(self.training_file, "w", encoding="utf-8") as f:
                json.dump({
                    "adjustments": self.agent_adjustments,
                    "error_patterns": self.error_patterns,
                    "last_updated": datetime.utcnow().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def analyze_agent_performance(self) -> Dict[str, Any]:
        """Analyze all agent performances and identify underperformers"""
        agent_metrics = self.metrics.get_agent_metrics()
        
        analysis = {
            "underperforming_agents": [],
            "well_performing_agents": [],
            "recommendations": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for agent_id, metrics in agent_metrics.items():
            success_rate = metrics.get("success_rate", 1.0)
            error_count = metrics.get("error_count", 0)
            call_count = metrics.get("call_count", 0)
            
            # Calculate performance score
            performance_score = self._calculate_performance_score(metrics)
            
            agent_analysis = {
                "agent_id": agent_id,
                "performance_score": performance_score,
                "success_rate": success_rate,
                "error_rate": error_count / call_count if call_count > 0 else 0.0,
                "call_count": call_count,
                "average_time": metrics.get("average_time", 0.0),
                "needs_training": False,
                "issues": []
            }
            
            # Identify issues
            if success_rate < self.min_success_rate:
                agent_analysis["needs_training"] = True
                agent_analysis["issues"].append(f"Low success rate: {success_rate:.2%}")
            
            if call_count > 10 and (error_count / call_count) > self.max_error_rate:
                agent_analysis["needs_training"] = True
                agent_analysis["issues"].append(f"High error rate: {error_count / call_count:.2%}")
            
            if performance_score < 0.60:
                agent_analysis["needs_training"] = True
                agent_analysis["issues"].append(f"Low performance score: {performance_score:.2f}")
            
            # Categorize
            if agent_analysis["needs_training"]:
                analysis["underperforming_agents"].append(agent_analysis)
                # Generate recommendations
                analysis["recommendations"][agent_id] = self._generate_recommendations(
                    agent_id, metrics, agent_analysis
                )
            else:
                analysis["well_performing_agents"].append(agent_analysis)
        
        return analysis
    
    def _calculate_performance_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall performance score for an agent"""
        success_rate = metrics.get("success_rate", 1.0)
        call_count = metrics.get("call_count", 0)
        error_count = metrics.get("error_count", 0)
        avg_time = metrics.get("average_time", 0.0)
        
        # Base score from success rate
        score = success_rate
        
        # Penalty for high error rate
        if call_count > 0:
            error_rate = error_count / call_count
            score -= error_rate * 0.3
        
        # Bonus for high call count (more reliable)
        if call_count > 20:
            score += 0.1
        
        # Penalty for very slow execution
        if avg_time > 5.0:  # More than 5 seconds
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _generate_recommendations(
        self,
        agent_id: str,
        metrics: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate training recommendations for an agent"""
        recommendations = {
            "agent_id": agent_id,
            "priority": "high" if analysis["performance_score"] < 0.50 else "medium",
            "actions": [],
            "parameter_adjustments": {}
        }
        
        # Agent-specific recommendations
        if agent_id == "JA":  # Judge Agent
            if analysis["success_rate"] < 0.70:
                recommendations["actions"].append("Adjust verdict thresholds")
                recommendations["parameter_adjustments"]["threshold_adjustment"] = "increase_sensitivity"
            
            if analysis.get("error_rate", 0) > 0.20:
                recommendations["actions"].append("Improve error handling")
                recommendations["parameter_adjustments"]["error_handling"] = "enhanced"
        
        elif agent_id == "TCA":  # Textual Context Agent
            if analysis["success_rate"] < 0.75:
                recommendations["actions"].append("Enhance text analysis algorithms")
                recommendations["parameter_adjustments"]["analysis_depth"] = "increased"
        
        elif agent_id == "VVA":  # Visual Validator Agent
            if analysis["success_rate"] < 0.70:
                recommendations["actions"].append("Improve image analysis")
                recommendations["parameter_adjustments"]["image_analysis"] = "enhanced"
        
        elif agent_id == "STA":  # Source Tracker Agent
            if analysis["success_rate"] < 0.80:
                recommendations["actions"].append("Update source credibility database")
                recommendations["parameter_adjustments"]["source_db_update"] = True
        
        elif agent_id == "CA":  # Claim Agent
            if analysis["success_rate"] < 0.75:
                recommendations["actions"].append("Improve argument generation")
                recommendations["parameter_adjustments"]["argument_quality"] = "enhanced"
        
        elif agent_id == "CHA":  # Challenge Agent
            if analysis["success_rate"] < 0.75:
                recommendations["actions"].append("Strengthen challenge arguments")
                recommendations["parameter_adjustments"]["challenge_strength"] = "increased"
        
        # General recommendations
        if analysis.get("error_rate", 0) > 0.15:
            recommendations["actions"].append("Add more error handling and validation")
        
        if analysis.get("average_time", 0) > 3.0:
            recommendations["actions"].append("Optimize execution time")
        
        return recommendations
    
    def record_error(
        self,
        agent_id: str,
        error_type: str,
        error_message: str,
        context: Dict[str, Any]
    ):
        """Record an agent error for pattern analysis"""
        error_record = {
            "agent_id": agent_id,
            "error_type": error_type,
            "error_message": error_message,
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.error_patterns[agent_id].append(error_record)
        
        # Keep only last 100 errors per agent
        if len(self.error_patterns[agent_id]) > 100:
            self.error_patterns[agent_id] = self.error_patterns[agent_id][-100:]
        
        # Analyze error patterns
        self._analyze_error_patterns(agent_id)
    
    def _analyze_error_patterns(self, agent_id: str):
        """Analyze error patterns for an agent"""
        errors = self.error_patterns.get(agent_id, [])
        if len(errors) < 5:
            return
        
        # Group errors by type
        error_types = defaultdict(int)
        for error in errors[-20:]:  # Last 20 errors
            error_types[error["error_type"]] += 1
        
        # If one error type dominates, suggest fix
        if error_types:
            most_common = max(error_types.items(), key=lambda x: x[1])
            if most_common[1] >= len(errors) * 0.5:  # 50% or more
                self.agent_adjustments[agent_id] = {
                    "common_error": most_common[0],
                    "error_count": most_common[1],
                    "suggested_fix": self._suggest_fix(agent_id, most_common[0]),
                    "last_updated": datetime.utcnow().isoformat()
                }
                self._save_training_data()
    
    def _suggest_fix(self, agent_id: str, error_type: str) -> str:
        """Suggest a fix for a common error type"""
        fixes = {
            "JA": {
                "ValueError": "Add input validation for verdict calculation",
                "KeyError": "Add default values for missing keys",
                "TypeError": "Add type checking before operations"
            },
            "TCA": {
                "AttributeError": "Add null checks before attribute access",
                "IndexError": "Add bounds checking for list operations"
            },
            "VVA": {
                "URLError": "Add retry logic for image downloads",
                "TimeoutError": "Increase timeout or add fallback"
            }
        }
        
        agent_fixes = fixes.get(agent_id, {})
        return agent_fixes.get(error_type, "Review error handling logic")
    
    def apply_training(self, agent_id: str, recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """Apply training adjustments to an agent"""
        adjustments = recommendations.get("parameter_adjustments", {})
        
        training_result = {
            "agent_id": agent_id,
            "adjustments_applied": adjustments,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "applied"
        }
        
        # Store adjustments
        self.agent_adjustments[agent_id] = {
            **self.agent_adjustments.get(agent_id, {}),
            **adjustments,
            "last_training": datetime.utcnow().isoformat()
        }
        
        self._save_training_data()
        
        return training_result
    
    def get_agent_adjustments(self, agent_id: str) -> Dict[str, Any]:
        """Get current adjustments for an agent"""
        return self.agent_adjustments.get(agent_id, {})
    
    def get_training_report(self) -> Dict[str, Any]:
        """Get comprehensive training report"""
        analysis = self.analyze_agent_performance()
        
        return {
            "analysis": analysis,
            "error_patterns": {
                agent_id: {
                    "total_errors": len(errors),
                    "recent_errors": len([e for e in errors if datetime.fromisoformat(e["timestamp"]) > datetime.utcnow() - timedelta(days=7)]),
                    "most_common_error": max(
                        [(e["error_type"], sum(1 for err in errors if err["error_type"] == e["error_type"])) 
                         for e in errors],
                        key=lambda x: x[1],
                        default=("none", 0)
                    )[0] if errors else "none"
                }
                for agent_id, errors in self.error_patterns.items()
            },
            "applied_adjustments": self.agent_adjustments,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global trainer instance
_trainer_instance: Optional[AgentTrainer] = None

def get_agent_trainer() -> AgentTrainer:
    """Get or create the global agent trainer"""
    global _trainer_instance
    if _trainer_instance is None:
        _trainer_instance = AgentTrainer()
    return _trainer_instance

