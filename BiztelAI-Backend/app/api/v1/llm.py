"""LLM diagnostics and dynamic live connection testing endpoints."""

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required
from app.api.deps import supervisor_required
from app.schemas.llm import LLMStatusResponse, LLMTestConnectionRequest, LLMTestConnectionResponse
from app.services.llm.factory import get_llm_provider
from app.utils.security import mask_secret

llm_bp = Blueprint("llm", __name__)


@llm_bp.route("/llm/status", methods=["GET"])
@jwt_required()
@supervisor_required
def get_llm_status():
    """Inspect active LLM configuration and detected capabilities without leaking secrets."""
    provider = get_llm_provider()
    cfg = current_app.config

    return jsonify({
        "success": True,
        "data": {
            "provider_name": provider.provider_name,
            "api_base_url": cfg.get("LLM_API_BASE_URL"),
            "model_name": provider.model_name,
            "temperature": cfg.get("LLM_TEMPERATURE", 0.0),
            "max_tokens": cfg.get("LLM_MAX_TOKENS", 2048),
            "timeout_seconds": cfg.get("LLM_TIMEOUT_SECONDS", 45),
            "masked_api_key": mask_secret(cfg.get("LLM_API_KEY", "")),
            "capabilities": {
                "streaming_supported": True,
                "json_mode_supported": True,
                "multi_turn_history": True,
            },
        },
    }), 200


@llm_bp.route("/llm/test-connection", methods=["POST"])
@jwt_required()
@supervisor_required
def test_llm_connection():
    """Trigger dynamic test completion to verify API key validity, connectivity, and model responsiveness."""
    provider = get_llm_provider()
    result = provider.test_connection()

    status_code = 200 if result.get("success") else 502
    return jsonify({
        "success": result.get("success", False),
        "data": result,
    }), status_code

