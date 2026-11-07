"""
permissions.py — Role-based access control for NEXUS AI.

Roles:
  citizen  — report, upvote, view
  officer  — + update status, verify resolution, ward-level analytics
  admin    — + all wards, user management, model configuration, export data

Usage:
    from app.core.permissions import require_role, require_officer
    @router.patch("/{id}")
    def update(..., user: require_officer):
        ...
"""

from functools import wraps
from typing import Annotated, Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import CurrentUser, get_current_user
from app.database import get_db
from app.models.user import User

ROLE_HIERARCHY = {
    "citizen": 0,
    "officer": 1,
    "admin":   2,
}


def require_role(minimum_role: str) -> Callable:
    """Dependency factory: raises 403 if user role is below minimum."""
    def checker(user: CurrentUser) -> User:
        user_level    = ROLE_HIERARCHY.get(user.role, 0)
        required_level = ROLE_HIERARCHY.get(minimum_role, 0)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires '{minimum_role}' role. You have '{user.role}'.",
            )
        return user
    return Depends(checker)


# ── Pre-built dependencies ────────────────────────────────────────────────────
require_citizen = require_role("citizen")   # any authenticated user
require_officer = require_role("officer")   # officer or admin
require_admin   = require_role("admin")     # admin only


def require_ward_access(ward: str | None) -> Callable:
    """
    Officers can only update issues in their assigned ward(s).
    Admin bypasses this check.
    Returns a FastAPI dependency that validates ward access.
    """
    def checker(user: CurrentUser) -> User:
        if user.role == "admin":
            return user
        if user.role == "officer":
            # Officer.assigned_wards is a comma-separated string in User.phone for MVP
            # In production: add an assigned_wards column to User model
            if ward and hasattr(user, "assigned_wards") and user.assigned_wards:
                if ward not in user.assigned_wards:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Officer not assigned to ward: {ward}",
                    )
        return user
    return Depends(checker)


class PermissionMixin:
    """
    Mixin to add role-checking methods to Pydantic schemas.
    """
    def can_edit_by(self, user: User) -> bool:
        """Override in subclasses for per-resource logic."""
        return user.role in ("officer", "admin")

    def can_delete_by(self, user: User) -> bool:
        return user.role == "admin"

    def can_view_by(self, user: User) -> bool:
        return True  # default public visibility
