"""
JAK Data Analytics - API Webhook Service

Provides framework-independent webhook management.

Features:
- Register and manage webhook endpoints.
- Subscribe endpoints to application events.
- Generate and verify HMAC-SHA256 signatures.
- Build webhook delivery payloads.
- Record delivery attempts.
- Track delivery status and retry metadata.
- Schedule retry metadata for failed deliveries.
- Disable and enable webhook endpoints.
- Filter delivery history.
- Generate webhook statistics.
- Export webhook records.

Development storage:
- Uses Streamlit session state.

Production requirements:
- Persist webhook records in a database.
- Store webhook secrets encrypted.
- Deliver events through a background worker.
- Implement persistent retry scheduling.
- Apply SSRF protection to destination URLs.
- Never expose webhook secrets in API responses or logs.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import uuid

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

import streamlit as st


# ============================================================
# CONSTANTS
# ============================================================

WEBHOOKS_KEY = "jak_api_webhooks"
DELIVERIES_KEY = "jak_api_webhook_deliveries"

WEBHOOK_STATUSES = {
    "active",
    "inactive",
}

DELIVERY_STATUSES = {
    "pending",
    "delivered",
    "failed",
    "retry_scheduled",
}

DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_RETRY_DELAY_SECONDS = 60

ALLOWED_EVENTS = {
    "user.created",
    "user.updated",
    "user.deleted",
    "project.created",
    "project.updated",
    "project.deleted",
    "dataset.uploaded",
    "dataset.updated",
    "dataset.deleted",
    "analysis.completed",
    "report.generated",
    "report.exported",
    "prediction.completed",
    "forecast.completed",
    "data.quality.checked",
    "api.key.created",
    "api.key.revoked",
    "system.notification",
}


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

    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(
                str(value).replace("Z", "+00:00")
            )
        except (TypeError, ValueError):
            return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def _ensure_storage() -> None:
    if WEBHOOKS_KEY not in st.session_state:
        st.session_state[WEBHOOKS_KEY] = {}

    if DELIVERIES_KEY not in st.session_state:
        st.session_state[DELIVERIES_KEY] = {}


def _get_webhooks() -> Dict[str, Dict[str, Any]]:
    _ensure_storage()
    return st.session_state[WEBHOOKS_KEY]


def _get_deliveries() -> Dict[str, Dict[str, Any]]:
    _ensure_storage()
    return st.session_state[DELIVERIES_KEY]


def _safe_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")

    value = value.strip()

    if not value:
        raise ValueError(f"{field_name} is required.")

    return value


def _validate_url(url: str) -> str:
    """
    Basic destination URL validation.

    This is not sufficient SSRF protection for production.
    A production implementation must resolve and block private,
    loopback, link-local, reserved, and internal network addresses,
    including after redirects.
    """

    url = _safe_string(url, "Webhook URL")

    parsed = urlparse(url)

    if parsed.scheme.lower() != "https":
        raise ValueError("Webhook URLs must use HTTPS.")

    if not parsed.hostname:
        raise ValueError("Webhook URL must contain a valid hostname.")

    if parsed.username or parsed.password:
        raise ValueError(
            "Webhook URLs must not contain embedded credentials."
        )

    if parsed.fragment:
        raise ValueError(
            "Webhook URLs must not contain URL fragments."
        )

    return url


def _validate_events(events: Iterable[str]) -> List[str]:
    if isinstance(events, str):
        events = [events]

    if not isinstance(events, (list, tuple, set)):
        raise ValueError("Events must be a list of event names.")

    cleaned = []

    for event in events:
        if not isinstance(event, str):
            raise ValueError("Every event name must be a string.")

        event = event.strip()

        if not event:
            continue

        if event not in ALLOWED_EVENTS:
            raise ValueError(
                f"Unsupported webhook event: {event}"
            )

        if event not in cleaned:
            cleaned.append(event)

    if not cleaned:
        raise ValueError(
            "At least one valid webhook event is required."
        )

    return cleaned


def _validate_max_attempts(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("Maximum attempts must be an integer.")

    if value < 1 or value > 20:
        raise ValueError(
            "Maximum attempts must be between 1 and 20."
        )

    return value


def _validate_retry_delay(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("Retry delay must be an integer.")

    if value < 5 or value > 86400:
        raise ValueError(
            "Retry delay must be between 5 and 86400 seconds."
        )

    return value


def _public_webhook(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return webhook information without exposing its secret.
    """

    result = dict(record)
    result.pop("secret", None)

    return result


def _safe_json(data: Any) -> str:
    try:
        return json.dumps(
            data,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Webhook payload must be JSON serializable."
        ) from exc


# ============================================================
# WEBHOOK REGISTRATION
# ============================================================

def create_webhook(
    name: str,
    url: str,
    events: Iterable[str],
    user_id: Optional[str] = None,
    description: str = "",
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    retry_delay_seconds: int = DEFAULT_RETRY_DELAY_SECONDS,
) -> Dict[str, Any]:
    """
    Register a webhook endpoint.

    The generated secret is returned once in the creation result.
    The stored record keeps the secret for signing deliveries.
    """

    name = _safe_string(name, "Webhook name")
    url = _validate_url(url)
    events = _validate_events(events)

    max_attempts = _validate_max_attempts(max_attempts)
    retry_delay_seconds = _validate_retry_delay(
        retry_delay_seconds
    )

    if description and not isinstance(description, str):
        raise ValueError("Description must be a string.")

    webhook_id = str(uuid.uuid4())
    secret = "whsec_" + secrets.token_urlsafe(32)

    now = _iso_now()

    record = {
        "id": webhook_id,
        "name": name,
        "url": url,
        "description": description.strip(),
        "user_id": str(user_id) if user_id is not None else None,
        "events": events,
        "status": "active",
        "secret": secret,
        "max_attempts": max_attempts,
        "retry_delay_seconds": retry_delay_seconds,
        "created_at": now,
        "updated_at": now,
        "last_delivery_at": None,
        "last_delivery_status": None,
        "total_deliveries": 0,
        "successful_deliveries": 0,
        "failed_deliveries": 0,
    }

    _get_webhooks()[webhook_id] = record

    result = _public_webhook(record)
    result["secret"] = secret
    result["secret_display_warning"] = (
        "Save this secret securely. It will not be shown again."
    )

    return result


def get_webhook(
    webhook_id: str,
    include_secret: bool = False,
) -> Optional[Dict[str, Any]]:
    webhook = _get_webhooks().get(str(webhook_id))

    if not webhook:
        return None

    if include_secret:
        return dict(webhook)

    return _public_webhook(webhook)


def list_webhooks(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    records = []

    for webhook in _get_webhooks().values():
        if user_id is not None:
            if webhook.get("user_id") != str(user_id):
                continue

        if status is not None:
            if webhook.get("status") != status:
                continue

        records.append(_public_webhook(webhook))

    records.sort(
        key=lambda item: item.get("created_at", ""),
        reverse=True,
    )

    return records


def update_webhook(
    webhook_id: str,
    name: Optional[str] = None,
    url: Optional[str] = None,
    events: Optional[Iterable[str]] = None,
    description: Optional[str] = None,
    max_attempts: Optional[int] = None,
    retry_delay_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    webhooks = _get_webhooks()
    webhook_id = str(webhook_id)

    if webhook_id not in webhooks:
        raise ValueError("Webhook was not found.")

    webhook = webhooks[webhook_id]

    if name is not None:
        webhook["name"] = _safe_string(name, "Webhook name")

    if url is not None:
        webhook["url"] = _validate_url(url)

    if events is not None:
        webhook["events"] = _validate_events(events)

    if description is not None:
        if not isinstance(description, str):
            raise ValueError("Description must be a string.")

        webhook["description"] = description.strip()

    if max_attempts is not None:
        webhook["max_attempts"] = _validate_max_attempts(
            max_attempts
        )

    if retry_delay_seconds is not None:
        webhook["retry_delay_seconds"] = _validate_retry_delay(
            retry_delay_seconds
        )

    webhook["updated_at"] = _iso_now()

    return _public_webhook(webhook)


# ============================================================
# WEBHOOK STATUS AND SECRET MANAGEMENT
# ============================================================

def enable_webhook(webhook_id: str) -> Dict[str, Any]:
    return _change_webhook_status(webhook_id, "active")


def disable_webhook(webhook_id: str) -> Dict[str, Any]:
    return _change_webhook_status(webhook_id, "inactive")


def _change_webhook_status(
    webhook_id: str,
    status: str,
) -> Dict[str, Any]:
    if status not in WEBHOOK_STATUSES:
        raise ValueError("Invalid webhook status.")

    webhook = _get_webhooks().get(str(webhook_id))

    if not webhook:
        raise ValueError("Webhook was not found.")

    webhook["status"] = status
    webhook["updated_at"] = _iso_now()

    return _public_webhook(webhook)


def rotate_webhook_secret(webhook_id: str) -> Dict[str, str]:
    """
    Replace the signing secret.

    Existing deliveries signed with the previous secret will no
    longer verify after rotation.
    """

    webhook = _get_webhooks().get(str(webhook_id))

    if not webhook:
        raise ValueError("Webhook was not found.")

    new_secret = "whsec_" + secrets.token_urlsafe(32)

    webhook["secret"] = new_secret
    webhook["updated_at"] = _iso_now()

    return {
        "webhook_id": str(webhook_id),
        "secret": new_secret,
        "message": (
            "Webhook secret rotated. Save the new secret securely."
        ),
    }


def delete_webhook(webhook_id: str) -> bool:
    webhook_id = str(webhook_id)
    webhooks = _get_webhooks()

    if webhook_id not in webhooks:
        return False

    del webhooks[webhook_id]

    return True


# ============================================================
# SIGNATURE GENERATION AND VERIFICATION
# ============================================================

def generate_webhook_signature(
    secret: str,
    payload: Any,
    timestamp: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Generate an HMAC-SHA256 signature.

    Signed message format:
        timestamp.payload

    The receiver should verify both the signature and timestamp.
    """

    secret = _safe_string(secret, "Webhook secret")

    if timestamp is None:
        timestamp = int(_utc_now().timestamp())

    if isinstance(timestamp, bool) or not isinstance(timestamp, int):
        raise ValueError("Timestamp must be an integer.")

    payload_json = _safe_json(payload)

    signed_content = (
        str(timestamp) + "." + payload_json
    ).encode("utf-8")

    signature = hmac.new(
        secret.encode("utf-8"),
        signed_content,
        hashlib.sha256,
    ).hexdigest()

    return {
        "timestamp": timestamp,
        "signature": "sha256=" + signature,
        "signed_payload": payload_json,
    }


def verify_webhook_signature(
    secret: str,
    payload: Any,
    signature: str,
    timestamp: int,
    tolerance_seconds: int = 300,
) -> bool:
    """
    Verify a webhook signature and reject stale timestamps.

    This helper is intended for webhook receiver implementations.
    """

    try:
        secret = _safe_string(secret, "Webhook secret")
        signature = _safe_string(signature, "Signature")

        if isinstance(timestamp, bool) or not isinstance(timestamp, int):
            return False

        if (
            isinstance(tolerance_seconds, bool)
            or not isinstance(tolerance_seconds, int)
            or tolerance_seconds < 0
        ):
            return False

        current_timestamp = int(_utc_now().timestamp())

        if abs(current_timestamp - timestamp) > tolerance_seconds:
            return False

        generated = generate_webhook_signature(
            secret=secret,
            payload=payload,
            timestamp=timestamp,
        )

        return hmac.compare_digest(
            generated["signature"],
            signature,
        )

    except (ValueError, TypeError):
        return False


# ============================================================
# EVENT MATCHING AND PAYLOAD BUILDING
# ============================================================

def get_webhooks_for_event(
    event_name: str,
    user_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Return active webhooks subscribed to an event.

    When user_id is provided, this implementation returns webhooks
    owned by that user and global webhooks with no owner.
    """

    event_name = _safe_string(event_name, "Event name")

    if event_name not in ALLOWED_EVENTS:
        raise ValueError("Unsupported webhook event.")

    matches = []

    for webhook in _get_webhooks().values():
        if webhook["status"] != "active":
            continue

        if event_name not in webhook["events"]:
            continue

        owner = webhook.get("user_id")

        if user_id is not None:
            if owner is not None and owner != str(user_id):
                continue

        matches.append(dict(webhook))

    return matches


def build_webhook_payload(
    event_name: str,
    data: Dict[str, Any],
    event_id: Optional[str] = None,
) -> Dict[str, Any]:
    if event_name not in ALLOWED_EVENTS:
        raise ValueError("Unsupported webhook event.")

    if not isinstance(data, dict):
        raise ValueError("Webhook event data must be a dictionary.")

    payload = {
        "id": event_id or str(uuid.uuid4()),
        "type": event_name,
        "created_at": _iso_now(),
        "api_version": "v1",
        "data": data,
    }

    # Confirm that the payload can be serialized before returning.
    _safe_json(payload)

    return payload


# ============================================================
# DELIVERY RECORDS
# ============================================================

def create_delivery_record(
    webhook_id: str,
    event_name: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    webhook_id = str(webhook_id)

    webhook = _get_webhooks().get(webhook_id)

    if not webhook:
        raise ValueError("Webhook was not found.")

    if webhook["status"] != "active":
        raise ValueError("Webhook is not active.")

    if event_name not in webhook["events"]:
        raise ValueError(
            "Webhook is not subscribed to this event."
        )

    if not isinstance(payload, dict):
        raise ValueError("Payload must be a dictionary.")

    payload_json = _safe_json(payload)

    delivery_id = str(uuid.uuid4())
    now = _iso_now()

    record = {
        "id": delivery_id,
        "webhook_id": webhook_id,
        "event_name": event_name,
        "event_id": payload.get("id"),
        "payload": payload_json,
        "status": "pending",
        "attempt_count": 0,
        "max_attempts": webhook["max_attempts"],
        "created_at": now,
        "updated_at": now,
        "next_retry_at": None,
        "delivered_at": None,
        "last_error": None,
        "attempts": [],
    }

    _get_deliveries()[delivery_id] = record

    return dict(record)


def get_delivery(delivery_id: str) -> Optional[Dict[str, Any]]:
    record = _get_deliveries().get(str(delivery_id))

    if not record:
        return None

    return dict(record)


def list_deliveries(
    webhook_id: Optional[str] = None,
    status: Optional[str] = None,
    event_name: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError("Limit must be an integer.")

    if limit < 1 or limit > 1000:
        raise ValueError("Limit must be between 1 and 1000.")

    if status is not None and status not in DELIVERY_STATUSES:
        raise ValueError("Invalid delivery status.")

    records = []

    for delivery in _get_deliveries().values():
        if webhook_id is not None:
            if delivery["webhook_id"] != str(webhook_id):
                continue

        if status is not None:
            if delivery["status"] != status:
                continue

        if event_name is not None:
            if delivery["event_name"] != event_name:
                continue

        records.append(dict(delivery))

    records.sort(
        key=lambda item: item.get("created_at", ""),
        reverse=True,
    )

    return records[:limit]


# ============================================================
# DELIVERY ATTEMPT TRACKING
# ============================================================

def record_delivery_attempt(
    delivery_id: str,
    success: bool,
    response_status: Optional[int] = None,
    response_body: Optional[str] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Record the result of one delivery attempt.

    This function records metadata only. It does not send HTTP
    requests. A background worker should perform actual delivery.
    """

    delivery_id = str(delivery_id)

    delivery = _get_deliveries().get(delivery_id)

    if not delivery:
        raise ValueError("Delivery record was not found.")

    if delivery["status"] in {"delivered", "failed"}:
        raise ValueError(
            "This delivery has already reached a final status."
        )

    if not isinstance(success, bool):
        raise ValueError("Success must be a boolean.")

    if response_status is not None:
        if (
            isinstance(response_status, bool)
            or not isinstance(response_status, int)
            or response_status < 100
            or response_status > 599
        ):
            raise ValueError("Invalid HTTP response status.")

    if response_body is not None and not isinstance(response_body, str):
        raise ValueError("Response body must be a string.")

    if error is not None and not isinstance(error, str):
        raise ValueError("Error must be a string.")

    webhooks = _get_webhooks()
    webhook = webhooks.get(delivery["webhook_id"])

    if not webhook:
        raise ValueError("Associated webhook was not found.")

    if delivery["attempt_count"] >= delivery["max_attempts"]:
        raise ValueError("Maximum delivery attempts reached.")

    delivery["attempt_count"] += 1

    now = _iso_now()

    attempt = {
        "attempt_number": delivery["attempt_count"],
        "attempted_at": now,
        "success": success,
        "response_status": response_status,
        "response_body": (
            response_body[:1000]
            if response_body is not None
            else None
        ),
        "error": error[:1000] if error else None,
    }

    delivery["attempts"].append(attempt)
    delivery["updated_at"] = now

    webhook["total_deliveries"] += 1
    webhook["last_delivery_at"] = now

    if success:
        delivery["status"] = "delivered"
        delivery["delivered_at"] = now
        delivery["next_retry_at"] = None
        delivery["last_error"] = None

        webhook["successful_deliveries"] += 1
        webhook["last_delivery_status"] = "delivered"

    else:
        delivery["last_error"] = error or (
            f"HTTP delivery failed: {response_status}"
            if response_status is not None
            else "Delivery failed."
        )

        if delivery["attempt_count"] >= delivery["max_attempts"]:
            delivery["status"] = "failed"
            delivery["next_retry_at"] = None

            webhook["failed_deliveries"] += 1
            webhook["last_delivery_status"] = "failed"

        else:
            delay = webhook["retry_delay_seconds"]

            # Exponential backoff, capped at 24 hours.
            multiplier = 2 ** (delivery["attempt_count"] - 1)
            delay = min(delay * multiplier, 86400)

            next_retry = _utc_now() + timedelta(seconds=delay)

            delivery["status"] = "retry_scheduled"
            delivery["next_retry_at"] = next_retry.isoformat()

            webhook["last_delivery_status"] = "retry_scheduled"

    webhook["updated_at"] = now

    return dict(delivery)


# ============================================================
# RETRY MANAGEMENT
# ============================================================

def get_due_retries(
    current_time: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """
    Find deliveries whose retry time has arrived.

    A worker should retrieve these records and attempt delivery.
    """

    if current_time is None:
        current_time = _utc_now()

    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    current_time = current_time.astimezone(timezone.utc)

    due = []

    for delivery in _get_deliveries().values():
        if delivery["status"] != "retry_scheduled":
            continue

        retry_at = _parse_datetime(delivery.get("next_retry_at"))

        if retry_at and retry_at <= current_time:
            due.append(dict(delivery))

    due.sort(
        key=lambda item: item.get("next_retry_at") or ""
    )

    return due


def prepare_delivery_retry(
    delivery_id: str,
) -> Dict[str, Any]:
    """
    Move a due retry back to pending.

    The worker should call this immediately before making a new
    delivery attempt.
    """

    delivery = _get_deliveries().get(str(delivery_id))

    if not delivery:
        raise ValueError("Delivery record was not found.")

    if delivery["status"] != "retry_scheduled":
        raise ValueError(
            "Delivery is not scheduled for retry."
        )

    retry_at = _parse_datetime(delivery.get("next_retry_at"))

    if not retry_at or retry_at > _utc_now():
        raise ValueError("Retry is not due yet.")

    webhook = _get_webhooks().get(delivery["webhook_id"])

    if not webhook or webhook["status"] != "active":
        raise ValueError(
            "Webhook is missing or inactive."
        )

    delivery["status"] = "pending"
    delivery["next_retry_at"] = None
    delivery["updated_at"] = _iso_now()

    return dict(delivery)


def cancel_scheduled_retry(delivery_id: str) -> Dict[str, Any]:
    delivery = _get_deliveries().get(str(delivery_id))

    if not delivery:
        raise ValueError("Delivery record was not found.")

    if delivery["status"] != "retry_scheduled":
        raise ValueError(
            "Delivery does not have a scheduled retry."
        )

    delivery["status"] = "failed"
    delivery["next_retry_at"] = None
    delivery["updated_at"] = _iso_now()
    delivery["last_error"] = (
        delivery.get("last_error")
        or "Scheduled retry was cancelled."
    )

    webhook = _get_webhooks().get(delivery["webhook_id"])

    if webhook:
        webhook["failed_deliveries"] += 1
        webhook["last_delivery_status"] = "failed"
        webhook["updated_at"] = _iso_now()

    return dict(delivery)


# ============================================================
# WEBHOOK STATISTICS
# ============================================================

def get_webhook_statistics(
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    webhooks = list_webhooks(user_id=user_id)

    allowed_ids = {
        item["id"] for item in webhooks
    }

    deliveries = [
        item
        for item in _get_deliveries().values()
        if item["webhook_id"] in allowed_ids
    ]

    status_counts = {
        status: 0
        for status in DELIVERY_STATUSES
    }

    for delivery in deliveries:
        status_counts[delivery["status"]] += 1

    total_attempts = sum(
        delivery["attempt_count"]
        for delivery in deliveries
    )

    delivered = status_counts["delivered"]
    failed = status_counts["failed"]

    completed = delivered + failed

    success_rate = (
        round((delivered / completed) * 100, 2)
        if completed
        else 0.0
    )

    return {
        "total_webhooks": len(webhooks),
        "active_webhooks": sum(
            item["status"] == "active"
            for item in webhooks
        ),
        "inactive_webhooks": sum(
            item["status"] == "inactive"
            for item in webhooks
        ),
        "total_deliveries": len(deliveries),
        "pending_deliveries": status_counts["pending"],
        "scheduled_retries": status_counts["retry_scheduled"],
        "successful_deliveries": delivered,
        "failed_deliveries": failed,
        "total_attempts": total_attempts,
        "success_rate": success_rate,
        "generated_at": _iso_now(),
    }


# ============================================================
# EXPORT
# ============================================================

def export_webhooks(
    user_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Export webhook configuration without secret values.
    """

    return list_webhooks(user_id=user_id)


def export_deliveries(
    webhook_id: Optional[str] = None,
    limit: int = 1000,
) -> List[Dict[str, Any]]:
    """
    Export delivery history.

    Stored payloads are included, so apply appropriate access
    controls before exposing this output to users.
    """

    return list_deliveries(
        webhook_id=webhook_id,
        limit=limit,
    )


def export_webhook_data(
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "webhooks": export_webhooks(user_id=user_id),
        "statistics": get_webhook_statistics(user_id=user_id),
        "exported_at": _iso_now(),
    }
