"""Application factory for BiztelAI Manufacturing SOP Copilot Backend."""

import os
import socket
from typing import Optional
from flask import Flask, request
from app.config import Config, get_config
from app.extensions import db, migrate, jwt, cors, limiter
from app.utils.logging import configure_logging, setup_request_logging
from app.utils.errors import register_error_handlers

# Prime DNS cache on Windows for Neon cloud PostgreSQL pooler
try:
    socket.getaddrinfo("ep-noisy-bonus-b3o3sjfv-pooler.c-4.ap-southeast-1.aws.neon.tech", 5432, socket.AF_INET)
    socket.getaddrinfo("electric-lynx-187247.upstash.io", 6379, socket.AF_INET)
except Exception:
    pass


def create_app(config_name: Optional[str] = None) -> Flask:
    """Construct and configure the Flask core application."""
    app = Flask(__name__)

    # Load configuration
    cfg = get_config(config_name)
    app.config.from_object(cfg)

    # Allow dynamic environment override for database if passed via environment (unless in testing)
    if not cfg.TESTING and os.getenv("DATABASE_URL"):
        app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
        # For sqlite, remove postgres specific engine pool options
        if "sqlite" in os.getenv("DATABASE_URL"):
            app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}

    # Initialize structured JSON logging
    configure_logging(app.config.get("LOG_LEVEL", "INFO"))
    setup_request_logging(app)

    # Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Configure CORS to allow requests from any origin (e.g., localhost, LAN IPs, mobile devices)
    cors.init_app(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=True,
        allow_headers=["*"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    )

    @app.after_request
    def set_cors_headers(response):
        origin = request.headers.get("Origin")
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        else:
            response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Accept"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        return response

    # Register centralized exception handlers
    register_error_handlers(app)

    # Register API Blueprints
    from app.api import register_blueprints
    register_blueprints(app)

    # Create storage directory if missing
    storage_path = app.config.get("DOCUMENT_STORAGE_PATH")
    if storage_path:
        try:
            os.makedirs(storage_path, exist_ok=True)
        except (PermissionError, OSError):
            pass

    @app.shell_context_processor
    def make_shell_context():
        import app.models as models
        return {"db": db, **{k: getattr(models, k) for k in dir(models) if not k.startswith("_")}}

    return app
