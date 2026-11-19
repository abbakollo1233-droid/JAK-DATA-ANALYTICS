"""
JAK Data Analytics - Password Reset Service

Handles password-reset token creation, validation,
expiration, and single-use protection.

IMPORTANT:
This development implementation uses Streamlit session state.
Production must store reset-token hashes in the database.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

import streamlit as st

from jak_data_analytics.services.password_policy_service import (
    generate_password_reset_token,
    hash_reset_token,
    verify_reset_token,
)


RESET_STORE_KEY = "jak_password_reset_records"

DEFAULT_TOKEN_EXPIRY_MINUTES = 30
MAX_RESET_RECORDS = 1000


def _utc_now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(timezone.utc)


def _get_store() -> Dict[str, Dict[str, Any]]:
    """Get or initialize the reset-token store."""

    store = st.session_state.get(RESET_STORE_KEY)

    if not isinstance(store, dict):
        store = {}
        st.session_state[RESET_STORE_KEY] = store

    return store


def _parse_datetime(value: Any) -> Optional[datetime]:
    """Convert a datetime or ISO timestamp into UTC."""

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
    """Serialize a datetime as ISO 8601."""
    return value.astimezone(timezone.utc).isoformat()


def _public_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Return a reset record without its token hash."""

    return {
        "reset_id": record.get("reset_id"),
        "user_id": record.get("user_id"),
        "email": record.get("email"),
        "created_at": record.get("created_at"),
        "expires_at": record.get("expires_at"),
        "used": record.get("used", False),
        "revoked": record.get("revoked", False),
        "expired": record.get("expired", False),
    }


def create_reset_request(
    user_id: Any,
    email: str,
    expiry_minutes: int = DEFAULT_TOKEN_EXPIRY_MINUTES,
) -> Dict[str, Any]:
    """
    Create a password-reset request.

    The returned token should be sent to the user through
    a verified email address.

    Never store the plain-text token.
    """

    if user_id is None or not str(user_id).strip():
        return {
            "success": False,
            "message": "A valid user ID is required.",
        }

    if not isinstance(email, str) or "@" not in email:
        return {
            "success": False,
            "message": "A valid email address is required.",
        }

    try:
        expiry_minutes = max(5, min(int(expiry_minutes), 120))
    except (TypeError, ValueError):
        expiry_minutes = DEFAULT_TOKEN_EXPIRY_MINUTES

    now = _utc_now()

    # Revoke previous unused reset requests for this user.
    revoke_user_reset_requests(
        user_id=user_id,
        reason="Replaced by a newer reset request",
    )

    token = generate_password_reset_token()
    reset_id = str(uuid4())

    record = {
        "reset_id": reset_id,
        "user_id": str(user_id),
        "email": email.strip().lower(),
        "token_hash": hash_reset_token(token),
        "created_at": _serialize_datetime(now),
        "expires_at": _serialize_datetime(
            now + timedelta(minutes=expiry_minutes)
        ),
        "used": False,
        "used_at": None,
        "revoked": False,
        "revoked_at": None,
        "revocation_reason": "",
        "expired": False,
        "attempt_count": 0,
    }

    store = _get_store()
    store[reset_id] = record

    _trim_store()

    return {
        "success": True,
        "message": "Password-reset request created.",
        "reset_id": reset_id,
        "token": token,
        "expires_at": record["expires_at"],
        "expiry_minutes": expiry_minutes,
    }


def validate_reset_token(
    reset_id: str,
    token: str,
    user_id: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Validate a password-reset token.

    A valid token must:
    - Exist in the reset store.
    - Belong to the expected user, if supplied.
    - Not have been used.
    - Not have been revoked.
    - Not have expired.
    - Match the stored token hash.
    """

    if not reset_id or not token:
        return {
            "valid": False,
            "message": "Reset ID and token are required.",
        }

    record = _get_store().get(str(reset_id))

    if not record:
        return {
            "valid": False,
            "message": "Invalid or expired reset link.",
        }

    if user_id is not None:
        if str(record.get("user_id")) != str(user_id):
            return {
                "valid": False,
                "message": "Invalid or expired reset link.",
            }

    if record.get("used"):
        return {
            "valid": False,
            "message": "This reset link has already been used.",
        }

    if record.get("revoked"):
        return {
            "valid": False,
            "message": "This reset link has been revoked.",
        }

    expires_at = _parse_datetime(record.get("expires_at"))

    if not expires_at or _utc_now() >= expires_at:
        record["expired"] = True

        return {
            "valid": False,
            "message": "This reset link has expired.",
        }

    record["attempt_count"] = (
        int(record.get("attempt_count", 0)) + 1
    )

    if record["attempt_count"] > 10:
        record["revoked"] = True
        record["revoked_at"] = _serialize_datetime(_utc_now())
        record["revocation_reason"] = "Too many validation attempts"

        return {
            "valid": False,
            "message": "Too many attempts. Request a new reset link.",
        }

    if not verify_reset_token(
        token,
        record.get("token_hash", ""),
    ):
        return {
            "valid": False,
            "message": "Invalid or expired reset link.",
        }

    return {
        "valid": True,
        "message": "Reset token is valid.",
        "user_id": record.get("user_id"),
        "email": record.get("email"),
        "reset_id": record.get("reset_id"),
    }


def complete_reset_request(
    reset_id: str,
    token: str,
    user_id: Any,
) -> Dict[str, Any]:
    """
    Mark a successfully validated reset request as used.

    IMPORTANT:
    Call this only after the new password has been securely
    hashed and successfully saved to the user's database record.
    """

    validation = validate_reset_token(
        reset_id=reset_id,
        token=token,
        user_id=user_id,
    )

    if not validation["valid"]:
        return {
            "success": False,
            "message": validation["message"],
        }

    record = _get_store()[str(reset_id)]
    now = _utc_now()

    record["used"] = True
    record["used_at"] = _serialize_datetime(now)

    # Remove the token hash after successful use.
    record.pop("token_hash", None)

    return {
        "success": True,
        "message": "Password-reset request completed.",
        "user_id": str(user_id),
    }


def revoke_reset_request(
    reset_id: str,
    reason: str = "Reset request revoked",
) -> Dict[str, Any]:
    """Revoke a particular reset request."""

    record = _get_store().get(str(reset_id))

    if not record:
        return {
            "success": False,
            "message": "Reset request not found.",
        }

    if record.get("used"):
        return {
            "success": False,
            "message": "This reset request has already been used.",
        }

    record["revoked"] = True
    record["revoked_at"] = _serialize_datetime(_utc_now())
    record["revocation_reason"] = str(reason)

    record.pop("token_hash", None)

    return {
        "success": True,
        "message": "Reset request revoked successfully.",
    }


def revoke_user_reset_requests(
    user_id: Any,
    reason: str = "All reset requests revoked",
) -> Dict[str, Any]:
    """Revoke all unused reset requests belonging to a user."""

    store = _get_store()
    now = _utc_now()
    revoked_count = 0

    for record in store.values():
        if str(record.get("user_id")) != str(user_id):
            continue

        if record.get("used") or record.get("revoked"):
            continue

        record["revoked"] = True
        record["revoked_at"] = _serialize_datetime(now)
        record["revocation_reason"] = str(reason)

        record.pop("token_hash", None)

        revoked_count += 1

    return {
        "success": True,
        "revoked_count": revoked_count,
        "message": f"{revoked_count} reset request(s) revoked.",
    }


def expire_reset_requests() -> Dict[str, Any]:
    """Mark expired, unused reset requests."""

    store = _get_store()
    now = _utc_now()
    expired_count = 0

    for record in store.values():
        if record.get("used") or record.get("revoked"):
            continue

        expires_at = _parse_datetime(record.get("expires_at"))

        if not expires_at or now >= expires_at:
            record["expired"] = True
            record.pop("token_hash", None)
            expired_count += 1

    return {
        "success": True,
        "expired_count": expired_count,
    }


def get_reset_request(
    reset_id: str,
) -> Optional[Dict[str, Any]]:
    """Retrieve a reset request without exposing its token hash."""

    record = _get_store().get(str(reset_id))

    if not record:
        return None

    return _public_record(record)


def get_user_reset_requests(
    user_id: Any,
    include_completed: bool = True,
) -> list:
    """Retrieve reset-request history for a user."""

    results = []

    for record in _get_store().values():
        if str(record.get("user_id")) != str(user_id):
            continue

        if not include_completed and record.get("used"):
            continue

        results.append(_public_record(record))

    results.sort(
        key=lambda item: item.get("created_at") or "",
        reverse=True,
    )

    return results


def get_reset_statistics() -> Dict[str, int]:
    """Return basic reset-request statistics."""

    store = _get_store()
    now = _utc_now()

    total = len(store)
    used = 0
    revoked = 0
    expired = 0
    active = 0

    for record in store.values():
        if record.get("used"):
            used += 1
        elif record.get("revoked"):
            revoked += 1
        else:
            expires_at = _parse_datetime(record.get("expires_at"))

            if not expires_at or now >= expires_at:
                expired += 1
            else:
                active += 1

    return {
        "total_requests": total,
        "used_requests": used,
        "revoked_requests": revoked,
        "expired_requests": expired,
        "active_requests": active,
    }


def _trim_store() -> None:
    """Limit the development reset-request history."""

    store = _get_store()

    if len(store) <= MAX_RESET_RECORDS:
        return

    ordered = sorted(
        store.items(),
        key=lambda item: item[1].get("created_at") or "",
        reverse=True,
    )

    st.session_state[RESET_STORE_KEY] = dict(
        ordered[:MAX_RESET_RECORDS]
    )


def clear_reset_store() -> None:
    """
    Clear all development reset records.

    Testing only. Never expose this to ordinary users.
    """

    st.session_state[RESET_STORE_KEY] = {}
