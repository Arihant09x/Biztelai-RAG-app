"""API Blueprints registry."""

from flask import Flask
from app.api.v1.health import health_bp
from app.api.v1.auth import auth_bp
from app.api.v1.documents import documents_bp
from app.api.v1.ingestion import ingestion_bp
from app.api.v1.chat import chat_bp
from app.api.v1.procedures import procedures_bp
from app.api.v1.feedback import feedback_bp
from app.api.v1.admin import admin_bp
from app.api.v1.llm import llm_bp
from app.api.v1.swagger import swagger_bp


def register_blueprints(app: Flask) -> None:
    """Register all modular REST API blueprints under /api/v1 prefix."""
    api_prefix = "/api/v1"

    app.register_blueprint(health_bp, url_prefix=api_prefix)
    app.register_blueprint(auth_bp, url_prefix=api_prefix)
    app.register_blueprint(documents_bp, url_prefix=api_prefix)
    app.register_blueprint(ingestion_bp, url_prefix=api_prefix)
    app.register_blueprint(chat_bp, url_prefix=api_prefix)
    app.register_blueprint(procedures_bp, url_prefix=api_prefix)
    app.register_blueprint(feedback_bp, url_prefix=api_prefix)
    app.register_blueprint(admin_bp, url_prefix=api_prefix)
    app.register_blueprint(llm_bp, url_prefix=api_prefix)
    app.register_blueprint(swagger_bp, url_prefix=f"{api_prefix}/docs")
