"""
Performance Metrics Tracking System
Tracks detailed performance metrics for all agents and pipeline phases
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import time
import json
import os
from collections import defaultdict
from dataclasses import dataclass, asdict
from threading import Lock


@dataclass
class AgentMetrics:
    """Individual agent performance metrics"""
    agent_id: str
    call_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    success_count: int = 0
    error_count: int = 0
    last_call_time: Optional[str] = None
    
    def record_call(self, duration: float, success: bool = True):
        """Record a single agent call"""
        self.call_count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        self.last_call_time = datetime.utcnow().isoformat()
    
    @property
    def average_time(self) -> float:
        """Calculate average execution time"""
        return self.total_time / self.call_count if self.call_count > 0 else 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.error_count
        return self.success_count / total if total > 0 else 0.0


@dataclass
class PhaseMetrics:
    """Pipeline phase performance metrics"""
    phase_name: str
    execution_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    last_execution: Optional[str] = None
    
    def record_execution(self, duration: float):
        """Record a phase execution"""
        self.execution_count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.last_execution = datetime.utcnow().isoformat()
    
    @property
    def average_time(self) -> float:
        """Calculate average execution time"""
        return self.total_time / self.execution_count if self.execution_count > 0 else 0.0


class MetricsCollector:
    """
    Centralized metrics collection system
    Thread-safe for concurrent access
    """
    
    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file or "logs/metrics.jsonl"
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.phase_metrics: Dict[str, PhaseMetrics] = {}
        self.pipeline_metrics: List[Dict[str, Any]] = []
        self.lock = Lock()
        
        # Ensure logs directory exists
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def record_agent_call(
        self,
        agent_id: str,
        duration: float,
        success: bool = True
    ):
        """Record an agent call"""
        with self.lock:
            if agent_id not in self.agent_metrics:
                self.agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id)
            self.agent_metrics[agent_id].record_call(duration, success)
    
    def record_phase_execution(
        self,
        phase_name: str,
        duration: float
    ):
        """Record a phase execution"""
        with self.lock:
            if phase_name not in self.phase_metrics:
                self.phase_metrics[phase_name] = PhaseMetrics(phase_name=phase_name)
            self.phase_metrics[phase_name].record_execution(duration)
    
    def record_pipeline_execution(
        self,
        item_id: str,
        verdict: str,
        total_time: float,
        phase_times: Dict[str, float],
        success: bool = True
    ):
        """Record a complete pipeline execution"""
        with self.lock:
            record = {
                "item_id": item_id,
                "verdict": verdict,
                "total_time": total_time,
                "phase_times": phase_times,
                "success": success,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.pipeline_metrics.append(record)
            
            # Keep only last 1000 records in memory
            if len(self.pipeline_metrics) > 1000:
                self.pipeline_metrics = self.pipeline_metrics[-1000:]
            
            # Write to log file
            self._write_to_log(record)
    
    def _write_to_log(self, record: Dict[str, Any]):
        """Write metrics record to log file"""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            # Silently fail if logging fails
            pass
    
    def get_agent_metrics(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for a specific agent or all agents"""
        with self.lock:
            if agent_id:
                if agent_id not in self.agent_metrics:
                    return {}
                metrics = self.agent_metrics[agent_id]
                return {
                    "agent_id": metrics.agent_id,
                    "call_count": metrics.call_count,
                    "average_time": metrics.average_time,
                    "min_time": metrics.min_time if metrics.min_time != float('inf') else 0.0,
                    "max_time": metrics.max_time,
                    "success_count": metrics.success_count,
                    "error_count": metrics.error_count,
                    "success_rate": metrics.success_rate,
                    "last_call_time": metrics.last_call_time
                }
            else:
                return {
                    agent_id: {
                        "call_count": m.call_count,
                        "average_time": m.average_time,
                        "min_time": m.min_time if m.min_time != float('inf') else 0.0,
                        "max_time": m.max_time,
                        "success_count": m.success_count,
                        "error_count": m.error_count,
                        "success_rate": m.success_rate,
                        "last_call_time": m.last_call_time
                    }
                    for agent_id, m in self.agent_metrics.items()
                }
    
    def get_phase_metrics(self, phase_name: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for a specific phase or all phases"""
        with self.lock:
            if phase_name:
                if phase_name not in self.phase_metrics:
                    return {}
                metrics = self.phase_metrics[phase_name]
                return {
                    "phase_name": metrics.phase_name,
                    "execution_count": metrics.execution_count,
                    "average_time": metrics.average_time,
                    "min_time": metrics.min_time if metrics.min_time != float('inf') else 0.0,
                    "max_time": metrics.max_time,
                    "last_execution": metrics.last_execution
                }
            else:
                return {
                    phase_name: {
                        "execution_count": m.execution_count,
                        "average_time": m.average_time,
                        "min_time": m.min_time if m.min_time != float('inf') else 0.0,
                        "max_time": m.max_time,
                        "last_execution": m.last_execution
                    }
                    for phase_name, m in self.phase_metrics.items()
                }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get overall system performance summary"""
        with self.lock:
            # Calculate totals
            total_pipelines = len(self.pipeline_metrics)
            total_agent_calls = sum(m.call_count for m in self.agent_metrics.values())
            total_phase_executions = sum(m.execution_count for m in self.phase_metrics.values())
            
            # Calculate averages
            if total_pipelines > 0:
                avg_pipeline_time = sum(r["total_time"] for r in self.pipeline_metrics) / total_pipelines
                verdict_distribution = defaultdict(int)
                for r in self.pipeline_metrics:
                    verdict_distribution[r.get("verdict", "UNSURE")] += 1
            else:
                avg_pipeline_time = 0.0
                verdict_distribution = {}
            
            # Find slowest agents
            slowest_agents = sorted(
                self.agent_metrics.items(),
                key=lambda x: x[1].average_time,
                reverse=True
            )[:5]
            
            # Find slowest phases
            slowest_phases = sorted(
                self.phase_metrics.items(),
                key=lambda x: x[1].average_time,
                reverse=True
            )[:5]
            
            return {
                "total_pipelines_executed": total_pipelines,
                "total_agent_calls": total_agent_calls,
                "total_phase_executions": total_phase_executions,
                "average_pipeline_time": avg_pipeline_time,
                "verdict_distribution": dict(verdict_distribution),
                "slowest_agents": [
                    {
                        "agent_id": agent_id,
                        "average_time": metrics.average_time,
                        "call_count": metrics.call_count
                    }
                    for agent_id, metrics in slowest_agents
                ],
                "slowest_phases": [
                    {
                        "phase_name": phase_name,
                        "average_time": metrics.average_time,
                        "execution_count": metrics.execution_count
                    }
                    for phase_name, metrics in slowest_phases
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def reset(self):
        """Reset all metrics (useful for testing)"""
        with self.lock:
            self.agent_metrics.clear()
            self.phase_metrics.clear()
            self.pipeline_metrics.clear()


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create the global metrics collector"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def reset_metrics_collector():
    """Reset the global metrics collector (for testing)"""
    global _metrics_collector
    _metrics_collector = None


