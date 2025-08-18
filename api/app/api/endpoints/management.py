"""
Monitoring endpoints.
"""
import time
from fastapi import APIRouter
from typing import Dict

# Global metrics dictionary
metrics = {
    "start_time": time.time(),
    "processed_count": 0,
    "success_count": 0,
    "error_count": 0,
    "processing_times": [],
    "last_minute": {},
    "last_hour": {},
    "last_day": {},
    "active_workers": 0,
    "queue_size": 0,
}

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return {"status": "ok", "uptime": time.time() - metrics["start_time"]}


@router.get("/metrics")
async def get_metrics():
    """
    Get service metrics.
    
    Returns:
        Service metrics
    """
    uptime = time.time() - metrics["start_time"]
    avg_time = sum(metrics["processing_times"]) / max(1, len(metrics["processing_times"]))
    
    return {
        "uptime": uptime,
        "processed": metrics["processed_count"],
        "success_rate": metrics["success_count"] / max(1, metrics["processed_count"]) * 100,
        "avg_processing_time": avg_time,
        "active_workers": metrics["active_workers"],
        "queue_size": metrics["queue_size"],
        "last_minute": metrics["last_minute"],
        "last_hour": metrics["last_hour"],
        "last_day": metrics["last_day"],
    }


def increment_metric(name: str, value: int = 1):
    """
    Increment a metric.
    
    Args:
        name: Metric name
        value: Value to increment by
    """
    metrics[name] += value


def update_processing_time(time_taken: float):
    """
    Update processing time metrics.
    
    Args:
        time_taken: Processing time in seconds
    """
    metrics["processing_times"].append(time_taken)
    
    # Keep only the last 100 times
    if len(metrics["processing_times"]) > 100:
        metrics["processing_times"] = metrics["processing_times"][-100:]


def record_activity(action: str):
    """
    Record an activity in the time-based metrics.
    
    Args:
        action: Activity name
    """
    # Update last minute
    metrics["last_minute"][action] = metrics["last_minute"].get(action, 0) + 1
    
    # Update last hour
    metrics["last_hour"][action] = metrics["last_hour"].get(action, 0) + 1
    
    # Update last day
    metrics["last_day"][action] = metrics["last_day"].get(action, 0) + 1


def reset_minute_metrics():
    """Reset the last minute metrics."""
    metrics["last_minute"] = {}


def reset_hour_metrics():
    """Reset the last hour metrics."""
    metrics["last_hour"] = {}


def reset_day_metrics():
    """Reset the last day metrics."""
    metrics["last_day"] = {}