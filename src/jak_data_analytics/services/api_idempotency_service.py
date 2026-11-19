"""
JAK Data Analytics - API Idempotency Service

Prevents duplicate API operations caused by repeated requests.

Features:
- Generate and validate idempotency keys.
- Store request fingerprints.
- Detect duplicate requests.
- Return previously stored responses.
- Detect conflicting key reuse.
- Track request processing status.
- Expire old idempotency records.
- Provide statistics and export.

Development storage:
- Uses Streamlit session state.

Production requirements:
- Use persistent database or Redis storage.
- Enforce unique keys transactionally.
- Use atomic locking for concurrent requests.
- Scope keys to users and API endpoints.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import streamlit as st


# ============================================================
# CONSTANTS
# ============================================================

IDEMPOTENCY_KEY = "jak_api_idempotency_records"

IDEMPOTENCY_STATUSES = {
    "processing",
    "completed",
    "failed",
}

DEFAULT_EXPIRY_HOURS = 24

MAX_EXPIRY_HOURS = 168

KEY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")


# ============================================================
# STORAGE
# ============================================================

def _ensure_storage() -> None:
    if IDEMPOTENCY_KEY not in st.session_state:
        st.session_state[IDEMPOTENCY_KEY] = {}


def _get_records() -> Dict[str, Dict[str, Any]]:
    _ensure_storage()
    return st.session_state[IDEMPOTENCY_KEY]


# ============================================================
# GENERAL HELPERS
# ============================================================

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _utc_now().isoformat()


def _parse_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)

    except (TypeError, ValueError):
        return None


def _validate_expiry(hours: int) -> int:
    if isinstance(hours, bool) or not isinstance(hours, int):
        raise ValueError("Expiry must be an integer.")

    if hours < 1 or hours > MAX_EXPIRY_HOURS:
        raise ValueError(
            f"Expiry must be between 1 and {MAX_EXPIRY_HOURS} hours."
        )

    return hours


def _validate_key(key: str) -> str:
    if not isinstance(key, str):
        raise ValueError("Idempotency key must be a string.")

    key = key.strip()

    if not KEY_PATTERN.fullmatch(key):
        raise ValueError(
            "Idempotency key must contain 8–128 characters "
            "using letters, numbers, dots, underscores, "
            "colons, or hyphens."
        )

    return key


def _request_fingerprint(
    method: str,
    endpoint: str,
    payload: Any,
) -> str:
    """
    Generate a SHA-256 fingerprint for a request.

    This is used to detect reuse of one idempotency key
    with different request contents.
    """

    if not isinstance(method, str) or not method.strip():
        raise ValueError("HTTP method is required.")

    if not isinstance(endpoint, str) or not endpoint.strip():
        raise ValueError("Endpoint is required.")

    normalized = {
        "method": method.strip().upper(),
        "endpoint": endpoint.strip(),
        "payload": payload,
    }

    try:
        serialized = json.dumps(
            normalized,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Request payload cannot be fingerprinted."
        ) from exc

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()


def _storage_key(
    user_id: Optional[str],
    endpoint: str,
    idempotency_key: str,
) -> str:
    """
    Scope keys by user and endpoint.

    Hashing prevents raw client keys from appearing in
    internal storage identifiers.
    """

    scope = {
        "user_id": str(user_id) if user_id is not None else "anonymous",
        "endpoint": endpoint.strip(),
        "key": idempotency_key,
    }

    serialized = json.dumps(
        scope,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()


# ============================================================
# KEY GENERATION
# ============================================================

def generate_idempotency_key() -> str:
    """
    Generate a client-ready idempotency key.
    """

    return "jak_" + uuid.uuid4().hex


# ============================================================
# RECORD REGISTRATION
# ============================================================

def begin_idempotent_request(
    idempotency_key: str,
    method: str,
    endpoint: str,
    payload: Any,
    user_id: Optional[str] = None,
    expiry_hours: int = DEFAULT_EXPIRY_HOURS,
) -> Dict[str, Any]:
    """
    Register a request before executing its operation.

    Results:
    - started: A new request can proceed.
    - replay: A previous completed response is available.
    - processing: The same request is already being processed.
    - conflict: The key was reused with different contents.
    """

    idempotency_key = _validate_key(idempotency_key)
    expiry_hours = _validate_expiry(expiry_hours)

    fingerprint = _request_fingerprint(
        method,
        endpoint,
        payload,
    )

    record_key = _storage_key(
        user_id,
        endpoint,
        idempotency_key,
    )

    records = _get_records()
    existing = records.get(record_key)

    now = _utc_now()

    if existing:
        expires_at = _parse_datetime(
            existing.get("expires_at")
        )

        if expires_at and expires_at <= now:
            del records[record_key]
            existing = None

    if existing:
        if existing["fingerprint"] != fingerprint:
            return {
                "action": "conflict",
                "success": False,
                "message": (
                    "This idempotency key was already used "
                    "with a different request."
                ),
            }

        if existing["status"] == "completed":
            return {
                "action": "replay",
                "success": True,
                "response": existing.get("response"),
                "http_status": existing.get("http_status"),
                "record_id": existing["id"],
                "message": "Returning the previously stored response.",
            }

        if existing["status"] == "processing":
            return {
                "action": "processing",
                "success": False,
                "record_id": existing["id"],
                "message": (
                    "This request is already being processed."
                ),
            }

        if existing["status"] == "failed":
            return {
                "action": "processing",
                "success": False,
                "record_id": existing["id"],
                "message": (
                    "The previous request failed. "
                    "Use a new idempotency key for a new attempt."
                ),
            }

    record_id = str(uuid.uuid4())

    expires_at = now + timedelta(
        hours=expiry_hours
    )

    record = {
        "id": record_id,
        "idempotency_key_hash": record_key,
        "fingerprint": fingerprint,
        "user_id": (
            str(user_id)
            if user_id is not None
            else None
        ),
        "method": method.strip().upper(),
        "endpoint": endpoint.strip(),
        "status": "processing",
        "response": None,
        "http_status": None,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "completed_at": None,
        "error": None,
    }

    records[record_key] = record

    return {
        "action": "started",
        "success": True,
        "record_id": record_id,
        "message": "Request registered successfully.",
    }


# ============================================================
# RECORD RETRIEVAL
# ============================================================

def get_idempotency_record(
    record_id: str,
) -> Optional[Dict[str, Any]]:

    for record in _get_records().values():
        if record["id"] == str(record_id):
            return dict(record)

    return None


def list_idempotency_records(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:

    if (
        isinstance(limit, bool)
        or not isinstance(limit, int)
        or limit < 1
        or limit > 1000
    ):
        raise ValueError(
            "Limit must be between 1 and 1000."
        )

    if status is not None and status not in IDEMPOTENCY_STATUSES:
        raise ValueError("Invalid idempotency status.")

    results = []

    for record in _get_records().values():

        if user_id is not None:
            if record["user_id"] != str(user_id):
                continue

        if status is not None:
            if record["status"] != status:
                continue

        results.append(dict(record))

    results.sort(
        key=lambda item: item["created_at"],
        reverse=True,
    )

    return results[:limit]


# ============================================================
# COMPLETE REQUEST
# ============================================================

def complete_idempotent_request(
    record_id: str,
    response: Any,
    http_status: int = 200,
) -> Dict[str, Any]:
    """
    Save a successful operation response.

    The response must be JSON serializable so that it can
    be replayed for subsequent matching requests.
    """

    if (
        isinstance(http_status, bool)
        or not isinstance(http_status, int)
        or http_status < 200
        or http_status > 599
    ):
        raise ValueError("Invalid HTTP status code.")

    try:
        json.dumps(
            response,
            ensure_ascii=False,
            default=str,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Response must be JSON serializable."
        ) from exc

    record = _find_record(record_id)

    if not record:
        raise ValueError(
            "Idempotency record was not found."
        )

    if record["status"] != "processing":
        raise ValueError(
            "Only processing requests can be completed."
        )

    record["status"] = "completed"
    record["response"] = response
    record["http_status"] = http_status
    record["completed_at"] = _iso_now()
    record["updated_at"] = _iso_now()
    record["error"] = None

    return dict(record)


# ============================================================
# FAIL REQUEST
# ============================================================

def fail_idempotent_request(
    record_id: str,
    error: str,
) -> Dict[str, Any]:

    if not isinstance(error, str) or not error.strip():
        raise ValueError("Error description is required.")

    record = _find_record(record_id)

    if not record:
        raise ValueError(
            "Idempotency record was not found."
        )

    if record["status"] != "processing":
        raise ValueError(
            "Only processing requests can be marked failed."
        )

    record["status"] = "failed"
    record["error"] = error.strip()[:1000]
    record["updated_at"] = _iso_now()

    return dict(record)


# ============================================================
# INTERNAL LOOKUP
# ============================================================

def _find_record(
    record_id: str,
) -> Optional[Dict[str, Any]]:

    for record in _get_records().values():
        if record["id"] == str(record_id):
            return record

    return None


# ============================================================
# EXPIRATION CLEANUP
# ============================================================

def cleanup_expired_idempotency_records(
    current_time: Optional[datetime] = None,
) -> Dict[str, Any]:

    if current_time is None:
        current_time = _utc_now()

    if current_time.tzinfo is None:
        current_time = current_time.replace(
            tzinfo=timezone.utc
        )

    current_time = current_time.astimezone(
        timezone.utc
    )

    records = _get_records()

    expired_keys = []

    for key, record in records.items():

        expires_at = _parse_datetime(
            record.get("expires_at")
        )

        if expires_at and expires_at <= current_time:
            expired_keys.append(key)

    for key in expired_keys:
        del records[key]

    return {
        "deleted_records": len(expired_keys),
        "remaining_records": len(records),
        "cleaned_at": _iso_now(),
    }


# ============================================================
# STATISTICS
# ============================================================

def get_idempotency_statistics(
    user_id: Optional[str] = None,
) -> Dict[str, Any]:

    records = list_idempotency_records(
        user_id=user_id,
        limit=1000,
    )

    counts = {
        status: 0
        for status in IDEMPOTENCY_STATUSES
    }

    for record in records:
        counts[record["status"]] += 1

    total = len(records)

    return {
        "total_records": total,
        "processing_records": counts["processing"],
        "completed_records": counts["completed"],
        "failed_records": counts["failed"],
        "completion_rate": (
            round(
                counts["completed"] / total * 100,
                2,
            )
            if total
            else 0.0
        ),
        "generated_at": _iso_now(),
    }


# ============================================================
# EXPORT
# ============================================================

def export_idempotency_records(
    user_id: Optional[str] = None,
    limit: int = 1000,
) -> List[Dict[str, Any]]:

    return list_idempotency_records(
        user_id=user_id,
        limit=limit,
    )


def export_idempotency_data(
    user_id: Optional[str] = None,
) -> Dict[str, Any]:

    return {
        "records": export_idempotency_records(
            user_id=user_id
        ),
        "statistics": get_idempotency_statistics(
            user_id=user_id
        ),
        "exported_at": _iso_now(),
    }
