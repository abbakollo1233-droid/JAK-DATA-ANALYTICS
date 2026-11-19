"""
JAK Data Analytics — API Key Service

Provides API key generation, verification, permission scopes,
expiration, revocation, and key management.

Security:
- Uses cryptographically secure random tokens.
- Stores SHA-256 hashes rather than plaintext API keys.
- Shows the plaintext key only when it is created.
- Uses constant-time hash comparison.

Development note:
Records are stored in Streamlit session state.
For production, persist records in the database and enforce
permissions in every API endpoint.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

from datetime import datetime, timedelta, timezone
from typing import Optional, Iterable
from uuid import uuid4

import streamlit as st


API_KEYS_STORE = "jak_api_keys"

API_KEY_PREFIX = "jak_live_"
API_KEY_LENGTH = 48

DEFAULT_SCOPES = {
    "datasets:read",
    "datasets:write",
    "projects:read",
    "projects:write",
    "analysis:read",
    "analysis:run",
    "reports:read",
    "reports:write",
}


class APIKeyError(Exception):
    """Raised when API key operations fail."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _get_store() -> dict:
    """Return the API key record store."""
    if API_KEYS_STORE not in st.session_state:
        st.session_state[API_KEYS_STORE] = {}

    return st.session_state[API_KEYS_STORE]


def _normalize_scopes(
    scopes: Optional[Iterable[str]],
) -> list[str]:
    """Validate and normalize API permission scopes."""
    if scopes is None:
        return sorted(DEFAULT_SCOPES)

    if isinstance(scopes, str):
        raise APIKeyError(
            "Scopes must be a list or another iterable of scope names."
        )

    allowed = DEFAULT_SCOPES

    normalized = set()

    for scope in scopes:
        if not isinstance(scope, str):
            raise APIKeyError("Every scope must be a string.")

        scope = scope.strip().lower()

        if not scope:
            continue

        if scope not in allowed:
            raise APIKeyError(
                f"Unsupported API permission scope: {scope}"
            )

        normalized.add(scope)

    if not normalized:
        raise APIKeyError(
            "An API key must have at least one permission scope."
        )

    return sorted(normalized)


def _hash_key(api_key: str) -> str:
    """Return the SHA-256 hash of an API key."""
    return hashlib.sha256(
        api_key.encode("utf-8")
    ).hexdigest()


def _validate_expiry(
    expires_in_days: Optional[int],
) -> Optional[str]:
    """Calculate an optional API key expiration date."""
    if expires_in_days is None:
        return None

    if (
        isinstance(expires_in_days, bool)
        or not isinstance(expires_in_days, int)
    ):
        raise APIKeyError(
            "Expiration must be a whole number of days."
        )

    if not 1 <= expires_in_days <= 3650:
        raise APIKeyError(
            "Expiration must be between 1 and 3650 days."
        )

    expires_at = _utc_now() + timedelta(
        days=expires_in_days
    )

    return expires_at.isoformat()


def _is_expired(expires_at: Optional[str]) -> bool:
    """Check whether an API key has expired."""
    if not expires_at:
        return False

    try:
        expiry = datetime.fromisoformat(expires_at)

        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)

        return _utc_now() >= expiry

    except (TypeError, ValueError):
        return True


def _public_record(record: dict) -> dict:
    """
    Return API key metadata without exposing its hash
    or plaintext value.
    """
    return {
        "id": record["id"],
        "name": record["name"],
        "user_id": record["user_id"],
        "key_prefix": record["key_prefix"],
        "scopes": list(record["scopes"]),
        "created_at": record["created_at"],
        "expires_at": record["expires_at"],
        "last_used_at": record["last_used_at"],
        "revoked": record["revoked"],
        "revoked_at": record["revoked_at"],
        "is_expired": _is_expired(record["expires_at"]),
    }


def create_api_key(
    user_id: str,
    name: str,
    scopes: Optional[Iterable[str]] = None,
    expires_in_days: Optional[int] = 90,
) -> dict:
    """
    Create a new API key.

    The plaintext API key is returned only once.
    Save it securely because it cannot be retrieved later.
    """
    if not user_id or not str(user_id).strip():
        raise APIKeyError("A valid user ID is required.")

    if not isinstance(name, str) or not name.strip():
        raise APIKeyError("An API key name is required.")

    name = name.strip()

    if len(name) > 100:
        raise APIKeyError(
            "API key name cannot exceed 100 characters."
        )

    normalized_scopes = _normalize_scopes(scopes)

    expires_at = _validate_expiry(expires_in_days)

    raw_secret = secrets.token_urlsafe(API_KEY_LENGTH)

    api_key = f"{API_KEY_PREFIX}{raw_secret}"

    key_hash = _hash_key(api_key)

    key_id = str(uuid4())

    now = _utc_now().isoformat()

    record = {
        "id": key_id,
        "name": name,
        "user_id": str(user_id),
        "key_hash": key_hash,
        "key_prefix": api_key[:18],
        "scopes": normalized_scopes,
        "created_at": now,
        "expires_at": expires_at,
        "last_used_at": None,
        "revoked": False,
        "revoked_at": None,
    }

    store = _get_store()

    if key_hash in store:
        raise APIKeyError(
            "An unexpected API key collision occurred. Try again."
        )

    store[key_hash] = record

    return {
        "id": key_id,
        "name": name,
        "api_key": api_key,
        "key_prefix": record["key_prefix"],
        "scopes": normalized_scopes,
        "created_at": now,
        "expires_at": expires_at,
        "warning": (
            "Copy this API key now. "
            "The plaintext key will not be displayed again."
        ),
    }


def verify_api_key(
    api_key: str,
    required_scope: Optional[str] = None,
    update_last_used: bool = True,
) -> Optional[dict]:
    """
    Verify an API key and optionally check its permission scope.

    Returns safe API key metadata when valid.
    Returns None when invalid, expired, revoked, or unauthorized.
    """
    if not isinstance(api_key, str):
        return None

    api_key = api_key.strip()

    if not api_key.startswith(API_KEY_PREFIX):
        return None

    if len(api_key) > 200:
        return None

    submitted_hash = _hash_key(api_key)

    store = _get_store()

    matched_record = None

    for stored_hash, record in store.items():
        if hmac.compare_digest(
            submitted_hash,
            stored_hash,
        ):
            matched_record = record
            break

    if matched_record is None:
        return None

    if matched_record["revoked"]:
        return None

    if _is_expired(matched_record["expires_at"]):
        return None

    if required_scope:
        required_scope = required_scope.strip().lower()

        if required_scope not in matched_record["scopes"]:
            return None

    if update_last_used:
        matched_record["last_used_at"] = (
            _utc_now().isoformat()
        )

    return _public_record(matched_record)


def get_api_key(
    key_id: str,
    user_id: Optional[str] = None,
) -> Optional[dict]:
    """Retrieve API key metadata by ID."""
    for record in _get_store().values():
        if record["id"] != key_id:
            continue

        if (
            user_id is not None
            and record["user_id"] != str(user_id)
        ):
            return None

        return _public_record(record)

    return None


def list_api_keys(
    user_id: str,
    include_revoked: bool = False,
) -> list[dict]:
    """List API keys belonging to a user."""
    results = []

    for record in _get_store().values():
        if record["user_id"] != str(user_id):
            continue

        if record["revoked"] and not include_revoked:
            continue

        results.append(_public_record(record))

    results.sort(
        key=lambda item: item["created_at"],
        reverse=True,
    )

    return results


def revoke_api_key(
    key_id: str,
    user_id: str,
) -> bool:
    """Revoke an API key belonging to a user."""
    for record in _get_store().values():
        if record["id"] != key_id:
            continue

        if record["user_id"] != str(user_id):
            return False

        if record["revoked"]:
            return False

        record["revoked"] = True
        record["revoked_at"] = _utc_now().isoformat()

        return True

    return False


def revoke_all_api_keys(
    user_id: str,
    except_key_id: Optional[str] = None,
) -> int:
    """Revoke all active API keys belonging to a user."""
    revoked_count = 0

    for record in _get_store().values():
        if record["user_id"] != str(user_id):
            continue

        if record["id"] == except_key_id:
            continue

        if record["revoked"]:
            continue

        record["revoked"] = True
        record["revoked_at"] = _utc_now().isoformat()

        revoked_count += 1

    return revoked_count


def update_api_key_scopes(
    key_id: str,
    user_id: str,
    scopes: Iterable[str],
) -> bool:
    """Replace the permission scopes assigned to an API key."""
    normalized_scopes = _normalize_scopes(scopes)

    for record in _get_store().values():
        if record["id"] != key_id:
            continue

        if record["user_id"] != str(user_id):
            return False

        if record["revoked"]:
            return False

        record["scopes"] = normalized_scopes

        return True

    return False


def get_api_key_statistics(user_id: str) -> dict:
    """Return API key statistics for a user."""
    records = [
        record
        for record in _get_store().values()
        if record["user_id"] == str(user_id)
    ]

    active = [
        record for record in records
        if not record["revoked"]
        and not _is_expired(record["expires_at"])
    ]

    expired = [
        record for record in records
        if not record["revoked"]
        and _is_expired(record["expires_at"])
    ]

    revoked = [
        record for record in records
        if record["revoked"]
    ]

    return {
        "total": len(records),
        "active": len(active),
        "expired": len(expired),
        "revoked": len(revoked),
        "used": sum(
            1 for record in records
            if record["last_used_at"] is not None
        ),
        "unused": sum(
            1 for record in records
            if record["last_used_at"] is None
        ),
    }


def cleanup_expired_api_keys(
    user_id: Optional[str] = None,
) -> int:
    """
    Revoke expired API keys.

    Records are retained for auditing rather than deleted.
    """
    count = 0

    for record in _get_store().values():
        if user_id is not None:
            if record["user_id"] != str(user_id):
                continue

        if record["revoked"]:
            continue

        if _is_expired(record["expires_at"]):
            record["revoked"] = True
            record["revoked_at"] = _utc_now().isoformat()
            count += 1

    return count


def get_available_api_scopes() -> list[str]:
    """Return the supported API permission scopes."""
    return sorted(DEFAULT_SCOPES)
