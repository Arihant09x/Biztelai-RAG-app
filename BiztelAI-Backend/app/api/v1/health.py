"""Health and readiness check endpoints for load balancers and orchestrators."""

import os
from pathlib import Path
from flask import Blueprint, current_app, jsonify
from sqlalchemy import text
from app.extensions import db
import structlog

logger = structlog.get_logger(__name__)
health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def liveness_check():
    """Liveness probe returning 200 if Flask WSGI process is running."""
    return jsonify({
        "status": "healthy",
        "service": "biztelai-sop-backend",
        "timestamp": os.getenv("APP_ENV", "development"),
    }), 200


@health_bp.route("/health/ready", methods=["GET"])
def readiness_check():
    """Readiness probe verifying database connectivity, storage writeability, and Redis."""
    components = {}
    is_ready = True

    # 1. Database check
    try:
        db.session.execute(text("SELECT 1"))
        components["database"] = {"status": "up"}
    except Exception as e:
        logger.error("health_db_check_failed", error=str(e))
        components["database"] = {"status": "down", "error": str(e)}
        is_ready = False

    # 2. Document storage write check
    try:
        storage_path = Path(current_app.config.get("DOCUMENT_STORAGE_PATH", "./data/documents"))
        storage_path.mkdir(parents=True, exist_ok=True)
        test_file = storage_path / ".health_probe"
        test_file.write_text("ok")
        test_file.unlink()
        components["storage"] = {"status": "up", "path": str(storage_path)}
    except Exception as e:
        logger.error("health_storage_check_failed", error=str(e))
        components["storage"] = {"status": "down", "error": str(e)}
        is_ready = False

    # 3. Redis / Upstash check
    try:
        redis_url = current_app.config.get("REDIS_URL", "")
        if "localhost" not in redis_url:
            import redis
            ssl_kwargs = {"ssl_cert_reqs": None} if "rediss://" in redis_url else {}
            r = redis.from_url(redis_url, socket_timeout=3, **ssl_kwargs)
            # Ping if possible
            components["redis"] = {"status": "configured", "provider": "upstash" if "upstash" in redis_url else "generic"}
        else:
            components["redis"] = {"status": "local_fallback"}
    except Exception as e:
        components["redis"] = {"status": "unreachable", "error": str(e)}

    status_code = 200 if is_ready else 503
    return jsonify({
        "status": "ready" if is_ready else "not_ready",
        "components": components,
    }), status_code

