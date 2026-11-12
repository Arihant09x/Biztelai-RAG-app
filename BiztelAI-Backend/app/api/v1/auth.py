"""Authentication API routes."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from pydantic import ValidationError as PydanticValidationError
from app.api.deps import get_current_user
from app.constants import AuditAction
from app.schemas.auth import TokenRefreshRequest, UserLoginRequest, UserRegisterRequest
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.utils.errors import ValidationError

auth_bp = Blueprint("auth", __name__)
auth_service = AuthService()


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    """Register a new user account."""
    raw_data = request.get_json() or {}
    try:
        req = UserRegisterRequest.model_validate(raw_data)
    except PydanticValidationError as e:
        raise ValidationError("Registration validation failed.", details=e.errors())

    user = auth_service.register_user(req)
    AuditService.log_event(action=AuditAction.AUTH_REGISTER.value, user_id=str(user.id), details={"email": user.email})

    return jsonify({
        "success": True,
        "message": "User registered successfully.",
        "data": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.name if user.role else "operator",
        },
    }), 201


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """Authenticate with email and password and receive JWT tokens."""
    raw_data = request.get_json() or {}
    try:
        req = UserLoginRequest.model_validate(raw_data)
    except PydanticValidationError as e:
        raise ValidationError("Login validation failed.", details=e.errors())

    user, token_res = auth_service.authenticate_user(req.email, req.password)
    AuditService.log_event(action=AuditAction.AUTH_LOGIN.value, user_id=str(user.id))

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "data": token_res.model_dump(),
    }), 200


@auth_bp.route("/auth/refresh", methods=["POST"])
def refresh():
    """Exchange a valid refresh token for a fresh token pair."""
    raw_data = request.get_json() or {}
    try:
        req = TokenRefreshRequest.model_validate(raw_data)
    except PydanticValidationError as e:
        raise ValidationError("Token refresh validation failed.", details=e.errors())

    token_str = req.refresh_token or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token_str:
        raise ValidationError("Refresh token must be provided in body or Authorization header.")

    token_res = auth_service.refresh_user_token(token_str)
    return jsonify({
        "success": True,
        "data": token_res.model_dump(),
    }), 200


@auth_bp.route("/auth/logout", methods=["POST"])
@jwt_required()
def logout():
    """Invalidate or log user session exit."""
    user_id = get_jwt_identity()
    AuditService.log_event(action=AuditAction.AUTH_LOGOUT.value, user_id=user_id)
    return jsonify({
        "success": True,
        "message": "Logged out successfully.",
    }), 200


@auth_bp.route("/auth/me", methods=["GET"])
@jwt_required()
def me():
    """Retrieve current authenticated user profile."""
    user = get_current_user()
    return jsonify({
        "success": True,
        "data": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "department": user.department,
            "role": user.role.name if user.role else "operator",
            "is_active": user.is_active,
            "is_supervisor": user.is_supervisor,
            "is_admin": user.is_admin,
        },
    }), 200

