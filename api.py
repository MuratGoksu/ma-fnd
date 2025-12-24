"""
FastAPI REST API for Multi-Agent Fake News Detection System
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uvicorn

from orchestrator import Orchestrator
import traceback
import logging
from datetime import datetime
from collections.abc import Mapping, Iterable

app = FastAPI(
    title="Multi-Agent Fake News Detection API",
    description="REST API for the multi-agent fake news detection system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
orchestrator = Orchestrator()

def _sanitize_for_json(obj: Any) -> Any:
    """
    Ensure the object is JSON-serializable:
    - tuples/sets -> lists
    - mappings -> dict with string keys
    - other iterables -> list
    """
    # Simple types
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    # Tuples/Sets -> list
    if isinstance(obj, (tuple, set)):
        return [_sanitize_for_json(x) for x in obj]
    # Dict-like
    if isinstance(obj, Mapping):
        return {str(k): _sanitize_for_json(v) for k, v in obj.items()}
    # List-like (but not str which was handled)
    if isinstance(obj, Iterable):
        try:
            return [_sanitize_for_json(x) for x in obj]
        except Exception:
            pass
    # Fallback to string
    try:
        return str(obj)
    except Exception:
        return None

# Request/Response models
class NewsItemRequest(BaseModel):
    id: Optional[str] = None
    headline: Optional[str] = None
    text: Optional[str] = None
    link: Optional[str] = None
    image_url: Optional[str] = None
    source: Optional[str] = None


class NewsItemResponse(BaseModel):
    status: str
    item: Dict[str, Any]
    verdict: str
    confidence: float
    processing_time: float
    phases: Dict[str, Any]
    timestamp: str


class StatisticsResponse(BaseModel):
    total_processed: int
    verdict_distribution: Dict[str, int]
    average_processing_time: float
    last_processed: Optional[str]


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Multi-Agent Fake News Detection API",
        "version": "1.0.0",
        "endpoints": {
            "POST /analyze": "Analyze a news item",
            "GET /statistics": "Get pipeline statistics",
            "GET /health": "Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agents": {
            "crawler": "active",
            "source_tracker": "active",
            "preprocessing": "active",
            "visual_validator": "active",
            "textual_context": "active",
            "claim": "active",
            "challenge": "active",
            "refuter": "active",
            "judge": "active",
            "meta_evaluator": "active",
            "optimizer": "active",
            "reinforcement": "active",
            "correction": "active"
        }
    }


@app.post("/analyze")
async def analyze_news(
    item: NewsItemRequest,
    background_tasks: BackgroundTasks
):
    """
    Analyze a news item for fake news detection
    
    - **id**: Optional item ID
    - **headline**: News headline
    - **text**: News article text
    - **link**: Source URL
    - **image_url**: Optional image URL
    - **source**: Optional source name
    """
    try:
        # Convert request to dict
        # Pydantic v2: model_dump replaces dict()
        item_dict = item.model_dump(exclude_none=True)
        
        # Process through pipeline
        result = orchestrator.process_news_item(item_dict)

        # Normalize result to match NewsItemResponse even for early exits (spam/duplicate)
        normalized = _build_response_from_pipeline(result)
        
        # Sanitize for JSON / Pydantic
        safe_result = _sanitize_for_json(normalized)
        # Return raw JSON-safe dict (bypass response_model while debugging)
        return safe_result
    
    except Exception as e:
        # Return clearer error in API response
        logging.error("Analyze error: %s", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing error: {e}")


@app.post("/analyze_raw")
async def analyze_news_raw(
    item: NewsItemRequest,
):
    """
    Debug endpoint: returns raw orchestrator output without response_model validation.
    Useful to diagnose serialization/validation issues causing 500 errors.
    """
    try:
        item_dict = item.model_dump(exclude_none=True)
        result = orchestrator.process_news_item(item_dict)
        return _sanitize_for_json(result)
    except Exception as e:
        logging.error("Analyze RAW error: %s", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing error (raw): {e}")


def _build_response_from_pipeline(pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure required fields exist for NewsItemResponse even when pipeline exits early
    (e.g., status=spam or status=duplicate).
    """
    if not isinstance(pipeline_result, dict):
        # Fallback minimal structure
        return {
            "status": "error",
            "item": {},
            "verdict": "UNSURE",
            "confidence": 0.0,
            "processing_time": 0.0,
            "phases": {},
            "timestamp": datetime.utcnow().isoformat()
        }

    status = pipeline_result.get("status", "completed")
    if status == "completed":
        # Assume orchestrator already returns full structure
        return pipeline_result

    # Early exit normalization (spam/duplicate/etc.)
    item = pipeline_result.get("item") or {}
    processing_time = float(pipeline_result.get("processing_time", 0.0))

    phases: Dict[str, Any] = {}
    # Include minimal preprocessing info if available
    if status in {"spam", "duplicate"}:
        phases["preprocessing"] = {"status": status}

    return {
        "status": status,
        "item": item,
        "verdict": "UNSURE",
        "confidence": 0.0,
        "processing_time": processing_time,
        "phases": phases,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """Get pipeline statistics"""
    try:
        stats = orchestrator.get_pipeline_statistics()
        return StatisticsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_id}/state")
async def get_agent_state(agent_id: str):
    """Get state of a specific agent"""
    # This would require exposing agent states
    # For now, return placeholder
    return {
        "agent_id": agent_id,
        "status": "active",
        "note": "Agent state retrieval not fully implemented"
    }


@app.get("/metrics/summary")
async def get_metrics_summary():
    """Get overall performance metrics summary"""
    try:
        summary = orchestrator.get_metrics_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/agents")
async def get_agent_metrics(agent_id: Optional[str] = None):
    """Get metrics for all agents or a specific agent"""
    try:
        metrics = orchestrator.get_agent_metrics(agent_id)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/phases")
async def get_phase_metrics(phase_name: Optional[str] = None):
    """Get metrics for all phases or a specific phase"""
    try:
        metrics = orchestrator.get_phase_metrics(phase_name)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

