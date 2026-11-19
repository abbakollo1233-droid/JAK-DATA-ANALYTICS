"""
JAK Data Analytics - Email Verification Service

Manages email verification tokens and verification requests.

Features:
- Secure verification token generation.
- Hashed token storage.
- Token expiration.
- One-time verification.
- Resending verification requests.
- Revoking previous verification requests.
- Verification statistics.

IMPORTANT:
This development implementation uses Streamlit session state.
Production must persist verification records in the database.
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


VERIFICATION_STORE_KEY = "jak_email_verification_records"

DEFAULT_EXPIRY_MINUTES = 30
MAX_VERIFICATION_RECORDS = 1000
MAX_TOKEN_ATTEMPTS = 10


def _utc_now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(timezone.utc)


def _serialize_datetime(value: datetime) -> str:
    """Convert a datetime to an ISO 8601 string."""
    return value.astimezone(timezone.utc).isoformat()


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


def _get_store() -> Dict[str, Dict[str, Any]]:
    """Retrieve or initialize the verification store."""

    store = st.session_state.get(VERIFICATION_STORE_KEY)

    if not isinstance(store, dict):
        store = {}
        st.session_state[VERIFICATION_STORE_KEY] = store

    return store


def _public_record(
    record: Dict[str, Any],
) -> Dict[str, Any]:
    """Return verification information without exposing token hashes."""

    return {
        "verification_id": record.get("verification_id"),
        "user_id": record.get("user_id"),
        "email": record.get("email"),
        "created_at": record.get("created_at"),
        "expires_at": record.get("expires_at"),
        "verified": record.get("verified", False),
        "verified_at": record.get("verified_at"),
        "revoked": record.get("revoked", False),
        "expired": record.get("expired", False),
        "attempt_count": record.get("attempt_count", 0),
    }


def create_verification_request(
    user_id: Any,
    email: str,
    expiry_minutes: int = DEFAULT_EXPIRY_MINUTES,
) -> Dict[str, Any]:
    """
    Create a new email verification request.

    The plain-text token is returned once so the email service
    can send it to the user's email address.

    Never store the plain-text token.
    """

    if user_id is None or not str(user_id).strip():
        return {
            "success": False,
            "message": "A valid user ID is required.",
        }

    if not isinstance(email, str):
        return {
            "success": False,
            "message": "A valid email address is required.",
        }

    email = email.strip().lower()

    if (
        not email
        or "@" not in email
        or email.startswith("@")
        or email.endswith("@")
    ):
        return {
            "success": False,
            "message": "A valid email address is required.",
        }

    try:
        expiry_minutes = max(
            5,
            min(int(expiry_minutes), 1440),
        )
    except (TypeError, ValueError):
        expiry_minutes = DEFAULT_EXPIRY_MINUTES

    # Replace previous unused requests for this user.
    revoke_user_verification_requests(
        user_id=user_id,
        reason="Replaced by a newer verification request",
    )

    now = _utc_now()

    verification_id = str(uuid4())
    token = generate_password_reset_token()

    record = {
        "verification_id": verification_id,
        "user_id": str(user_id),
        "email": email,
        "token_hash": hash_reset_token(token),
        "created_at": _serialize_datetime(now),
        "expires_at": _serialize_datetime(
            now + timedelta(minutes=expiry_minutes)
        ),
        "verified": False,
        "verified_at": None,
        "revoked": False,
        "revoked_at": None,
        "revocation_reason": "",
        "expired": False,
        "attempt_count": 0,
    }

    store = _get_store()
    store[verification_id] = record

    _trim_store()

    return {
        "success": True,
        "message": "Verification request created successfully.",
        "verification_id": verification_id,
        "token": token,
        "email": email,
        "expires_at": record["expires_at"],
        "expiry_minutes": expiry_minutes,
    }


def validate_verification_token(
    verification_id: str,
    token: str,
    user_id: Optional[Any] = None,
    email: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validate an email verification token.

    A valid token must:
    - Exist.
    - Belong to the expected user, if supplied.
    - Match the expected email, if supplied.
    - Not have expired.
    - Not have been revoked.
    - Not have been used.
    """

    if not verification_id or not token:
        return {
            "valid": False,
            "message": "Verification ID and token are required.",
        }

    record = _get_store().get(str(verification_id))

    if not record:
        return {
            "valid": False,
            "message": "Invalid or expired verification link.",
        }

    if user_id is not None:
        if str(record.get("user_id")) != str(user_id):
            return {
                "valid": False,
                "message": "Invalid or expired verification link.",
            }

    if email is not None:
        if record.get("email") != str(email).strip().lower():
            return {
                "valid": False,
                "message": "Invalid or expired verification link.",
            }

    if record.get("verified"):
        return {
            "valid": False,
            "message": "This email has already been verified.",
        }

    if record.get("revoked"):
        return {
            "valid": False,
            "message": "This verification link has been revoked.",
        }

    expires_at = _parse_datetime(record.get("expires_at"))

    if not expires_at or _utc_now() >= expires_at:
        record["expired"] = True
        record.pop("token_hash", None)

        return {
            "valid": False,
            "message": "This verification link has expired.",
        }

    record["attempt_count"] = (
        int(record.get("attempt_count", 0)) + 1
    )

    if record["attempt_count"] > MAX_TOKEN_ATTEMPTS:
        record["revoked"] = True
        record["revoked_at"] = _serialize_datetime(_utc_now())
        record["revocation_reason"] = "Too many validation attempts"
        record.pop("token_hash", None)

        return {
            "valid": False,
            "message": "Too many attempts. Request a new verification link.",
        }

    if not verify_reset_token(
        token,
        record.get("token_hash", ""),
    ):
        return {
            "valid": False,
            "message": "Invalid or expired verification link.",
        }

    return {
        "valid": True,
        "message": "Verification token is valid.",
        "verification_id": verification_id,
        "user_id": record.get("user_id"),
        "email": record.get("email"),
    }


def complete_verification(
    verification_id: str,
    token: str,
    user_id: Any,
    email: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Complete a verification request.

    IMPORTANT:
    After this function succeeds, the authentication service
    must update the user's email_verified field in the database.

    This function only updates the development verification store.
    """

    validation = validate_verification_token(
        verification_id=verification_id,
        token=token,
        user_id=user_id,
        email=email,
    )

    if not validation["valid"]:
        return {
            "success": False,
            "message": validation["message"],
        }

    record = _get_store()[str(verification_id)]
    now = _utc_now()

    record["verified"] = True
    record["verified_at"] = _serialize_datetime(now)

    # Remove the token hash after successful verification.
    record.pop("token_hash", None)

    return {
        "success": True,
        "message": "Email verification completed successfully.",
        "user_id": str(user_id),
        "email": record.get("email"),
        "verified_at": record["verified_at"],
    }


def revoke_verification_request(
    verification_id: str,
    reason: str = "Verification request revoked",
) -> Dict[str, Any]:
    """Revoke a specific verification request."""

    record = _get_store().get(str(verification_id))

    if not record:
        return {
            "success": False,
            "message": "Verification request not found.",
        }

    if record.get("verified"):
        return {
            "success": False,
            "message": "This email has already been verified.",
        }

    record["revoked"] = True
    record["revoked_at"] = _serialize_datetime(_utc_now())
    record["revocation_reason"] = str(reason)

    record.pop("token_hash", None)

    return {
        "success": True,
        "message": "Verification request revoked successfully.",
    }


def revoke_user_verification_requests(
    user_id: Any,
    reason: str = "Verification requests revoked",
) -> Dict[str, Any]:
    """Revoke all unused verification requests for a user."""

    store = _get_store()
    now = _utc_now()
    revoked_count = 0

    for record in store.values():
        if str(record.get("user_id")) != str(user_id):
            continue

        if record.get("verified") or record.get("revoked"):
            continue

        record["revoked"] = True
        record["revoked_at"] = _serialize_datetime(now)
        record["revocation_reason"] = str(reason)

        record.pop("token_hash", None)

        revoked_count += 1

    return {
        "success": True,
        "revoked_count": revoked_count,
        "message": f"{revoked_count} verification request(s) revoked.",
    }


def expire_verification_requests() -> Dict[str, Any]:
    """Mark expired verification requests."""

    store = _get_store()
    now = _utc_now()
    expired_count = 0

    for record in store.values():
        if record.get("verified") or record.get("revoked"):
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


def get_verification_request(
    verification_id: str,
) -> Optional[Dict[str, Any]]:
    """Retrieve a verification request without its token hash."""

    record = _get_store().get(str(verification_id))

    if not record:
        return None

    return _public_record(record)


def get_user_verification_history(
    user_id: Any,
) -> list:
    """Retrieve verification history for a user."""

    results = []

    for record in _get_store().values():
        if str(record.get("user_id")) != str(user_id):
            continue

        results.append(_public_record(record))

    results.sort(
        key=lambda item: item.get("created_at") or "",
        reverse=True,
    )

    return results


def get_verification_statistics() -> Dict[str, int]:
    """Return email verification statistics."""

    store = _get_store()
    now = _utc_now()

    total = len(store)
    verified = 0
    revoked = 0
    expired = 0
    pending = 0

    for record in store.values():
        if record.get("verified"):
            verified += 1

        elif record.get("revoked"):
            revoked += 1

        else:
            expires_at = _parse_datetime(record.get("expires_at"))

            if not expires_at or now >= expires_at:
                expired += 1
            else:
                pending += 1

    return {
        "total_requests": total,
        "verified_requests": verified,
        "revoked_requests": revoked,
        "expired_requests": expired,
        "pending_requests": pending,
    }


def _trim_store() -> None:
    """Keep the development verification store within its limit."""

    store = _get_store()

    if len(store) <= MAX_VERIFICATION_RECORDS:
        return

    ordered = sorted(
        store.items(),
        key=lambda item: item[1].get("created_at") or "",
        reverse=True,
    )

    st.session_state[VERIFICATION_STORE_KEY] = dict(
        ordered[:MAX_VERIFICATION_RECORDS]
    )


def clear_verification_store() -> None:
    """
    Clear development verification records.

    Intended for testing only.
    Never expose this operation to ordinary users.
    """

    st.session_state[VERIFICATION_STORE_KEY] = {}
