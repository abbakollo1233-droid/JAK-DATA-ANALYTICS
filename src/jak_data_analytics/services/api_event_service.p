"""
JAK Data Analytics - API Event Service

Central event management system.

Features:
- Register application event types.
- Publish application events.
- Generate unique event identifiers.
- Store event history.
- Retrieve and filter events.
- Dispatch events to webhook subscribers.
- Track event processing status.
- Retry failed event dispatches.
- Export event records.

Development storage:
- Uses Streamlit session state.

Production requirements:
- Persist events in a database.
- Use a durable message queue.
- Implement background event processing.
- Add idempotency protection.
- Apply user and tenant authorization.
"""

from __future__ import annotations

import json
import uuid

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import streamlit as st


# ============================================================
# CONSTANTS
# ============================================================

EVENTS_KEY = "jak_api_events"
EVENT_TYPES_KEY = "jak_api_event_types"

EVENT_STATUSES = {
    "pending",
    "processing",
    "completed",
    "failed",
}

DEFAULT_EVENT_TYPES = {
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
# STORAGE HELPERS
# ============================================================

def _ensure_storage() -> None:
    if EVENTS_KEY not in st.session_state:
        st.session_state[EVENTS_KEY] = {}

    if EVENT_TYPES_KEY not in st.session_state:
        st.session_state[EVENT_TYPES_KEY] = set(
            DEFAULT_EVENT_TYPES
        )


def _get_events() -> Dict[str, Dict[str, Any]]:
    _ensure_storage()
    return st.session_state[EVENTS_KEY]


def _get_event_types() -> set:
    _ensure_storage()
    return st.session_state[EVENT_TYPES_KEY]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _utc_now().isoformat()


def _serialize(data: Any) -> str:
    try:
        return json.dumps(
            data,
            ensure_ascii=False,
            default=str,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Event data must be JSON serializable."
        ) from exc


# ============================================================
# EVENT TYPE MANAGEMENT
# ============================================================

def register_event_type(
    event_name: str,
) -> Dict[str, Any]:
    """
    Register a new application event type.
    """

    if not isinstance(event_name, str):
        raise ValueError("Event name must be a string.")

    event_name = event_name.strip()

    if not event_name:
        raise ValueError("Event name is required.")

    if len(event_name) > 100:
        raise ValueError(
            "Event name cannot exceed 100 characters."
        )

    if any(character.isspace() for character in event_name):
        raise ValueError(
            "Event names cannot contain spaces."
        )

    event_types = _get_event_types()

    if event_name in event_types:
        return {
            "success": True,
            "event_name": event_name,
            "message": "Event type is already registered.",
        }

    event_types.add(event_name)

    return {
        "success": True,
        "event_name": event_name,
        "message": "Event type registered successfully.",
    }


def unregister_event_type(
    event_name: str,
) -> bool:
    """
    Remove an event type from the registry.

    Existing event history is preserved.
    """

    if event_name in DEFAULT_EVENT_TYPES:
        raise ValueError(
            "Built-in event types cannot be removed."
        )

    event_types = _get_event_types()

    if event_name not in event_types:
        return False

    event_types.remove(event_name)

    return True


def list_event_types() -> List[str]:
    return sorted(_get_event_types())


def is_event_type_registered(
    event_name: str,
) -> bool:
    return event_name in _get_event_types()


# ============================================================
# EVENT VALIDATION
# ============================================================

def validate_event_data(
    event_name: str,
    data: Dict[str, Any],
) -> Dict[str, Any]:

    if not isinstance(event_name, str):
        raise ValueError("Event name must be a string.")

    event_name = event_name.strip()

    if event_name not in _get_event_types():
        raise ValueError(
            f"Event type '{event_name}' is not registered."
        )

    if not isinstance(data, dict):
        raise ValueError(
            "Event data must be a dictionary."
        )

    if len(_serialize(data)) > 1_000_000:
        raise ValueError(
            "Event data cannot exceed 1 MB."
        )

    return data


# ============================================================
# EVENT CREATION
# ============================================================

def create_event(
    event_name: str,
    data: Dict[str, Any],
    user_id: Optional[str] = None,
    source: str = "application",
    event_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create and store an application event.

    An optional event_id supports idempotency within the
    current session. Production implementations must enforce
    uniqueness transactionally in persistent storage.
    """

    data = validate_event_data(
        event_name,
        data,
    )

    if not isinstance(source, str) or not source.strip():
        raise ValueError("Event source is required.")

    if metadata is None:
        metadata = {}

    if not isinstance(metadata, dict):
        raise ValueError(
            "Event metadata must be a dictionary."
        )

    if event_id is not None:
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("Event ID must be a valid string.")

        event_id = event_id.strip()

        if event_id in _get_events():
            return dict(_get_events()[event_id])

    else:
        event_id = str(uuid.uuid4())

    record = {
        "id": event_id,
        "event_name": event_name,
        "data": data,
        "user_id": (
            str(user_id)
            if user_id is not None
            else None
        ),
        "source": source.strip(),
        "metadata": metadata,
        "status": "pending",
        "created_at": _iso_now(),
        "updated_at": _iso_now(),
        "processed_at": None,
        "processing_attempts": 0,
        "last_error": None,
        "dispatch_result": None,
    }

    _get_events()[event_id] = record

    return dict(record)


# ============================================================
# EVENT RETRIEVAL
# ============================================================

def get_event(
    event_id: str,
) -> Optional[Dict[str, Any]]:

    record = _get_events().get(str(event_id))

    if not record:
        return None

    return dict(record)


def list_events(
    event_name: Optional[str] = None,
    status: Optional[str] = None,
    user_id: Optional[str] = None,
    source: Optional[str] = None,
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

    if status is not None and status not in EVENT_STATUSES:
        raise ValueError("Invalid event status.")

    results = []

    for event in _get_events().values():

        if event_name is not None:
            if event["event_name"] != event_name:
                continue

        if status is not None:
            if event["status"] != status:
                continue

        if user_id is not None:
            if event["user_id"] != str(user_id):
                continue

        if source is not None:
            if event["source"] != source:
                continue

        results.append(dict(event))

    results.sort(
        key=lambda item: item["created_at"],
        reverse=True,
    )

    return results[:limit]


# ============================================================
# EVENT STATUS MANAGEMENT
# ============================================================

def update_event_status(
    event_id: str,
    status: str,
    error: Optional[str] = None,
) -> Dict[str, Any]:

    if status not in EVENT_STATUSES:
        raise ValueError("Invalid event status.")

    event = _get_events().get(str(event_id))

    if not event:
        raise ValueError("Event was not found.")

    if event["status"] == "completed":
        raise ValueError(
            "Completed events cannot be modified."
        )

    event["status"] = status
    event["updated_at"] = _iso_now()

    if status == "processing":
        event["processing_attempts"] += 1

    if status == "completed":
        event["processed_at"] = _iso_now()
        event["last_error"] = None

    elif status == "failed":
        event["last_error"] = (
            str(error)[:1000]
            if error is not None
            else "Event processing failed."
        )

    return dict(event)


# ============================================================
# WEBHOOK EVENT DISPATCH
# ============================================================

def dispatch_event(
    event_id: str,
    timeout: int = 15,
) -> Dict[str, Any]:
    """
    Dispatch an event to matching webhook subscribers.

    This function uses the API webhook dispatch service.
    """

    event = _get_events().get(str(event_id))

    if not event:
        raise ValueError("Event was not found.")

    if event["status"] == "completed":
        raise ValueError(
            "Event has already been completed."
        )

    update_event_status(
        event_id,
        "processing",
    )

    try:
        from src.jak_data_analytics.services.api_webhook_dispatch_service import (
            dispatch_event_to_all_subscribers,
        )

        result = dispatch_event_to_all_subscribers(
            event_name=event["event_name"],
            payload={
                "id": event["id"],
                "type": event["event_name"],
                "created_at": event["created_at"],
                "api_version": "v1",
                "data": event["data"],
            },
            user_id=event["user_id"],
            timeout=timeout,
        )

        event["dispatch_result"] = result

        # An event with no subscribers is still successfully
        # processed. Failed deliveries are tracked separately.
        update_event_status(
            event_id,
            "completed",
        )

        return {
            "success": True,
            "event_id": event_id,
            "event_status": "completed",
            "dispatch_result": result,
        }

    except Exception as exc:
        update_event_status(
            event_id,
            "failed",
            error=str(exc),
        )

        return {
            "success": False,
            "event_id": event_id,
            "event_status": "failed",
            "message": "Event dispatch failed.",
        }


# ============================================================
# PUBLISH EVENT
# ============================================================

def publish_event(
    event_name: str,
    data: Dict[str, Any],
    user_id: Optional[str] = None,
    source: str = "application",
    dispatch: bool = True,
) -> Dict[str, Any]:
    """
    Create an event and optionally dispatch it immediately.

    Set dispatch=False to create an event for later processing.
    """

    event = create_event(
        event_name=event_name,
        data=data,
        user_id=user_id,
        source=source,
    )

    if not dispatch:
        return {
            "success": True,
            "event_id": event["id"],
            "status": "pending",
            "message": "Event created and waiting for processing.",
        }

    return dispatch_event(event["id"])


# ============================================================
# PENDING EVENT PROCESSING
# ============================================================

def process_pending_events(
    maximum_items: int = 50,
) -> Dict[str, Any]:

    if (
        isinstance(maximum_items, bool)
        or not isinstance(maximum_items, int)
        or maximum_items < 1
        or maximum_items > 500
    ):
        raise ValueError(
            "Maximum items must be between 1 and 500."
        )

    pending = list_events(
        status="pending",
        limit=maximum_items,
    )

    results = []

    for event in pending:
        results.append(
            dispatch_event(event["id"])
        )

    successful = sum(
        item["success"] is True
        for item in results
    )

    return {
        "total_processed": len(results),
        "successful": successful,
        "failed": len(results) - successful,
        "results": results,
        "processed_at": _iso_now(),
    }


# ============================================================
# EVENT STATISTICS
# ============================================================

def get_event_statistics(
    user_id: Optional[str] = None,
) -> Dict[str, Any]:

    events = list_events(
        user_id=user_id,
        limit=1000,
    )

    counts = {
        status: 0
        for status in EVENT_STATUSES
    }

    event_type_counts = {}

    for event in events:
        counts[event["status"]] += 1

        name = event["event_name"]

        event_type_counts[name] = (
            event_type_counts.get(name, 0) + 1
        )

    return {
        "total_events": len(events),
        "pending_events": counts["pending"],
        "processing_events": counts["processing"],
        "completed_events": counts["completed"],
        "failed_events": counts["failed"],
        "event_types_used": len(event_type_counts),
        "event_type_counts": event_type_counts,
        "generated_at": _iso_now(),
    }


# ============================================================
# EXPORT
# ============================================================

def export_events(
    user_id: Optional[str] = None,
    limit: int = 1000,
) -> List[Dict[str, Any]]:

    return list_events(
        user_id=user_id,
        limit=limit,
    )


def export_event_data(
    user_id: Optional[str] = None,
) -> Dict[str, Any]:

    return {
        "events": export_events(user_id=user_id),
        "statistics": get_event_statistics(user_id=user_id),
        "event_types": list_event_types(),
        "exported_at": _iso_now(),
    }
