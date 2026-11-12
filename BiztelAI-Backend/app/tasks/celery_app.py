"""Celery application instance configured with Upstash Redis TLS support."""

import os
import ssl
import socket
from celery import Celery
from app.config import Config

# Prime DNS cache on Windows for Neon cloud pooler and Upstash Redis
for _host, _port in [
    ("ep-noisy-bonus-b3o3sjfv-pooler.c-4.ap-southeast-1.aws.neon.tech", 5432),
    ("electric-lynx-187247.upstash.io", 6379),
]:
    try:
        socket.getaddrinfo(_host, _port, socket.AF_INET)
    except Exception:
        pass


def make_celery(app_name: str = "biztelai_sop") -> Celery:
    """Instantiate and configure Celery worker with Upstash Redis SSL compatibility."""
    app_env = os.getenv("APP_ENV", "development").lower()
    is_testing = app_env == "testing"

    broker_url = "memory://" if is_testing else os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    result_backend = "cache+memory://" if is_testing else os.getenv("CELERY_RESULT_BACKEND", broker_url)

    celery_app = Celery(
        app_name,
        broker=broker_url,
        backend=result_backend,
        include=["app.tasks.ingestion_tasks"],
    )

    conf: dict = {
        "task_serializer": "json",
        "accept_content": ["json"],
        "result_serializer": "json",
        "timezone": "UTC",
        "enable_utc": True,
        "task_track_started": True,
        "task_time_limit": 600,  # 10 minutes max per task
        "task_soft_time_limit": 540,
        "worker_prefetch_multiplier": 1,
        "task_acks_late": True,
        "task_always_eager": is_testing,
    }

    # Upstash Redis requires TLS / SSL support
    if broker_url.startswith("rediss://") or "upstash.io" in broker_url:
        ssl_options = {"ssl_cert_reqs": ssl.CERT_NONE}
        conf["broker_use_ssl"] = ssl_options
        conf["redis_backend_use_ssl"] = ssl_options

    celery_app.conf.update(conf)
    return celery_app


celery = make_celery()
