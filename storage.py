"""
Simple file-based storage for recent checks and statistics
"""
import json
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict


class NewsStorage:
    """Simple JSON-based storage for news checks"""
    
    def __init__(self, storage_file: str = "logs/news_checks.json"):
        self.storage_file = storage_file
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self):
        """Create storage file if it doesn't exist"""
        os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
        if not os.path.exists(self.storage_file):
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump({"checks": [], "url_counts": {}, "feedbacks": []}, f, ensure_ascii=False)
    
    def _load(self) -> Dict[str, Any]:
        """Load data from storage"""
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure feedbacks key exists for backward compatibility
                if "feedbacks" not in data:
                    data["feedbacks"] = []
                return data
        except Exception:
            return {"checks": [], "url_counts": {}, "feedbacks": []}
    
    def _save(self, data: Dict[str, Any]):
        """Save data to storage"""
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_check(self, result: Dict[str, Any]):
        """Add a news check result"""
        try:
            data = self._load()
            
            # Prepare check record with safe defaults
            item = result.get("item", {})
            check_record = {
                "id": item.get("id") or f"check-{datetime.utcnow().isoformat().replace(':', '-')}",
                "headline": item.get("headline", "") or item.get("title", "") or "Başlıksız",
                "link": item.get("link", "") or item.get("url", "") or "",
                "verdict": result.get("verdict", "UNSURE"),
                "confidence": float(result.get("confidence", 0.0)),
                "categories": result.get("categories", {}),
                "primary_category": result.get("primary_category"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Ensure categories is a dict (not None)
            if not isinstance(check_record["categories"], dict):
                check_record["categories"] = {}
            
            # Add to checks
            data["checks"].append(check_record)
            
            # Update URL count
            url = check_record["link"]
            if url:
                if url not in data["url_counts"]:
                    data["url_counts"][url] = {
                        "count": 0,
                        "first_seen": check_record["timestamp"],
                        "headline": check_record["headline"]
                    }
                data["url_counts"][url]["count"] += 1
            
            # Keep only last 1000 checks
            if len(data["checks"]) > 1000:
                data["checks"] = data["checks"][-1000:]
            
            self._save(data)
        except Exception as e:
            # Log error but don't fail the request
            import logging
            logging.error(f"Storage error in add_check: {e}", exc_info=True)
            # Continue without saving - don't break the API response
            pass
    
    def get_recent_checks(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most recent checks"""
        data = self._load()
        checks = data.get("checks", [])
        return checks[-limit:][::-1]  # Reverse to show newest first
    
    def get_weekly_top(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most checked URLs this week"""
        data = self._load()
        checks = data.get("checks", [])
        
        # Filter checks from last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_checks = [
            c for c in checks
            if datetime.fromisoformat(c["timestamp"].replace("Z", "+00:00")) > week_ago
        ]
        
        # Count URLs
        url_counts = defaultdict(int)
        url_info = {}
        for check in recent_checks:
            url = check.get("link", "")
            if url:
                url_counts[url] += 1
                if url not in url_info:
                    url_info[url] = {
                        "headline": check.get("headline", ""),
                        "verdict": check.get("verdict", "UNSURE")
                    }
        
        # Sort by count and return top N
        sorted_urls = sorted(url_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return [
            {
                "url": url,
                "count": count,
                "headline": url_info[url]["headline"],
                "verdict": url_info[url]["verdict"]
            }
            for url, count in sorted_urls
        ]
    
    def add_feedback(self, item_id: str, feedback: str, timestamp: str = None) -> Dict[str, Any]:
        """Add user feedback for a news item"""
        try:
            data = self._load()
            
            if timestamp is None:
                timestamp = datetime.utcnow().isoformat()
            
            feedback_record = {
                "id": f"feedback-{datetime.utcnow().isoformat().replace(':', '-')}",
                "item_id": item_id,
                "feedback": feedback,
                "timestamp": timestamp
            }
            
            # Add to feedbacks
            if "feedbacks" not in data:
                data["feedbacks"] = []
            data["feedbacks"].append(feedback_record)
            
            # Keep only last 500 feedbacks
            if len(data["feedbacks"]) > 500:
                data["feedbacks"] = data["feedbacks"][-500:]
            
            self._save(data)
            return feedback_record
        except Exception as e:
            import logging
            logging.error(f"Storage error in add_feedback: {e}", exc_info=True)
            raise


# Global storage instance
_storage_instance = None

def get_storage() -> NewsStorage:
    """Get or create storage instance"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = NewsStorage()
    return _storage_instance

