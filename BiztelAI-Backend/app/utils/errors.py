"""Centralized exception classes and global error handlers for Flask."""

import uuid
from typing import Any, Dict, List, Optional
from flask import Flask, jsonify, request
import structlog

logger = structlog.get_logger(__name__)


class AppException(Exception):
    """Base application exception with error code and HTTP status."""
    status_code: int = 500
    error_code: str = "INTERNAL_SERVER_ERROR"

    def __init__(
        self,
        message: str = "An unexpected internal error occurred.",
        details: Optional[List[Any]] = None,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.details = details or []
        if status_code:
            self.status_code = status_code
        if error_code:
            self.error_code = error_code


class ValidationError(AppException):
    status_code = 400
    error_code = "VALIDATION_ERROR"


class AuthenticationError(AppException):
    status_code = 401
    error_code = "AUTHENTICATION_FAILED"


# Alias for compatibility
UnauthorizedError = AuthenticationError


class AuthorizationError(AppException):
    status_code = 403
    error_code = "ACCESS_DENIED"


class NotFoundError(AppException):
    status_code = 404
    error_code = "RESOURCE_NOT_FOUND"


class ConflictError(AppException):
    status_code = 409
    error_code = "RESOURCE_CONFLICT"


class RateLimitExceededError(AppException):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"


class DatabaseError(AppException):
    status_code = 500
    error_code = "DATABASE_ERROR"


class VectorSearchError(AppException):
    status_code = 500
    error_code = "VECTOR_SEARCH_ERROR"


class LLMProviderError(AppException):
    status_code = 502
    error_code = "LLM_PROVIDER_ERROR"


class IngestionError(AppException):
    status_code = 422
    error_code = "DOCUMENT_INGESTION_FAILED"


class FileUploadError(AppException):
    status_code = 400
    error_code = "INVALID_FILE_UPLOAD"


def format_error_response(
    error_code: str,
    message: str,
    details: Optional[List[Any]] = None,
    status_code: int = 500,
) -> tuple[Any, int]:
    """Uniform JSON error envelope as specified in application requirements."""
    request_id = getattr(request, "request_id", None) or str(uuid.uuid4())
    payload = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "details": details or [],
        },
        "request_id": request_id,
    }
    return jsonify(payload), status_code


def register_error_handlers(app: Flask) -> None:
    """Register centralized error handlers on the Flask app."""

    @app.errorhandler(AppException)
    def handle_app_exception(err: AppException):
        logger.warning(
            "handled_app_exception",
            error_code=err.error_code,
            message=err.message,
            status_code=err.status_code,
            request_id=getattr(request, "request_id", None),
        )
        return format_error_response(
            error_code=err.error_code,
            message=err.message,
            details=err.details,
            status_code=err.status_code,
        )

    @app.errorhandler(400)
    def handle_bad_request(err):
        return format_error_response("BAD_REQUEST", str(err.description or "Bad request"), status_code=400)

    @app.errorhandler(401)
    def handle_unauthorized(err):
        return format_error_response("UNAUTHORIZED", "Authentication credentials missing or invalid.", status_code=401)

    @app.errorhandler(403)
    def handle_forbidden(err):
        return format_error_response("FORBIDDEN", "You do not have permission to access this resource.", status_code=403)

    @app.errorhandler(404)
    def handle_not_found(err):
        return format_error_response("NOT_FOUND", "The requested endpoint or resource does not exist.", status_code=404)

    @app.errorhandler(405)
    def handle_method_not_allowed(err):
        return format_error_response("METHOD_NOT_ALLOWED", "HTTP method not allowed for this route.", status_code=405)

    @app.errorhandler(429)
    def handle_rate_limit(err):
        return format_error_response("RATE_LIMIT_EXCEEDED", "Too many requests. Please retry later.", status_code=429)

    @app.errorhandler(500)
    def handle_internal_server_error(err):
        logger.error(
            "unhandled_server_error",
            error=str(err),
            request_id=getattr(request, "request_id", None),
            exc_info=True,
        )
        # Avoid exposing raw stack traces to client
        return format_error_response(
            "INTERNAL_SERVER_ERROR",
            "An internal server error occurred. Please contact system support.",
            status_code=500,
        )

    @app.errorhandler(Exception)
    def handle_generic_exception(err: Exception):
        logger.error(
            "unhandled_exception",
            error=str(err),
            request_id=getattr(request, "request_id", None),
            exc_info=True,
        )
        return format_error_response(
            "INTERNAL_SERVER_ERROR",
            "An unexpected error occurred processing your request.",
            status_code=500,
        )

