"""
FastAPI REST API for Multi-Agent Fake News Detection System
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uvicorn
import os

from orchestrator import Orchestrator
from fake_news_categorizer import FakeNewsCategorizer
from storage import get_storage
from agents import URLCrawlerAgent
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

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Global instances
orchestrator = Orchestrator()
categorizer = FakeNewsCategorizer()
storage = get_storage()
url_crawler = URLCrawlerAgent()

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
    """Root endpoint - serve web interface"""
    static_file = os.path.join(static_dir, "index.html")
    if os.path.exists(static_file):
        return FileResponse(static_file)
    return {
        "message": "Multi-Agent Fake News Detection API",
        "version": "1.0.0",
        "endpoints": {
            "POST /analyze": "Analyze a news item",
            "POST /analyze-url": "Analyze news from URL",
            "GET /recent-checks": "Get recent checks",
            "GET /weekly-top": "Get weekly top checked",
            "GET /statistics": "Get pipeline statistics",
            "GET /health": "Health check",
            "GET /metrics/summary": "Get overall metrics summary",
            "GET /metrics/agents": "Get agent metrics",
            "GET /metrics/phases": "Get phase metrics",
            "GET /training/analyze": "Analyze agent performance",
            "GET /training/report": "Get training report",
            "POST /training/train/{agent_id}": "Train an agent",
            "GET /training/adjustments/{agent_id}": "Get agent adjustments"
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


@app.get("/training/analyze")
async def analyze_agent_performance():
    """Analyze agent performance and identify underperformers"""
    try:
        from agent_trainer import get_agent_trainer
        trainer = get_agent_trainer()
        analysis = trainer.analyze_agent_performance()
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/training/report")
async def get_training_report():
    """Get comprehensive training report"""
    try:
        from agent_trainer import get_agent_trainer
        trainer = get_agent_trainer()
        report = trainer.get_training_report()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/training/train/{agent_id}")
async def train_agent(agent_id: str):
    """Apply training to a specific agent"""
    try:
        from agent_trainer import get_agent_trainer
        trainer = get_agent_trainer()
        analysis = trainer.analyze_agent_performance()
        
        # Find recommendations for this agent
        recommendations = analysis.get("recommendations", {}).get(agent_id)
        if not recommendations:
            raise HTTPException(
                status_code=404,
                detail=f"No training recommendations found for agent {agent_id}"
            )
        
        # Apply training
        result = trainer.apply_training(agent_id, recommendations)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/training/adjustments/{agent_id}")
async def get_agent_adjustments(agent_id: str):
    """Get current adjustments for an agent"""
    try:
        from agent_trainer import get_agent_trainer
        trainer = get_agent_trainer()
        adjustments = trainer.get_agent_adjustments(agent_id)
        return {"agent_id": agent_id, "adjustments": adjustments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-url")
async def analyze_url(request: Dict[str, Any]):
    """
    Analyze news from URL
    Fetches the URL, extracts content, and analyzes it
    Expected body: {"url": "https://..."}
    """
    try:
        # Extract URL from request
        if not isinstance(request, dict):
            raise HTTPException(status_code=400, detail="Invalid request format")
        
        url = request.get("url")
        if not url or not isinstance(url, str) or not url.strip():
            raise HTTPException(status_code=400, detail="URL parameter is required and must be a non-empty string")
        
        url = url.strip()
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Request parsing error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    try:
        # Add timestamp to URL to prevent caching issues
        # This ensures each analysis is fresh, even for the same URL
        import time
        cache_buster = int(time.time() * 1000)  # milliseconds
        logging.info(f"Analyzing URL: {url} (cache_buster: {cache_buster})")
        
        # Fetch content from URL
        news_item = url_crawler.fetch_news(url=url)
        
            # Check for fact-check result
            fact_check = news_item.get("fact_check")
        
        # If fact-check result exists, use it directly with high priority
        if fact_check and fact_check.get("is_fact_check"):
            # Fact-check sites are authoritative - use their verdict directly
            verdict = fact_check.get("verdict", "UNSURE")
            # Fact-check sites are highly reliable - use high confidence
            confidence = fact_check.get("confidence", 0.90)
            # Ensure minimum confidence for fact-check results
            if verdict == "FAKE" or verdict == "REAL":
                confidence = max(confidence, 0.90)  # Minimum 90% for fact-check results
            
            
            # Still categorize if fake
            categorization = categorizer.categorize(
                item=news_item,
                analyses={},
                verdict=verdict,
                confidence=confidence,
                fact_check_result=fact_check  # Pass fact-check info for special handling
            )
            
            result = {
                "status": "completed",
                "item": news_item,
                "verdict": verdict,  # MUST be "FAKE" for fake news
                "confidence": confidence,  # This is confidence in the verdict, not "realness"
                "is_fake": (verdict == "FAKE"),  # CRITICAL: Set is_fake based on verdict
                "fact_check_used": True,
                "fact_check_site": fact_check.get("site_name"),
                "fact_check_rating": fact_check.get("rating"),
                "processing_time": 0.1,  # Fast because fact-check already done
                "phases": {
                    "fact_check": fact_check
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            result.update(categorization)
            
            # Ensure is_fake is set correctly based on verdict
            result["is_fake"] = (verdict == "FAKE")
            result["verdict"] = verdict
            
            # Save to storage
            storage.add_check(result)
            return _sanitize_for_json(result)
        
        # Process through pipeline (normal flow)
        result = orchestrator.process_news_item(news_item)
        
        # Categorize if fake
        verdict = result.get("verdict", "UNSURE")
        confidence = result.get("confidence", 0.5)
        
        categorization = categorizer.categorize(
            item=result.get("item", {}),
            analyses=result.get("phases", {}),
            verdict=verdict,
            confidence=confidence
        )
        
        # Combine results
        final_result = {
            **result,
            **categorization
        }
        
        # CRITICAL: Ensure is_fake is set correctly based on verdict
        final_result["is_fake"] = (verdict == "FAKE")
        
        # Save to storage
        storage.add_check(final_result)
        
        # Sanitize for JSON
        safe_result = _sanitize_for_json(final_result)
        return safe_result
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logging.error("Analyze URL error: %s", e, exc_info=True)
        traceback.print_exc()
        # Return more detailed error for debugging
        error_detail = f"Processing error: {str(e)}"
        if hasattr(e, '__traceback__'):
            import traceback as tb
            error_detail += f"\nTraceback: {''.join(tb.format_tb(e.__traceback__))}"
        raise HTTPException(status_code=500, detail=error_detail)


@app.get("/recent-checks")
async def get_recent_checks(limit: int = 5):
    """Get most recent news checks"""
    try:
        checks = storage.get_recent_checks(limit=limit)
        # Format for frontend
        formatted_checks = [
            {
                "title": check.get("headline", ""),
                "url": check.get("link", ""),
                "verdict": check.get("verdict", "UNSURE"),
                "confidence": check.get("confidence", 0.0),
                "timestamp": check.get("timestamp", "")
            }
            for check in checks
        ]
        return {"recent": formatted_checks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/weekly-top")
async def get_weekly_top(limit: int = 5):
    """Get most checked URLs this week"""
    try:
        top_urls = storage.get_weekly_top(limit=limit)
        # Format for frontend
        formatted_top = [
            {
                "title": item.get("headline", ""),
                "url": item.get("url", ""),
                "count": item.get("count", 0),
                "verdict": item.get("verdict", "UNSURE")
            }
            for item in top_urls
        ]
        return {"top": formatted_top}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class FeedbackRequest(BaseModel):
    item_id: str = Field(..., description="News item ID")
    feedback: str = Field(..., min_length=1, max_length=500, description="User feedback (max 500 characters)")
    timestamp: Optional[str] = Field(None, description="Feedback timestamp")


@app.post("/feedback")
async def submit_feedback(feedback_request: FeedbackRequest):
    """Submit user feedback for reinforcement learning"""
    try:
        # Save feedback to storage
        feedback_record = storage.add_feedback(
            item_id=feedback_request.item_id,
            feedback=feedback_request.feedback,
            timestamp=feedback_request.timestamp or datetime.utcnow().isoformat()
        )
        
        # Process feedback through Reinforcement Agent
        # Find the original analysis result for this item
        # We'll use the feedback to calculate reward and update RL system
        try:
            # Get the original result from pipeline_results if available
            # Otherwise, we'll use the feedback text to infer ground truth
            rl_data = {
                "state": {
                    "item_id": feedback_request.item_id,
                    "feedback": feedback_request.feedback
                },
                "action": "process_feedback",
                "reward": None  # Will be calculated based on feedback sentiment
            }
            
            # Process through Reinforcement Agent
            rl_result = orchestrator.rla.process(rl_data)
            
            # Also send to Optimizer Agent for weight adjustments
            optimizer_data = {
                "performance_metrics": {
                    "user_feedback": feedback_request.feedback,
                    "item_id": feedback_request.item_id
                },
                "meta_feedback": {
                    "feedback_text": feedback_request.feedback,
                    "timestamp": feedback_record["timestamp"]
                }
            }
            optimizer_result = orchestrator.oa.process(optimizer_data)
            
            # Calculate reward from feedback
            reward = orchestrator.rla._calculate_reward_from_feedback(feedback_request.feedback)
            
            return {
                "status": "success",
                "message": "Feedback received and processed for system learning",
                "feedback_id": feedback_record["id"],
                "rl_result": rl_result,
                "optimizer_result": optimizer_result,
                "calculated_reward": reward,
                "processed_at": datetime.utcnow().isoformat()
            }
        except Exception as rl_error:
            # Log RL processing error but don't fail the request
            logging.error(f"RL processing error (feedback still saved): {rl_error}", exc_info=True)
            return {
                "status": "success",
                "message": "Feedback received and saved",
                "feedback_id": feedback_record["id"],
                "note": "RL processing encountered an error, but feedback was saved",
                "error": str(rl_error)
            }
            
    except Exception as e:
        logging.error(f"Feedback submission error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing feedback: {str(e)}")


@app.get("/feedbacks")
async def get_feedbacks(limit: int = 20):
    """Get recent user feedbacks"""
    try:
        # Use storage's internal method to get feedbacks
        import json
        import os
        storage_file = "logs/news_checks.json"
        if not os.path.exists(storage_file):
            return {"feedbacks": [], "total": 0, "returned": 0}
        
        with open(storage_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        feedbacks = data.get("feedbacks", [])
        # Return most recent feedbacks
        recent_feedbacks = feedbacks[-limit:][::-1]  # Reverse to show newest first
        return {
            "feedbacks": recent_feedbacks,
            "total": len(feedbacks),
            "returned": len(recent_feedbacks)
        }
    except Exception as e:
        logging.error(f"Error getting feedbacks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/feedbacks/stats")
async def get_feedback_stats():
    """Get feedback statistics"""
    try:
        import json
        import os
        storage_file = "logs/news_checks.json"
        if not os.path.exists(storage_file):
            return {"total_feedbacks": 0, "sentiment": {"positive": 0, "negative": 0, "neutral": 0}, "processed_by_rl": False}
        
        with open(storage_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        feedbacks = data.get("feedbacks", [])
        
        # Calculate statistics
        total = len(feedbacks)
        
        # Analyze sentiment (simple keyword-based)
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        positive_words = ["doğru", "haklı", "başarılı", "iyi", "güzel", "mükemmel", "correct", "right", "accurate"]
        negative_words = ["yanlış", "hatalı", "eksik", "yetersiz", "kötü", "başarısız", "wrong", "incorrect", "bad"]
        
        for feedback in feedbacks:
            feedback_text = feedback.get("feedback", "").lower()
            pos_count = sum(1 for word in positive_words if word in feedback_text)
            neg_count = sum(1 for word in negative_words if word in feedback_text)
            
            if pos_count > neg_count:
                positive_count += 1
            elif neg_count > pos_count:
                negative_count += 1
            else:
                neutral_count += 1
        
        return {
            "total_feedbacks": total,
            "sentiment": {
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count
            },
            "processed_by_rl": total > 0  # All feedbacks are processed by RL
        }
    except Exception as e:
        logging.error(f"Error getting feedback stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

