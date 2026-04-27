"""RBAC (Role-Based Access Control) SQLAlchemy models."""
from __future__ import annotations
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Permission(Base, TimestampMixin):
    """权限/菜单表"""
    __tablename__ = "sys_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    permission_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    type: Mapped[str] = mapped_column(String(10), nullable=False, default="menu")
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sys_permissions.id", ondelete="CASCADE")
    )
    path: Mapped[Optional[str]] = mapped_column(String(200))
    component: Mapped[Optional[str]] = mapped_column(String(200))
    icon: Mapped[Optional[str]] = mapped_column(String(50), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    visible: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(20), default="active")

    # Self-referential relationship for tree structure
    parent: Mapped[Optional[Permission]] = relationship(
        "Permission", remote_side="Permission.id", back_populates="children", lazy="selectin"
    )
    children: Mapped[list[Permission]] = relationship(
        "Permission", back_populates="parent", lazy="selectin"
    )

    # Many-to-many with Role
    roles: Mapped[list[Role]] = relationship(
        "Role", secondary="sys_role_permissions", back_populates="permissions", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, code='{self.permission_code}', type='{self.type}')>"


class Role(Base, TimestampMixin):
    """角色表"""
    __tablename__ = "sys_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    role_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(20), default="active")

    # Many-to-many with Permission
    permissions: Mapped[list[Permission]] = relationship(
        "Permission", secondary="sys_role_permissions", back_populates="roles", lazy="selectin"
    )

    # Many-to-many with User
    users: Mapped[list[User]] = relationship(
        "User", secondary="sys_user_roles", back_populates="roles", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, code='{self.role_code}', name='{self.name}')>"


class UserRole(Base):
    """用户-角色关联表"""
    __tablename__ = "sys_user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sys_users.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sys_roles.id", ondelete="CASCADE"), nullable=False
    )

    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


class RolePermission(Base):
    """角色-权限关联表"""
    __tablename__ = "sys_role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sys_roles.id", ondelete="CASCADE"), nullable=False
    )
    permission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sys_permissions.id", ondelete="CASCADE"), nullable=False
    )

    def __repr__(self) -> str:
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"
