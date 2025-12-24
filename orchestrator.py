"""
Main Orchestration System
Coordinates all agents in the multi-agent fake news detection pipeline
"""
from typing import Dict, Any, Optional, List
import time
from datetime import datetime

from agents import (
    CrawlerAgent, SourceTrackerAgent, PreprocessingAgent,
    VisualValidatorAgent, TextualContextAgent,
    ClaimAgent, ChallengeAgent, RefuterAgent,
    JudgeAgent as RuleJudgeAgent, MetaEvaluatorAgent,
    OptimizerAgent, ReinforcementAgent, CorrectionAgent,
    get_broker
)
from metrics import get_metrics_collector


class Orchestrator:
    """
    Main orchestrator for the multi-agent fake news detection system
    Coordinates all phases of the pipeline
    """
    
    def __init__(self):
        self.broker = get_broker()
        self.metrics = get_metrics_collector()
        
        # Initialize all agents
        self.crawler = CrawlerAgent()
        self.sta = SourceTrackerAgent()
        self.ppa = PreprocessingAgent()
        self.vva = VisualValidatorAgent()
        self.tca = TextualContextAgent()
        self.ca = ClaimAgent()
        self.cha = ChallengeAgent()
        self.ra = RefuterAgent()
        self.ja = RuleJudgeAgent()
        self.mea = MetaEvaluatorAgent()
        self.oa = OptimizerAgent()
        self.rla = ReinforcementAgent()
        self.coa = CorrectionAgent()
        
        # Storage for pipeline results
        self.pipeline_results: Dict[str, Any] = {}
    
    def process_news_item(self, item: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main pipeline execution
        Processes a news item through all phases
        """
        start_time = time.time()
        phase_times: Dict[str, float] = {}
        item_id = item.get("id", "unknown") if item else "unknown"
        success = True
        
        try:
            # Phase 1: Data Collection & Preprocessing
            phase_start = time.time()
            if item is None:
                item = self.crawler.fetch_news()
                item_id = item.get("id", "unknown")
            
            # Source tracking
            agent_start = time.time()
            source_result = self.sta.process(item)
            self.metrics.record_agent_call("STA", time.time() - agent_start, True)
            
            # Preprocessing
            agent_start = time.time()
            preprocessed = self.ppa.process(item)
            self.metrics.record_agent_call("PP-A", time.time() - agent_start, True)
            
            phase_times["data_collection"] = time.time() - phase_start
            self.metrics.record_phase_execution("data_collection", phase_times["data_collection"])
            
            if preprocessed.get("status") in ["duplicate", "spam"]:
                processing_time = time.time() - start_time
                self.metrics.record_pipeline_execution(
                    item_id, "UNSURE", processing_time, phase_times, True
                )
                return {
                    "status": preprocessed.get("status"),
                    "item": item,
                    "processing_time": processing_time
                }
            
            cleaned_item = preprocessed.get("cleaned_data", item)
            
            # Phase 2: Content Analysis (Parallel)
            phase_start = time.time()
            agent_start = time.time()
            visual_result = self.vva.process(cleaned_item)
            self.metrics.record_agent_call("VVA", time.time() - agent_start, True)
            
            agent_start = time.time()
            textual_result = self.tca.process(cleaned_item)
            self.metrics.record_agent_call("TCA", time.time() - agent_start, True)
            
            phase_times["content_analysis"] = time.time() - phase_start
            self.metrics.record_phase_execution("content_analysis", phase_times["content_analysis"])
            
            # Phase 3: Debate Process
            phase_start = time.time()
            agent_start = time.time()
            claim_arg = self.ca.generate_argument(cleaned_item)
            self.metrics.record_agent_call("CA", time.time() - agent_start, True)
            
            agent_start = time.time()
            challenge_arg = self.cha.generate_argument(cleaned_item)
            self.metrics.record_agent_call("CHA", time.time() - agent_start, True)
            
            # Refutation (if needed)
            refutation_data = {
                "claim_argument": claim_arg,
                "challenge_argument": challenge_arg,
                "item": cleaned_item
            }
            agent_start = time.time()
            refutation_result = self.ra.process(refutation_data)
            self.metrics.record_agent_call("RA", time.time() - agent_start, True)
            
            phase_times["debate"] = time.time() - phase_start
            self.metrics.record_phase_execution("debate", phase_times["debate"])
            
            # Phase 4: Decision Making
            phase_start = time.time()
            judge_data = {
                "claim_argument": claim_arg,
                "challenge_argument": challenge_arg,
                "refutation": refutation_result,
                "visual_analysis": visual_result,
                "textual_analysis": textual_result,
                "source_analysis": source_result,
                "item": cleaned_item
            }
            agent_start = time.time()
            judge_result = self.ja.process(judge_data)
            self.metrics.record_agent_call("JA", time.time() - agent_start, True)
            
            # Meta-evaluation
            meta_data = {
                "judge_decision": judge_result.get("decision", {}),
                "all_analyses": {
                    "visual_analysis": visual_result,
                    "textual_analysis": textual_result,
                    "source_analysis": source_result
                }
            }
            agent_start = time.time()
            meta_result = self.mea.process(meta_data)
            self.metrics.record_agent_call("MEA", time.time() - agent_start, True)
            
            phase_times["decision_making"] = time.time() - phase_start
            self.metrics.record_phase_execution("decision_making", phase_times["decision_making"])
            
            # Phase 5: Learning & Correction
            phase_start = time.time()
            verdict = judge_result.get("verdict", "UNSURE")
            
            # Correction (if fake detected)
            correction_result = None
            if verdict == "FAKE":
                correction_data = {
                    "verdict": verdict,
                    "item": cleaned_item,
                    "analyses": {
                        "visual_analysis": visual_result,
                        "textual_analysis": textual_result,
                        "source_analysis": source_result
                    }
                }
                agent_start = time.time()
                correction_result = self.coa.process(correction_data)
                self.metrics.record_agent_call("COA", time.time() - agent_start, True)
            
            phase_times["correction"] = time.time() - phase_start
            self.metrics.record_phase_execution("correction", phase_times["correction"])
            
        except Exception as e:
            success = False
            # Record error for all agents that might have been called
            # This is a simplified error handling
            raise
        
        finally:
            processing_time = time.time() - start_time
            verdict = judge_result.get("verdict", "UNSURE") if 'judge_result' in locals() else "UNSURE"
            self.metrics.record_pipeline_execution(
                item_id, verdict, processing_time, phase_times, success
            )
        
        # Compile results
        result = {
            "status": "completed",
            "item": cleaned_item,
            "verdict": verdict,
            "confidence": judge_result.get("decision", {}).get("confidence", 0.5),
            "processing_time": processing_time,
            "phases": {
                "source_tracking": source_result,
                "preprocessing": preprocessed,
                "visual_analysis": visual_result,
                "textual_analysis": textual_result,
                "claim_argument": claim_arg,
                "challenge_argument": challenge_arg,
                "refutation": refutation_result,
                "judge_decision": judge_result,
                "meta_evaluation": meta_result,
                "correction": correction_result
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.pipeline_results[cleaned_item.get("id", "unknown")] = result
        
        return result
    
    def get_pipeline_statistics(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        if not self.pipeline_results:
            return {"total_processed": 0}
        
        total = len(self.pipeline_results)
        verdicts = {}
        avg_time = 0.0
        
        for result in self.pipeline_results.values():
            verdict = result.get("verdict", "UNSURE")
            verdicts[verdict] = verdicts.get(verdict, 0) + 1
            avg_time += result.get("processing_time", 0)
        
        avg_time = avg_time / total if total > 0 else 0
        
        return {
            "total_processed": total,
            "verdict_distribution": verdicts,
            "average_processing_time": avg_time,
            "last_processed": max(
                self.pipeline_results.keys(),
                key=lambda k: self.pipeline_results[k].get("timestamp", "")
            ) if self.pipeline_results else None
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get detailed performance metrics summary"""
        return self.metrics.get_summary()
    
    def get_agent_metrics(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for specific agent or all agents"""
        return self.metrics.get_agent_metrics(agent_id)
    
    def get_phase_metrics(self, phase_name: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for specific phase or all phases"""
        return self.metrics.get_phase_metrics(phase_name)

