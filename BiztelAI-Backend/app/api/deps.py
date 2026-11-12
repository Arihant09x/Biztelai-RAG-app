"""Authentication dependencies, role guards, and request validation helpers."""

from functools import wraps
from typing import Callable, List
from flask import g, request
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request
from app.constants import UserRole
from app.models.user import User
from app.utils.errors import AuthenticationError, AuthorizationError


def get_current_user() -> User:
    """Retrieve currently authenticated User object from database."""
    verify_jwt_in_request()
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.is_active:
        raise AuthenticationError("Authenticated user account not found or deactivated.")
    g.current_user = user
    return user


def roles_required(*allowed_roles: str) -> Callable:
    """Decorator requiring the authenticated user to possess one of the allowed roles."""
    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role", "")
            # Admin always has access
            if user_role == UserRole.ADMIN.value or user_role in allowed_roles:
                g.current_user = get_current_user()
                return fn(*args, **kwargs)
            raise AuthorizationError(f"Role '{user_role}' is not authorized to access this endpoint.")
        return wrapper
    return decorator


def admin_required(fn: Callable) -> Callable:
    """Decorator restricting route to administrators only."""
    return roles_required(UserRole.ADMIN.value)(fn)


def supervisor_required(fn: Callable) -> Callable:
    """Decorator restricting route to supervisors and administrators."""
    return roles_required(UserRole.ADMIN.value, UserRole.SUPERVISOR.value)(fn)

