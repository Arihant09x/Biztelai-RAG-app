"""User, Role, and Permission models for role-based access control (RBAC)."""

from typing import List
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table, UniqueConstraint
from sqlalchemy.orm import relationship
from app.extensions import db
from app.models.base import BaseModel, GUID
from app.constants import UserRole


role_permissions = Table(
    "role_permissions",
    db.metadata,
    Column("role_id", GUID, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", GUID, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Role(BaseModel):
    """User authorization role."""
    __tablename__ = "roles"

    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    permissions = relationship("Permission", secondary=role_permissions, backref="roles", lazy="joined")
    users = relationship("User", back_populates="role")

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class Permission(BaseModel):
    """Fine-grained application permission."""
    __tablename__ = "permissions"

    code = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<Permission {self.code}>"


class User(BaseModel):
    """Application user account."""
    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(120), nullable=False)
    department = Column(String(100), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    role_id = Column(GUID, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False, index=True)
    role = relationship("Role", back_populates="users", lazy="joined")

    documents = relationship("Document", back_populates="creator", lazy="dynamic")
    conversations = relationship("Conversation", back_populates="user", lazy="dynamic")

    def has_permission(self, permission_code: str) -> bool:
        """Check if user role has the specified permission code."""
        if not self.role:
            return False
        return any(p.code == permission_code for p in self.role.permissions)

    @property
    def is_admin(self) -> bool:
        return bool(self.role and self.role.name == UserRole.ADMIN.value)

    @property
    def is_supervisor(self) -> bool:
        return bool(self.role and self.role.name in (UserRole.ADMIN.value, UserRole.SUPERVISOR.value))

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role.name if self.role else 'NoRole'})>"

