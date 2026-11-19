"""
JAK Data Analytics
Security Audit Service

Records security-related events for monitoring and auditing.

Features:
- Successful and failed login records
- Logout records
- Password change events
- Account security events
- Permission change events
- Suspicious activity records
- Security event filtering
- Security statistics
- Audit record export

Current storage:
Streamlit session state.

Production note:
Move audit records to a persistent database repository.
Security audit records should be append-only for normal users.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import streamlit as st


SECURITY_AUDIT_KEY = "jak_security_audit_logs"


VALID_EVENT_TYPES = {
    "login_success",
    "login_failed",
    "logout",
    "password_changed",
    "password_reset_requested",
    "password_reset_completed",
    "account_created",
    "account_suspended",
    "account_activated",
    "permission_changed",
    "role_changed",
    "two_factor_enabled",
    "two_factor_disabled",
    "session_expired",
    "suspicious_activity",
    "access_denied",
    "data_exported",
    "security_setting_changed",
    "other",
}

VALID_SEVERITIES = {
    "info",
    "low",
    "medium",
    "high",
    "critical",
}


# ---------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------

def _now() -> str:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _get_logs() -> List[Dict[str, Any]]:
    """Get or initialize the security audit collection."""
    if SECURITY_AUDIT_KEY not in st.session_state:
        st.session_state[SECURITY_AUDIT_KEY] = []

    return st.session_state[SECURITY_AUDIT_KEY]


def _get_current_user() -> Optional[Dict[str, Any]]:
    """Retrieve the authenticated user from supported session keys."""
    for key in ("jak_user", "user", "authenticated_user"):
        user = st.session_state.get(key)

        if isinstance(user, dict):
            return user

    return None


def _get_current_user_id() -> Optional[str]:
    """Retrieve the current user's ID."""
    user = _get_current_user()

    if not user:
        return None

    user_id = user.get("id") or user.get("user_id")

    return str(user_id) if user_id is not None else None


def _sanitize_metadata(
    metadata: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Remove sensitive values from audit metadata.

    Never store passwords, authentication tokens, API keys,
    session identifiers, or secret credentials in audit records.
    """
    if not metadata:
        return {}

    if not isinstance(metadata, dict):
        raise ValueError("Metadata must be a dictionary.")

    sensitive_terms = {
        "password",
        "passwd",
        "token",
        "secret",
        "api_key",
        "apikey",
        "authorization",
        "credential",
        "private_key",
        "session_id",
        "access_token",
        "refresh_token",
    }

    sanitized = {}

    for key, value in metadata.items():
        normalized_key = str(key).lower().replace("-", "_")

        if any(
            term in normalized_key
            for term in sensitive_terms
        ):
            sanitized[str(key)] = "[REDACTED]"
            continue

        if isinstance(value, dict):
            sanitized[str(key)] = _sanitize_metadata(value)

        elif isinstance(value, (str, int, float, bool)) or value is None:
            sanitized[str(key)] = value

        else:
            sanitized[str(key)] = str(value)[:500]

    return sanitized


# ---------------------------------------------------------
# RECORD SECURITY EVENTS
# ---------------------------------------------------------

def record_security_event(
    event_type: str,
    description: str,
    user_id: Optional[str] = None,
    severity: str = "info",
    actor_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Record a security event.

    IP address and user agent should only be supplied when
    obtained legitimately and handled according to the
    application's privacy policy.
    """
    event_type = str(event_type).strip().lower()
    severity = str(severity).strip().lower()

    if event_type not in VALID_EVENT_TYPES:
        raise ValueError("Invalid security event type.")

    if severity not in VALID_SEVERITIES:
        raise ValueError("Invalid security event severity.")

    if not description or not str(description).strip():
        raise ValueError("Event description is required.")

    current_user_id = _get_current_user_id()

    if actor_id is None:
        actor_id = current_user_id

    record = {
        "id": str(uuid4()),
        "event_type": event_type,
        "description": str(description).strip()[:2000],
        "severity": severity,
        "user_id": str(user_id) if user_id is not None else None,
        "actor_id": str(actor_id) if actor_id is not None else None,
        "ip_address": (
            str(ip_address)[:100]
            if ip_address
            else None
        ),
        "user_agent": (
            str(user_agent)[:500]
            if user_agent
            else None
        ),
        "resource_type": (
            str(resource_type)[:100]
            if resource_type
            else None
        ),
        "resource_id": (
            str(resource_id)[:200]
            if resource_id
            else None
        ),
        "metadata": _sanitize_metadata(metadata),
        "created_at": _now(),
    }

    _get_logs().append(record)

    return record.copy()


# ---------------------------------------------------------
# AUTHENTICATION EVENTS
# ---------------------------------------------------------

def record_login_success(
    user_id: str,
    email: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Dict[str, Any]:
    """Record a successful login."""
    metadata = {}

    if email:
        metadata["email"] = str(email)[:254]

    return record_security_event(
        event_type="login_success",
        description="User successfully signed in.",
        user_id=user_id,
        severity="info",
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=metadata,
    )


def record_login_failure(
    email: Optional[str] = None,
    reason: str = "Invalid login credentials.",
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Dict[str, Any]:
    """Record a failed login attempt without storing credentials."""
    metadata = {}

    if email:
        metadata["email"] = str(email)[:254]

    return record_security_event(
        event_type="login_failed",
        description="A login attempt failed.",
        severity="medium",
        ip_address=ip_address,
        user_agent=user_agent,
        metadata={
            **metadata,
            "failure_reason": str(reason)[:300],
        },
    )


def record_logout(
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Record a user logout."""
    return record_security_event(
        event_type="logout",
        description="User signed out.",
        user_id=user_id,
        severity="info",
    )


def record_session_expired(
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Record an expired authentication session."""
    return record_security_event(
        event_type="session_expired",
        description="User authentication session expired.",
        user_id=user_id,
        severity="low",
    )


# ---------------------------------------------------------
# ACCOUNT SECURITY EVENTS
# ---------------------------------------------------------

def record_password_change(
    user_id: str,
) -> Dict[str, Any]:
    """Record a successful password change."""
    return record_security_event(
        event_type="password_changed",
        description="Account password was changed.",
        user_id=user_id,
        severity="medium",
    )


def record_password_reset_request(
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Record a password reset request."""
    return record_security_event(
        event_type="password_reset_requested",
        description="A password reset was requested.",
        user_id=user_id,
        severity="low",
    )


def record_password_reset_completed(
    user_id: str,
) -> Dict[str, Any]:
    """Record a completed password reset."""
    return record_security_event(
        event_type="password_reset_completed",
        description="Account password reset was completed.",
        user_id=user_id,
        severity="medium",
    )


def record_account_suspended(
    user_id: str,
    reason: str = "",
) -> Dict[str, Any]:
    """Record an account suspension."""
    return record_security_event(
        event_type="account_suspended",
        description="User account was suspended.",
        user_id=user_id,
        severity="high",
        metadata={"reason": reason},
    )


def record_account_activated(
    user_id: str,
) -> Dict[str, Any]:
    """Record account reactivation."""
    return record_security_event(
        event_type="account_activated",
        description="User account was activated.",
        user_id=user_id,
        severity="medium",
    )


# ---------------------------------------------------------
# PERMISSION AND ROLE EVENTS
# ---------------------------------------------------------

def record_permission_change(
    user_id: str,
    permission: str,
    action: str,
) -> Dict[str, Any]:
    """Record a permission change."""
    return record_security_event(
        event_type="permission_changed",
        description="A user permission was changed.",
        user_id=user_id,
        severity="high",
        metadata={
            "permission": permission,
            "action": action,
        },
    )


def record_role_change(
    user_id: str,
    old_role: str,
    new_role: str,
) -> Dict[str, Any]:
    """Record a user role change."""
    return record_security_event(
        event_type="role_changed",
        description="User role was changed.",
        user_id=user_id,
        severity="high",
        metadata={
            "old_role": old_role,
            "new_role": new_role,
        },
    )


def record_access_denied(
    description: str,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Record an access-denied event."""
    return record_security_event(
        event_type="access_denied",
        description=description,
        user_id=user_id,
        severity="medium",
        resource_type=resource_type,
        resource_id=resource_id,
    )


# ---------------------------------------------------------
# SUSPICIOUS ACTIVITY
# ---------------------------------------------------------

def record_suspicious_activity(
    description: str,
    user_id: Optional[str] = None,
    severity: str = "high",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Record suspicious application activity."""
    if severity not in {"medium", "high", "critical"}:
        raise ValueError(
            "Suspicious activity severity must be medium, high, or critical."
        )

    return record_security_event(
        event_type="suspicious_activity",
        description=description,
        user_id=user_id,
        severity=severity,
        metadata=metadata,
    )


# ---------------------------------------------------------
# RETRIEVE AUDIT RECORDS
# ---------------------------------------------------------

def get_security_audit_logs(
    user_id: Optional[str] = None,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: Optional[int] = 100,
) -> List[Dict[str, Any]]:
    """Retrieve security audit records with optional filters."""
    records = list(_get_logs())

    if user_id is not None:
        identifier = str(user_id)

        records = [
            item for item in records
            if (
                item.get("user_id") == identifier
                or item.get("actor_id") == identifier
            )
        ]

    if event_type:
        normalized = event_type.lower().strip()

        if normalized not in VALID_EVENT_TYPES:
            raise ValueError("Invalid event type.")

        records = [
            item for item in records
            if item.get("event_type") == normalized
        ]

    if severity:
        normalized = severity.lower().strip()

        if normalized not in VALID_SEVERITIES:
            raise ValueError("Invalid severity.")

        records = [
            item for item in records
            if item.get("severity") == normalized
        ]

    records.sort(
        key=lambda item: item.get("created_at", ""),
        reverse=True,
    )

    if limit is not None:
        if limit < 1:
            raise ValueError("Limit must be greater than zero.")

        records = records[:limit]

    return [item.copy() for item in records]


def get_security_event(
    event_id: str,
) -> Optional[Dict[str, Any]]:
    """Retrieve one security audit event by its ID."""
    for item in _get_logs():
        if item.get("id") == str(event_id):
            return item.copy()

    return None


# ---------------------------------------------------------
# SECURITY STATISTICS
# ---------------------------------------------------------

def get_security_statistics() -> Dict[str, Any]:
    """Calculate security audit statistics."""
    records = _get_logs()

    event_counts = {
        event_type: 0
        for event_type in VALID_EVENT_TYPES
    }

    severity_counts = {
        severity: 0
        for severity in VALID_SEVERITIES
    }

    for item in records:
        event_type = item.get("event_type")
        severity = item.get("severity")

        if event_type in event_counts:
            event_counts[event_type] += 1

        if severity in severity_counts:
            severity_counts[severity] += 1

    return {
        "total_events": len(records),
        "event_counts": event_counts,
        "severity_counts": severity_counts,
        "failed_logins": event_counts["login_failed"],
        "successful_logins": event_counts["login_success"],
        "suspicious_activities": event_counts["suspicious_activity"],
        "access_denied_events": event_counts["access_denied"],
        "critical_events": severity_counts["critical"],
        "high_severity_events": severity_counts["high"],
    }


# ---------------------------------------------------------
# EXPORT
# ---------------------------------------------------------

def export_security_audit_logs() -> List[Dict[str, Any]]:
    """Return all audit records for export."""
    return get_security_audit_logs(limit=None)


# ---------------------------------------------------------
# DISPLAY HELPERS
# ---------------------------------------------------------

def get_severity_color(severity: str) -> str:
    """Return a UI color for a security severity."""
    colors = {
        "info": "#2563EB",
        "low": "#64748B",
        "medium": "#F59E0B",
        "high": "#EA580C",
        "critical": "#DC2626",
    }

    return colors.get(
        str(severity).lower(),
        "#64748B",
    )


def get_event_label(event_type: str) -> str:
    """Convert an event type into a readable label."""
    return str(event_type).replace("_", " ").title()


def get_severity_label(severity: str) -> str:
    """Convert a severity into a readable label."""
    return str(severity).title()
