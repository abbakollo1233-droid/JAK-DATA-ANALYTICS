"""
JAK Data Analytics - Session Management Service

Manages session metadata and lifecycle operations.

IMPORTANT:
This implementation uses Streamlit session state for development.
It is not a replacement for a secure production session manager.
Production sessions should be stored and managed server-side.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import streamlit as st


SESSION_STATE_KEY = "jak_managed_sessions"
CURRENT_SESSION_KEY = "jak_current_session_id"

DEFAULT_SESSION_TIMEOUT_MINUTES = 60
MAX_SESSION_HISTORY = 500


def _utc_now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(timezone.utc)


def _get_sessions() -> Dict[str, Dict[str, Any]]:
    """Retrieve the current session registry."""
    sessions = st.session_state.get(SESSION_STATE_KEY)

    if not isinstance(sessions, dict):
        sessions = {}
        st.session_state[SESSION_STATE_KEY] = sessions

    return sessions


def _parse_datetime(value: Any) -> Optional[datetime]:
    """Convert a datetime or ISO timestamp into an aware UTC datetime."""
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
    else:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def _serialize_datetime(value: datetime) -> str:
    """Convert datetime to ISO 8601."""
    return value.astimezone(timezone.utc).isoformat()


def _clean_session_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of a session record with normalized timestamps."""
    cleaned = dict(record)

    for field in (
        "created_at",
        "last_activity_at",
        "expires_at",
        "revoked_at",
    ):
        if cleaned.get(field):
            parsed = _parse_datetime(cleaned[field])
            cleaned[field] = (
                _serialize_datetime(parsed) if parsed else None
            )

    return cleaned


def create_session(
    user_id: Any,
    user_email: str = "",
    user_role: str = "user",
    timeout_minutes: int = DEFAULT_SESSION_TIMEOUT_MINUTES,
    device_name: str = "Unknown device",
    ip_address: str = "",
    user_agent: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a managed session for an authenticated user.

    Call this after successful authentication.
    """

    if user_id is None or str(user_id).strip() == "":
        return {
            "success": False,
            "message": "A valid user ID is required.",
        }

    try:
        timeout_minutes = int(timeout_minutes)
    except (TypeError, ValueError):
        timeout_minutes = DEFAULT_SESSION_TIMEOUT_MINUTES

    timeout_minutes = max(1, min(timeout_minutes, 10080))

    now = _utc_now()
    session_id = str(uuid4())

    record = {
        "session_id": session_id,
        "user_id": str(user_id),
        "user_email": str(user_email or ""),
        "user_role": str(user_role or "user"),
        "device_name": str(device_name or "Unknown device"),
        "ip_address": str(ip_address or ""),
        "user_agent": str(user_agent or ""),
        "created_at": _serialize_datetime(now),
        "last_activity_at": _serialize_datetime(now),
        "expires_at": _serialize_datetime(
            now + timedelta(minutes=timeout_minutes)
        ),
        "timeout_minutes": timeout_minutes,
        "is_active": True,
        "is_revoked": False,
        "revoked_at": None,
        "revocation_reason": "",
        "metadata": metadata or {},
    }

    sessions = _get_sessions()
    sessions[session_id] = record

    st.session_state[CURRENT_SESSION_KEY] = session_id

    _trim_session_history()

    return {
        "success": True,
        "message": "Session created successfully.",
        "session": _clean_session_record(record),
    }


def get_current_session() -> Optional[Dict[str, Any]]:
    """Return the current managed session."""
    session_id = st.session_state.get(CURRENT_SESSION_KEY)

    if not session_id:
        return None

    record = _get_sessions().get(session_id)

    if not record:
        return None

    return _clean_session_record(record)


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a session by its ID."""
    record = _get_sessions().get(str(session_id))

    if not record:
        return None

    return _clean_session_record(record)


def validate_session(
    session_id: Optional[str] = None,
    extend_session: bool = True,
) -> Dict[str, Any]:
    """
    Check whether a managed session is active and has not expired.

    If extend_session is True, valid activity refreshes its expiry time.
    """

    if not session_id:
        session_id = st.session_state.get(CURRENT_SESSION_KEY)

    if not session_id:
        return {
            "valid": False,
            "reason": "No active session was found.",
        }

    sessions = _get_sessions()
    record = sessions.get(str(session_id))

    if not record:
        return {
            "valid": False,
            "reason": "Session does not exist.",
        }

    if record.get("is_revoked"):
        return {
            "valid": False,
            "reason": "This session has been revoked.",
        }

    if not record.get("is_active"):
        return {
            "valid": False,
            "reason": "This session is inactive.",
        }

    now = _utc_now()
    expires_at = _parse_datetime(record.get("expires_at"))

    if not expires_at or now >= expires_at:
        record["is_active"] = False
        record["expired_at"] = _serialize_datetime(now)

        if st.session_state.get(CURRENT_SESSION_KEY) == session_id:
            st.session_state.pop(CURRENT_SESSION_KEY, None)

        return {
            "valid": False,
            "reason": "Your session has expired. Please log in again.",
        }

    if extend_session:
        timeout = int(
            record.get(
                "timeout_minutes",
                DEFAULT_SESSION_TIMEOUT_MINUTES,
            )
        )

        record["last_activity_at"] = _serialize_datetime(now)
        record["expires_at"] = _serialize_datetime(
            now + timedelta(minutes=timeout)
        )

    return {
        "valid": True,
        "reason": "Session is valid.",
        "session": _clean_session_record(record),
    }


def refresh_session(
    session_id: Optional[str] = None,
    timeout_minutes: Optional[int] = None,
) -> Dict[str, Any]:
    """Refresh the expiry time of a valid session."""

    if not session_id:
        session_id = st.session_state.get(CURRENT_SESSION_KEY)

    result = validate_session(
        session_id=session_id,
        extend_session=False,
    )

    if not result["valid"]:
        return {
            "success": False,
            "message": result["reason"],
        }

    record = _get_sessions()[str(session_id)]

    if timeout_minutes is None:
        timeout_minutes = record.get(
            "timeout_minutes",
            DEFAULT_SESSION_TIMEOUT_MINUTES,
        )

    try:
        timeout_minutes = int(timeout_minutes)
    except (TypeError, ValueError):
        timeout_minutes = DEFAULT_SESSION_TIMEOUT_MINUTES

    timeout_minutes = max(1, min(timeout_minutes, 10080))

    now = _utc_now()

    record["timeout_minutes"] = timeout_minutes
    record["last_activity_at"] = _serialize_datetime(now)
    record["expires_at"] = _serialize_datetime(
        now + timedelta(minutes=timeout_minutes)
    )

    return {
        "success": True,
        "message": "Session refreshed successfully.",
        "session": _clean_session_record(record),
    }


def revoke_session(
    session_id: str,
    reason: str = "Session revoked",
) -> Dict[str, Any]:
    """Revoke a specific session."""

    sessions = _get_sessions()
    record = sessions.get(str(session_id))

    if not record:
        return {
            "success": False,
            "message": "Session not found.",
        }

    now = _utc_now()

    record["is_active"] = False
    record["is_revoked"] = True
    record["revoked_at"] = _serialize_datetime(now)
    record["revocation_reason"] = str(reason)

    if st.session_state.get(CURRENT_SESSION_KEY) == str(session_id):
        st.session_state.pop(CURRENT_SESSION_KEY, None)

    return {
        "success": True,
        "message": "Session revoked successfully.",
    }


def revoke_all_user_sessions(
    user_id: Any,
    reason: str = "All sessions revoked",
    except_current: bool = False,
) -> Dict[str, Any]:
    """Revoke all sessions belonging to a user."""

    sessions = _get_sessions()
    current_id = st.session_state.get(CURRENT_SESSION_KEY)
    revoked_count = 0
    now = _utc_now()

    for session_id, record in sessions.items():
        if str(record.get("user_id")) != str(user_id):
            continue

        if not record.get("is_active"):
            continue

        if except_current and session_id == current_id:
            continue

        record["is_active"] = False
        record["is_revoked"] = True
        record["revoked_at"] = _serialize_datetime(now)
        record["revocation_reason"] = str(reason)

        if session_id == current_id:
            st.session_state.pop(CURRENT_SESSION_KEY, None)

        revoked_count += 1

    return {
        "success": True,
        "message": f"{revoked_count} session(s) revoked.",
        "revoked_count": revoked_count,
    }


def logout_current_session() -> Dict[str, Any]:
    """End the current managed session."""

    session_id = st.session_state.get(CURRENT_SESSION_KEY)

    if not session_id:
        return {
            "success": False,
            "message": "No active managed session was found.",
        }

    result = revoke_session(
        session_id,
        reason="User logged out",
    )

    return result


def get_user_sessions(
    user_id: Any,
    active_only: bool = False,
) -> List[Dict[str, Any]]:
    """Get session history for a specific user."""

    results = []

    for record in _get_sessions().values():
        if str(record.get("user_id")) != str(user_id):
            continue

        if active_only and not record.get("is_active"):
            continue

        results.append(_clean_session_record(record))

    results.sort(
        key=lambda item: item.get("created_at") or "",
        reverse=True,
    )

    return results


def get_active_sessions(
    user_id: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Return active, non-revoked and non-expired sessions."""

    results = []
    now = _utc_now()

    for record in _get_sessions().values():
        if user_id is not None:
            if str(record.get("user_id")) != str(user_id):
                continue

        if not record.get("is_active"):
            continue

        if record.get("is_revoked"):
            continue

        expires_at = _parse_datetime(record.get("expires_at"))

        if not expires_at or now >= expires_at:
            continue

        results.append(_clean_session_record(record))

    results.sort(
        key=lambda item: item.get("last_activity_at") or "",
        reverse=True,
    )

    return results


def expire_inactive_sessions() -> Dict[str, Any]:
    """Mark expired sessions as inactive."""

    sessions = _get_sessions()
    now = _utc_now()
    expired_count = 0

    for session_id, record in sessions.items():
        if not record.get("is_active"):
            continue

        expires_at = _parse_datetime(record.get("expires_at"))

        if not expires_at or now >= expires_at:
            record["is_active"] = False
            record["expired_at"] = _serialize_datetime(now)
            expired_count += 1

            if st.session_state.get(CURRENT_SESSION_KEY) == session_id:
                st.session_state.pop(CURRENT_SESSION_KEY, None)

    return {
        "success": True,
        "expired_count": expired_count,
    }


def get_session_statistics(
    user_id: Optional[Any] = None,
) -> Dict[str, int]:
    """Calculate session statistics."""

    records = list(_get_sessions().values())

    if user_id is not None:
        records = [
            record
            for record in records
            if str(record.get("user_id")) == str(user_id)
        ]

    now = _utc_now()

    active_count = 0
    expired_count = 0
    revoked_count = 0

    for record in records:
        if record.get("is_revoked"):
            revoked_count += 1
            continue

        expires_at = _parse_datetime(record.get("expires_at"))

        if not record.get("is_active") or not expires_at or now >= expires_at:
            expired_count += 1
        else:
            active_count += 1

    return {
        "total_sessions": len(records),
        "active_sessions": active_count,
        "expired_sessions": expired_count,
        "revoked_sessions": revoked_count,
    }


def get_session_history(
    user_id: Optional[Any] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Return recent session records."""

    try:
        limit = max(1, min(int(limit), MAX_SESSION_HISTORY))
    except (TypeError, ValueError):
        limit = 100

    records = list(_get_sessions().values())

    if user_id is not None:
        records = [
            record
            for record in records
            if str(record.get("user_id")) == str(user_id)
        ]

    records.sort(
        key=lambda item: item.get("created_at") or "",
        reverse=True,
    )

    return [
        _clean_session_record(record)
        for record in records[:limit]
    ]


def _trim_session_history() -> None:
    """Keep the in-memory registry within its configured size."""

    sessions = _get_sessions()

    if len(sessions) <= MAX_SESSION_HISTORY:
        return

    ordered = sorted(
        sessions.items(),
        key=lambda item: item[1].get("created_at") or "",
        reverse=True,
    )

    st.session_state[SESSION_STATE_KEY] = dict(
        ordered[:MAX_SESSION_HISTORY]
    )


def clear_session_registry() -> None:
    """
    Clear the current Streamlit session registry.

    Intended for development and testing only.
    Do not expose this operation to ordinary users.
    """

    st.session_state[SESSION_STATE_KEY] = {}
    st.session_state.pop(CURRENT_SESSION_KEY, None)
