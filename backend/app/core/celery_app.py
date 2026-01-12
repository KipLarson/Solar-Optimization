"""Celery application configuration"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "solar_optimization",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.core.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    worker_prefetch_multiplier=1,
)
