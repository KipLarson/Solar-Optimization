"""Progress tracking utilities"""
from typing import Dict, Any
import json
import redis
from app.core.config import settings


def update_task_progress(task_id: str, progress: int, message: str, state: str = "PROCESSING"):
    """
    Update task progress in Redis.
    
    Args:
        task_id: Task ID
        progress: Progress percentage (0-100)
        message: Progress message
        state: Task state (PROCESSING, COMPLETED, FAILED)
    """
    try:
        redis_client = redis.from_url(settings.redis_url)
        progress_data = {
            "status": state.lower(),
            "progress": progress,
            "message": message
        }
        redis_client.setex(
            f"task_progress:{task_id}",
            3600,  # 1 hour TTL
            json.dumps(progress_data)
        )
    except Exception as e:
        # Fail silently - progress tracking is not critical
        pass


def get_task_progress(task_id: str) -> Dict[str, Any]:
    """
    Get task progress from Redis.
    
    Args:
        task_id: Task ID
        
    Returns:
        Dictionary with progress information, or None if not found
    """
    try:
        redis_client = redis.from_url(settings.redis_url)
        progress_json = redis_client.get(f"task_progress:{task_id}")
        if progress_json:
            return json.loads(progress_json)
        return None
    except Exception:
        return None
