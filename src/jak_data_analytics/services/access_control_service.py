"""
JAK Data Analytics
Access Control Service

Provides centralized role-based access control (RBAC).

Important:
- This service provides permission checks.
- It does not replace authentication.
- Sensitive operations must enforce permissions on the server side.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Set

import streamlit as st


# ---------------------------------------------------------
# ROLE DEFINITIONS
# ---------------------------------------------------------

ROLE_ADMIN = "admin"
ROLE_ANALYST = "analyst"
ROLE_USER = "user"
ROLE_VIEWER = "viewer"

VALID_ROLES = {
    ROLE_ADMIN,
    ROLE_ANALYST,
    ROLE_USER,
    ROLE_VIEWER,
}


# ---------------------------------------------------------
# PERMISSION DEFINITIONS
# ---------------------------------------------------------

PERMISSIONS = {
    "users.view",
    "users.create",
    "users.update",
    "users.delete",

    "projects.view",
    "projects.create",
    "projects.update",
    "projects.delete",

    "datasets.view",
    "datasets.upload",
    "datasets.update",
    "datasets.delete",
    "datasets.export",

    "analysis.view",
    "analysis.create",
    "analysis.delete",

    "visualizations.view",
    "visualizations.create",
    "visualizations.update",
    "visualizations.delete",

    "dashboards.view",
    "dashboards.create",
    "dashboards.update",
    "dashboards.delete",
    "dashboards.share",

    "machine_learning.view",
    "machine_learning.run",

    "reports.view",
    "reports.create",
    "reports.export",
    "reports.delete",

    "connections.view",
    "connections.create",
    "connections.update",
    "connections.delete",
    "connections.test",

    "settings.view",
    "settings.update",

    "activity.view",
    "system.manage",
}


# ---------------------------------------------------------
# DEFAULT ROLE PERMISSIONS
# ---------------------------------------------------------

ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    ROLE_ADMIN: set(PERMISSIONS),

    ROLE_ANALYST: {
        "projects.view",
        "projects.create",
        "projects.update",

        "datasets.view",
        "datasets.upload",
        "datasets.update",
        "datasets.export",

        "analysis.view",
        "analysis.create",

        "visualizations.view",
        "visualizations.create",
        "visualizations.update",

        "dashboards.view",
        "dashboards.create",
        "dashboards.update",
        "dashboards.share",

        "machine_learning.view",
        "machine_learning.run",

        "reports.view",
        "reports.create",
        "reports.export",

        "connections.view",
        "connections.create",
        "connections.update",
        "connections.test",
    },

    ROLE_USER: {
        "projects.view",
        "projects.create",
        "projects.update",

        "datasets.view",
        "datasets.upload",
        "datasets.export",

        "analysis.view",
        "analysis.create",

        "visualizations.view",
        "visualizations.create",

        "dashboards.view",
        "dashboards.create",
        "dashboards.update",

        "machine_learning.view",

        "reports.view",
        "reports.create",
        "reports.export",
    },

    ROLE_VIEWER: {
        "projects.view",
        "datasets.view",
        "analysis.view",
        "visualizations.view",
        "dashboards.view",
        "reports.view",
    },
}


# ---------------------------------------------------------
# SESSION HELPERS
# ---------------------------------------------------------

def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Return the current authenticated user from session state.

    Supports common JAK session keys:
    - jak_user
    - user
    - authenticated_user
    """
    for key in (
        "jak_user",
        "user",
        "authenticated_user",
    ):
        value = st.session_state.get(key)

        if isinstance(value, dict):
            return value

    return None


def get_current_user_id() -> Optional[str]:
    """Return the current user's ID."""
    user = get_current_user()

    if not user:
        return None

    user_id = (
        user.get("id")
        or user.get("user_id")
    )

    return str(user_id) if user_id is not None else None


def get_current_user_role() -> Optional[str]:
    """Return the current user's normalized role."""
    user = get_current_user()

    if not user:
        return None

    role = user.get("role")

    if not role:
        return None

    normalized = str(role).strip().lower()

    return normalized if normalized in VALID_ROLES else None


def is_authenticated() -> bool:
    """Check whether a valid user session exists."""
    user = get_current_user()

    if not user:
        return False

    return get_current_user_id() is not None


# ---------------------------------------------------------
# ROLE MANAGEMENT
# ---------------------------------------------------------

def validate_role(role: str) -> str:
    """Validate and normalize a role name."""
    normalized = str(role).strip().lower()

    if normalized not in VALID_ROLES:
        raise ValueError(
            f"Invalid role '{role}'. "
            f"Allowed roles: {', '.join(sorted(VALID_ROLES))}"
        )

    return normalized


def get_role_permissions(role: str) -> Set[str]:
    """Return the default permissions assigned to a role."""
    normalized = validate_role(role)

    return set(ROLE_PERMISSIONS[normalized])


def get_available_roles() -> List[Dict[str, str]]:
    """Return available roles and descriptions."""
    return [
        {
            "role": ROLE_ADMIN,
            "name": "Administrator",
            "description": "Full system management access.",
        },
        {
            "role": ROLE_ANALYST,
            "name": "Data Analyst",
            "description": "Can import, analyse, transform, and report on data.",
        },
        {
            "role": ROLE_USER,
            "name": "Standard User",
            "description": "Can manage personal projects and perform basic analysis.",
        },
        {
            "role": ROLE_VIEWER,
            "name": "Viewer",
            "description": "Can view permitted projects, datasets, and reports.",
        },
    ]


# ---------------------------------------------------------
# CUSTOM PERMISSIONS
# ---------------------------------------------------------

def set_user_custom_permissions(
    user_id: str,
    permissions: Iterable[str],
) -> List[str]:
    """
    Store additional permissions for a user in session state.

    This is temporary session storage, not permanent database storage.
    """
    if not user_id:
        raise ValueError("User ID is required.")

    selected = set(permissions)
    invalid = selected - PERMISSIONS

    if invalid:
        raise ValueError(
            "Unknown permissions: "
            + ", ".join(sorted(invalid))
        )

    key = "jak_custom_user_permissions"

    if key not in st.session_state:
        st.session_state[key] = {}

    st.session_state[key][str(user_id)] = sorted(selected)

    return sorted(selected)


def get_user_custom_permissions(user_id: str) -> Set[str]:
    """Return additional permissions assigned to a user."""
    if not user_id:
        return set()

    custom = st.session_state.get(
        "jak_custom_user_permissions",
        {},
    )

    return set(custom.get(str(user_id), []))


def clear_user_custom_permissions(user_id: str) -> bool:
    """Remove temporary custom permissions for a user."""
    custom = st.session_state.get(
        "jak_custom_user_permissions",
        {},
    )

    if str(user_id) not in custom:
        return False

    del custom[str(user_id)]
    return True


# ---------------------------------------------------------
# PERMISSION CHECKS
# ---------------------------------------------------------

def get_user_permissions(
    user: Optional[Dict[str, Any]] = None,
) -> Set[str]:
    """Calculate effective permissions for a user."""
    if user is None:
        user = get_current_user()

    if not user:
        return set()

    role = str(user.get("role", "")).strip().lower()

    if role not in VALID_ROLES:
        return set()

    permissions = get_role_permissions(role)

    user_id = user.get("id") or user.get("user_id")

    if user_id is not None:
        permissions.update(
            get_user_custom_permissions(str(user_id))
        )

    return permissions


def has_permission(
    permission: str,
    user: Optional[Dict[str, Any]] = None,
) -> bool:
    """Check whether a user has a specific permission."""
    if permission not in PERMISSIONS:
        return False

    return permission in get_user_permissions(user)


def has_any_permission(
    permissions: Iterable[str],
    user: Optional[Dict[str, Any]] = None,
) -> bool:
    """Check whether a user has at least one listed permission."""
    return any(
        has_permission(permission, user)
        for permission in permissions
    )


def has_all_permissions(
    permissions: Iterable[str],
    user: Optional[Dict[str, Any]] = None,
) -> bool:
    """Check whether a user has every listed permission."""
    return all(
        has_permission(permission, user)
        for permission in permissions
    )


def require_permission(permission: str) -> None:
    """
    Stop execution when the current user lacks a permission.

    Use this before displaying or performing protected operations.
    """
    if not is_authenticated():
        st.error("Please log in to access this feature.")
        st.stop()

    if not has_permission(permission):
        st.error(
            "Access denied. You do not have permission "
            "to perform this action."
        )
        st.stop()


def require_any_permission(permissions: Iterable[str]) -> None:
    """Require at least one permission from a list."""
    if not is_authenticated():
        st.error("Please log in to access this feature.")
        st.stop()

    if not has_any_permission(permissions):
        st.error("Access denied.")
        st.stop()


def require_all_permissions(permissions: Iterable[str]) -> None:
    """Require every permission from a list."""
    if not is_authenticated():
        st.error("Please log in to access this feature.")
        st.stop()

    if not has_all_permissions(permissions):
        st.error("Access denied.")
        st.stop()


# ---------------------------------------------------------
# RESOURCE OWNERSHIP
# ---------------------------------------------------------

def is_resource_owner(
    resource: Dict[str, Any],
    user: Optional[Dict[str, Any]] = None,
) -> bool:
    """Check whether the user owns a resource."""
    if user is None:
        user = get_current_user()

    if not user or not resource:
        return False

    user_id = user.get("id") or user.get("user_id")

    owner_id = (
        resource.get("owner_id")
        or resource.get("user_id")
        or resource.get("created_by")
    )

    if user_id is None or owner_id is None:
        return False

    return str(user_id) == str(owner_id)


def can_access_resource(
    resource: Dict[str, Any],
    permission: str,
    user: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Check permission and resource ownership.

    Administrators can access all resources covered by their role.
    Other users must own the resource.
    """
    if user is None:
        user = get_current_user()

    if not user:
        return False

    if not has_permission(permission, user):
        return False

    if str(user.get("role", "")).lower() == ROLE_ADMIN:
        return True

    return is_resource_owner(resource, user)


# ---------------------------------------------------------
# PERMISSION INFORMATION
# ---------------------------------------------------------

def get_permission_catalogue() -> List[Dict[str, str]]:
    """Return all available permissions grouped by module."""
    result = []

    for permission in sorted(PERMISSIONS):
        module, action = permission.split(".", 1)

        result.append({
            "permission": permission,
            "module": module,
            "action": action,
            "label": (
                action.replace("_", " ").title()
                + " "
                + module.replace("_", " ").title()
            ),
        })

    return result


def get_access_summary(
    user: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Return a summary of a user's effective access."""
    if user is None:
        user = get_current_user()

    if not user:
        return {
            "authenticated": False,
            "user_id": None,
            "role": None,
            "permission_count": 0,
            "permissions": [],
        }

    permissions = get_user_permissions(user)

    user_id = user.get("id") or user.get("user_id")

    return {
        "authenticated": True,
        "user_id": str(user_id) if user_id is not None else None,
        "role": user.get("role"),
        "permission_count": len(permissions),
        "permissions": sorted(permissions),
    }
