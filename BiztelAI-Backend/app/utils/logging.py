"""Structured JSON logging configuration with correlation IDs and sensitive data masking."""

import logging
import sys
import uuid
from typing import Any, Dict
from flask import Flask, g, request
import structlog


def add_request_context(_, __, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Inject request_id, user_id, and endpoint into structured log events."""
    try:
        if request:
            event_dict["request_id"] = getattr(request, "request_id", None) or getattr(g, "request_id", None)
            event_dict["path"] = request.path
            event_dict["method"] = request.method
            if hasattr(g, "current_user") and g.current_user:
                event_dict["user_id"] = str(getattr(g.current_user, "id", ""))
    except RuntimeError:
        # Outside of Flask request context
        pass
    return event_dict


def mask_sensitive_keys(_, __, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Scrub sensitive keywords (passwords, tokens, keys) from log event dictionaries."""
    sensitive_keys = {"password", "secret", "token", "authorization", "api_key", "jwt", "key"}
    for k, v in list(event_dict.items()):
        if any(sens in k.lower() for sens in sensitive_keys) and isinstance(v, str):
            event_dict[k] = "[MASKED]"
    return event_dict


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog and standard library logging for structured JSON output."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        add_request_context,
        mask_sensitive_keys,
    ]

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)


def setup_request_logging(app: Flask) -> None:
    """Register before_request and after_request hooks for correlation ID and latency tracking."""
    import time

    @app.before_request
    def before_request():
        # Read or generate correlation Request ID
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.request_id = req_id
        g.request_id = req_id
        g.start_time = time.time()

    @app.after_request
    def after_request(response):
        # Attach correlation ID to outbound response headers
        if hasattr(request, "request_id"):
            response.headers["X-Request-ID"] = request.request_id

        # Calculate request duration
        duration_ms = None
        if hasattr(g, "start_time"):
            duration_ms = round((time.time() - g.start_time) * 1000, 2)

        # Log completion
        logger = structlog.get_logger("http_access")
        logger.info(
            "http_request_finished",
            status_code=response.status_code,
            duration_ms=duration_ms,
            content_length=response.calculate_content_length(),
        )
        return response

