"""Authentication service managing user registration, login, JWT token issuance, and roles."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
from app.constants import AuditAction, UserRole
from app.extensions import db
from app.models.user import Permission, Role, User
from app.schemas.auth import TokenResponse, UserRegisterRequest, UserResponse
from app.utils.errors import AuthenticationError, ConflictError, NotFoundError
from app.utils.security import hash_password, verify_password
import structlog

logger = structlog.get_logger(__name__)


class AuthService:
    """Handles user credential validation, role-based authorization, and JWT lifecycles."""

    def register_user(self, data: UserRegisterRequest) -> User:
        """Register a new user account with hashed password and assigned role."""
        # 1. Check if email already registered
        existing = User.query.filter_by(email=data.email.lower()).first()
        if existing:
            raise ConflictError(f"A user with email '{data.email}' already exists.")

        # 2. Resolve Role
        requested_role = (data.role or UserRole.OPERATOR.value).lower()
        role = Role.query.filter_by(name=requested_role).first()
        if not role:
            # Fallback to operator or create default role
            role = Role.query.filter_by(name=UserRole.OPERATOR.value).first()
            if not role:
                role = Role(name=requested_role, description=f"{requested_role.capitalize()} role")
                db.session.add(role)
                db.session.flush()

        # 3. Create user
        new_user = User(
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            department=data.department,
            role_id=role.id,
            is_active=True,
        )
        db.session.add(new_user)
        db.session.commit()

        logger.info("user_registered_successfully", user_id=str(new_user.id), email=new_user.email, role=role.name)
        return new_user

    def authenticate_user(self, email: str, password: str) -> Tuple[User, TokenResponse]:
        """Verify user credentials and issue fresh JWT access & refresh tokens."""
        user = User.query.filter_by(email=email.lower()).first()
        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password.")

        if not user.is_active:
            raise AuthenticationError("This user account has been disabled. Please contact your administrator.")

        # Create tokens
        token_response = self._generate_tokens_for_user(user)
        logger.info("user_authenticated_successfully", user_id=str(user.id), email=user.email)
        return user, token_response

    def refresh_user_token(self, refresh_token_str: str) -> TokenResponse:
        """Validate refresh token and issue new token pair."""
        try:
            decoded = decode_token(refresh_token_str)
            user_id = decoded.get("sub")
            user = User.query.get(user_id)
            if not user or not user.is_active:
                raise AuthenticationError("User associated with refresh token is invalid or inactive.")

            return self._generate_tokens_for_user(user)
        except Exception as e:
            raise AuthenticationError(f"Invalid or expired refresh token: {str(e)}")

    def _generate_tokens_for_user(self, user: User) -> TokenResponse:
        """Create access and refresh tokens with role and user claims."""
        expires_minutes = current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 30) if current_app else 30
        access_delta = timedelta(minutes=expires_minutes)
        refresh_delta = timedelta(days=14)

        additional_claims = {
            "role": user.role.name if user.role else "operator",
            "email": user.email,
            "department": user.department,
        }

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims,
            expires_delta=access_delta,
        )
        refresh_token = create_refresh_token(
            identity=str(user.id),
            additional_claims=additional_claims,
            expires_delta=refresh_delta,
        )

        user_resp = UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            department=user.department,
            role=user.role.name if user.role else "operator",
            is_active=user.is_active,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in_minutes=expires_minutes,
            user=user_resp,
        )

    def get_user_by_id(self, user_id: str) -> User:
        """Retrieve user by UUID."""
        user = User.query.get(user_id)
        if not user:
            raise NotFoundError(f"User with ID '{user_id}' not found.")
        return user

