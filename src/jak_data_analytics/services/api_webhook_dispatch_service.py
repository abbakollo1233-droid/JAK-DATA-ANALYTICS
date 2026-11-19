"""
JAK Data Analytics - API Webhook Dispatch Service

Handles actual HTTP webhook delivery.

Features:
- Send webhook events to registered endpoints.
- Sign requests using HMAC-SHA256.
- Include event and delivery identifiers.
- Record HTTP responses and failures.
- Process scheduled retries.
- Apply request timeouts.
- Disable automatic HTTP redirects.
- Return structured delivery results.

Dependencies:
    pip install requests

Security:
- Webhook destinations must be HTTPS.
- Redirects are disabled.
- Production deployments must enforce SSRF protection
  through destination allowlists and network egress controls.
- Never log webhook secrets or full sensitive payloads.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests

from src.jak_data_analytics.services.api_webhook_service import (
    create_delivery_record,
    generate_webhook_signature,
    get_due_retries,
    get_webhook,
    prepare_delivery_retry,
    record_delivery_attempt,
)


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_TIMEOUT = 15

MAX_TIMEOUT = 60

USER_AGENT = "JAK-Data-Analytics-Webhooks/1.0"

RETRYABLE_STATUS_CODES = {
    408,
    425,
    429,
    500,
    502,
    503,
    504,
}


# ============================================================
# VALIDATION
# ============================================================

def _validate_timeout(timeout: int) -> int:
    if isinstance(timeout, bool) or not isinstance(timeout, int):
        raise ValueError("Timeout must be an integer.")

    if timeout < 1 or timeout > MAX_TIMEOUT:
        raise ValueError(
            f"Timeout must be between 1 and {MAX_TIMEOUT} seconds."
        )

    return timeout


def _validate_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Webhook payload must be a dictionary.")

    try:
        json.dumps(payload, ensure_ascii=False, default=str)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Webhook payload must be JSON serializable."
        ) from exc

    return payload


# ============================================================
# HTTP REQUEST HEADERS
# ============================================================

def build_webhook_headers(
    webhook_secret: str,
    payload: Dict[str, Any],
    delivery_id: str,
    event_name: str,
) -> Dict[str, str]:
    signed = generate_webhook_signature(
        secret=webhook_secret,
        payload=payload,
    )

    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
        "X-JAK-Event": event_name,
        "X-JAK-Delivery": delivery_id,
        "X-JAK-Timestamp": str(signed["timestamp"]),
        "X-JAK-Signature": signed["signature"],
        "X-JAK-Webhook-Version": "1",
    }


# ============================================================
# RESPONSE HANDLING
# ============================================================

def _get_response_body(
    response: requests.Response,
    maximum_length: int = 1000,
) -> str:
    try:
        return response.text[:maximum_length]
    except Exception:
        return ""


def _is_success_response(
    response: requests.Response,
) -> bool:
    return 200 <= response.status_code < 300


# ============================================================
# DELIVERY EXECUTION
# ============================================================

def send_webhook_delivery(
    delivery_id: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """
    Send an existing pending webhook delivery.

    The delivery must already exist in the webhook service.

    This function:
    1. Loads the delivery and webhook.
    2. Retrieves the signing secret.
    3. Signs the payload.
    4. Sends the HTTP POST request.
    5. Records the delivery attempt.
    """

    timeout = _validate_timeout(timeout)

    from src.jak_data_analytics.services.api_webhook_service import (
        get_delivery,
    )

    delivery = get_delivery(delivery_id)

    if not delivery:
        raise ValueError("Delivery record was not found.")

    if delivery["status"] != "pending":
        raise ValueError(
            "Only pending deliveries can be sent."
        )

    webhook = get_webhook(
        delivery["webhook_id"],
        include_secret=True,
    )

    if not webhook:
        raise ValueError("Webhook was not found.")

    if webhook["status"] != "active":
        raise ValueError("Webhook is inactive.")

    secret = webhook.get("secret")

    if not secret:
        raise ValueError("Webhook signing secret is unavailable.")

    try:
        payload = json.loads(delivery["payload"])
    except (TypeError, json.JSONDecodeError):
        raise ValueError("Stored webhook payload is invalid.")

    payload = _validate_payload(payload)

    headers = build_webhook_headers(
        webhook_secret=secret,
        payload=payload,
        delivery_id=delivery["id"],
        event_name=delivery["event_name"],
    )

    try:
        response = requests.post(
            webhook["url"],
            json=payload,
            headers=headers,
            timeout=timeout,
            allow_redirects=False,
        )

        success = _is_success_response(response)

        response_body = _get_response_body(response)

        result = record_delivery_attempt(
            delivery_id=delivery_id,
            success=success,
            response_status=response.status_code,
            response_body=response_body,
            error=None if success else (
                f"Webhook endpoint returned HTTP "
                f"{response.status_code}."
            ),
        )

        return {
            "success": success,
            "delivery_id": delivery_id,
            "status": result["status"],
            "http_status": response.status_code,
            "attempt_count": result["attempt_count"],
            "message": (
                "Webhook delivered successfully."
                if success
                else "Webhook endpoint returned an unsuccessful response."
            ),
        }

    except requests.exceptions.Timeout:
        return _record_transport_failure(
            delivery_id,
            "Webhook request timed out.",
        )

    except requests.exceptions.SSLError:
        return _record_transport_failure(
            delivery_id,
            "Webhook SSL verification failed.",
        )

    except requests.exceptions.ConnectionError:
        return _record_transport_failure(
            delivery_id,
            "Could not connect to the webhook endpoint.",
        )

    except requests.exceptions.RequestException:
        return _record_transport_failure(
            delivery_id,
            "Webhook HTTP request failed.",
        )


def _record_transport_failure(
    delivery_id: str,
    error: str,
) -> Dict[str, Any]:
    result = record_delivery_attempt(
        delivery_id=delivery_id,
        success=False,
        error=error,
    )

    return {
        "success": False,
        "delivery_id": delivery_id,
        "status": result["status"],
        "http_status": None,
        "attempt_count": result["attempt_count"],
        "message": error,
    }


# ============================================================
# EVENT DISPATCH
# ============================================================

def dispatch_webhook_event(
    webhook_id: str,
    event_name: str,
    payload: Dict[str, Any],
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """
    Create and immediately send one webhook event.

    The webhook must be active and subscribed to the event.
    """

    timeout = _validate_timeout(timeout)
    payload = _validate_payload(payload)

    delivery = create_delivery_record(
        webhook_id=webhook_id,
        event_name=event_name,
        payload=payload,
    )

    return send_webhook_delivery(
        delivery_id=delivery["id"],
        timeout=timeout,
    )


def dispatch_event_to_all_subscribers(
    event_name: str,
    payload: Dict[str, Any],
    user_id: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """
    Deliver an event to all matching active webhook subscribers.

    Each destination receives its own delivery record.
    """

    from src.jak_data_analytics.services.api_webhook_service import (
        get_webhooks_for_event,
    )

    timeout = _validate_timeout(timeout)
    payload = _validate_payload(payload)

    subscribers = get_webhooks_for_event(
        event_name=event_name,
        user_id=user_id,
    )

    results = []

    for webhook in subscribers:
        try:
            result = dispatch_webhook_event(
                webhook_id=webhook["id"],
                event_name=event_name,
                payload=payload,
                timeout=timeout,
            )

            results.append(result)

        except Exception:
            results.append({
                "success": False,
                "webhook_id": webhook["id"],
                "status": "dispatch_error",
                "message": "Webhook dispatch could not be completed.",
            })

    successful = sum(
        item.get("success") is True
        for item in results
    )

    return {
        "event_name": event_name,
        "total_subscribers": len(subscribers),
        "successful_deliveries": successful,
        "failed_deliveries": len(results) - successful,
        "results": results,
        "dispatched_at": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# RETRY PROCESSING
# ============================================================

def process_due_webhook_retries(
    timeout: int = DEFAULT_TIMEOUT,
    maximum_items: int = 50,
) -> Dict[str, Any]:
    """
    Process deliveries whose retry time has arrived.

    This function can later be called by a Celery worker
    or another background task scheduler.
    """

    timeout = _validate_timeout(timeout)

    if (
        isinstance(maximum_items, bool)
        or not isinstance(maximum_items, int)
        or maximum_items < 1
        or maximum_items > 500
    ):
        raise ValueError(
            "Maximum items must be between 1 and 500."
        )

    due_deliveries = get_due_retries()[:maximum_items]

    results = []

    for delivery in due_deliveries:
        try:
            prepared = prepare_delivery_retry(
                delivery["id"]
            )

            result = send_webhook_delivery(
                delivery_id=prepared["id"],
                timeout=timeout,
            )

            results.append(result)

        except Exception:
            results.append({
                "success": False,
                "delivery_id": delivery["id"],
                "status": "retry_error",
                "message": "Retry processing failed.",
            })

    successful = sum(
        item.get("success") is True
        for item in results
    )

    return {
        "total_due": len(due_deliveries),
        "processed": len(results),
        "successful": successful,
        "failed": len(results) - successful,
        "results": results,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# CONNECTION TEST
# ============================================================

def test_webhook_endpoint(
    webhook_id: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """
    Test an endpoint using a real signed test event.

    A test delivery is recorded like a normal delivery.
    """

    test_payload = {
        "id": "test_" + datetime.now(timezone.utc).strftime(
            "%Y%m%d%H%M%S"
        ),
        "type": "system.notification",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "api_version": "v1",
        "data": {
            "message": "JAK webhook connection test.",
            "test": True,
        },
    }

    return dispatch_webhook_event(
        webhook_id=webhook_id,
        event_name="system.notification",
        payload=test_payload,
        timeout=timeout,
    )
