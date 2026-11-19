"""
JAK Data Analytics
Connection Health Service

Tracks the health, availability, response time, and connection
history of registered external data sources.

This service uses the data source metadata stored in the
application session. It does not store passwords or API keys.
"""

from __future__ import annotations

from datetime import datetime, timezone
from statistics import mean
from typing import Any, Dict, List, Optional
from uuid import uuid4

import streamlit as st


HEALTH_HISTORY_KEY = "jak_connection_health_history"
HEALTH_STATUS_KEY = "jak_connection_health_status"

VALID_STATUSES = {
    "healthy",
    "degraded",
    "unhealthy",
    "unknown",
}


def _utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


def _history() -> List[Dict[str, Any]]:
    """Get or initialize connection health history."""
    if HEALTH_HISTORY_KEY not in st.session_state:
        st.session_state[HEALTH_HISTORY_KEY] = []

    return st.session_state[HEALTH_HISTORY_KEY]


def _statuses() -> Dict[str, Dict[str, Any]]:
    """Get or initialize the latest health status for each source."""
    if HEALTH_STATUS_KEY not in st.session_state:
        st.session_state[HEALTH_STATUS_KEY] = {}

    return st.session_state[HEALTH_STATUS_KEY]


def classify_health(
    success: bool,
    response_time_ms: Optional[float] = None,
    warning_threshold_ms: float = 3000,
    critical_threshold_ms: float = 10000,
) -> str:
    """
    Classify a connection health result.

    healthy:
        Successful response within the warning threshold.

    degraded:
        Successful response slower than the warning threshold.

    unhealthy:
        Failed connection or response beyond the critical threshold.
    """
    if not success:
        return "unhealthy"

    if response_time_ms is None:
        return "unknown"

    if response_time_ms < 0:
        return "unknown"

    if response_time_ms >= critical_threshold_ms:
        return "unhealthy"

    if response_time_ms >= warning_threshold_ms:
        return "degraded"

    return "healthy"


def record_health_check(
    source_id: str,
    source_name: str,
    source_type: str,
    success: bool,
    response_time_ms: Optional[float] = None,
    message: str = "",
    checked_by: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Record a connection health check.

    This function records the result of a test performed by another
    service. It does not itself connect to external databases or APIs.
    """
    if not source_id:
        raise ValueError("A source ID is required.")

    if not source_name:
        raise ValueError("A source name is required.")

    if response_time_ms is not None and response_time_ms < 0:
        raise ValueError("Response time cannot be negative.")

    status = classify_health(
        success=success,
        response_time_ms=response_time_ms,
    )

    record = {
        "id": str(uuid4()),
        "source_id": str(source_id),
        "source_name": str(source_name),
        "source_type": str(source_type).lower(),
        "status": status,
        "success": bool(success),
        "response_time_ms": (
            round(float(response_time_ms), 2)
            if response_time_ms is not None
            else None
        ),
        "message": str(message)[:1000],
        "checked_by": checked_by,
        "checked_at": _utc_now().isoformat(),
    }

    history = _history()
    history.append(record)

    statuses = _statuses()
    statuses[str(source_id)] = record

    return record


def get_latest_health(source_id: str) -> Dict[str, Any]:
    """Get the latest health check for one source."""
    return _statuses().get(
        str(source_id),
        {
            "source_id": str(source_id),
            "status": "unknown",
            "success": None,
            "response_time_ms": None,
            "message": "No health check has been recorded.",
            "checked_at": None,
        },
    )


def get_all_latest_health() -> List[Dict[str, Any]]:
    """Get the latest health result for every monitored source."""
    return list(_statuses().values())


def get_health_history(
    source_id: Optional[str] = None,
    limit: Optional[int] = 100,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve connection health history with optional filters."""
    records = list(_history())

    if source_id:
        records = [
            item for item in records
            if item.get("source_id") == str(source_id)
        ]

    if status:
        normalized_status = status.lower()

        if normalized_status not in VALID_STATUSES:
            raise ValueError("Invalid health status.")

        records = [
            item for item in records
            if item.get("status") == normalized_status
        ]

    records.sort(
        key=lambda item: item.get("checked_at", ""),
        reverse=True,
    )

    if limit is not None:
        if limit < 1:
            raise ValueError("Limit must be greater than zero.")

        records = records[:limit]

    return records


def get_source_health_summary(source_id: str) -> Dict[str, Any]:
    """Calculate health statistics for one data source."""
    records = get_health_history(
        source_id=source_id,
        limit=None,
    )

    successful = [
        item for item in records
        if item.get("success") is True
    ]

    failed = [
        item for item in records
        if item.get("success") is False
    ]

    response_times = [
        item["response_time_ms"]
        for item in successful
        if item.get("response_time_ms") is not None
    ]

    total = len(records)

    uptime = (
        len(successful) / total * 100
        if total
        else None
    )

    latest = get_latest_health(source_id)

    return {
        "source_id": str(source_id),
        "total_checks": total,
        "successful_checks": len(successful),
        "failed_checks": len(failed),
        "uptime_percentage": (
            round(uptime, 2)
            if uptime is not None
            else None
        ),
        "average_response_time_ms": (
            round(mean(response_times), 2)
            if response_times
            else None
        ),
        "minimum_response_time_ms": (
            round(min(response_times), 2)
            if response_times
            else None
        ),
        "maximum_response_time_ms": (
            round(max(response_times), 2)
            if response_times
            else None
        ),
        "latest_status": latest.get("status", "unknown"),
        "last_checked": latest.get("checked_at"),
    }


def get_platform_health_summary() -> Dict[str, Any]:
    """Calculate overall health statistics for all monitored sources."""
    latest_records = get_all_latest_health()

    counts = {
        "healthy": 0,
        "degraded": 0,
        "unhealthy": 0,
        "unknown": 0,
    }

    for record in latest_records:
        status = record.get("status", "unknown")

        if status not in counts:
            status = "unknown"

        counts[status] += 1

    response_times = [
        item["response_time_ms"]
        for item in latest_records
        if item.get("response_time_ms") is not None
    ]

    total = len(latest_records)

    return {
        "total_sources": total,
        "healthy_sources": counts["healthy"],
        "degraded_sources": counts["degraded"],
        "unhealthy_sources": counts["unhealthy"],
        "unknown_sources": counts["unknown"],
        "average_response_time_ms": (
            round(mean(response_times), 2)
            if response_times
            else None
        ),
        "health_percentage": (
            round(
                (counts["healthy"] / total) * 100,
                2,
            )
            if total
            else None
        ),
    }


def clear_source_health_history(source_id: str) -> int:
    """
    Delete health history for one source from the current session.

    Returns the number of deleted records.
    """
    source_id = str(source_id)
    history = _history()

    remaining = [
        item for item in history
        if item.get("source_id") != source_id
    ]

    deleted_count = len(history) - len(remaining)

    st.session_state[HEALTH_HISTORY_KEY] = remaining
    _statuses().pop(source_id, None)

    return deleted_count


def clear_all_health_history() -> int:
    """Clear all connection health history from the current session."""
    history = _history()
    deleted_count = len(history)

    st.session_state[HEALTH_HISTORY_KEY] = []
    st.session_state[HEALTH_STATUS_KEY] = {}

    return deleted_count


def export_health_history() -> List[Dict[str, Any]]:
    """Return health history in a format suitable for CSV or JSON export."""
    return get_health_history(limit=None)


def get_health_status_label(status: str) -> str:
    """Return a readable label for a health status."""
    labels = {
        "healthy": "Healthy",
        "degraded": "Degraded",
        "unhealthy": "Unhealthy",
        "unknown": "Unknown",
    }

    return labels.get(str(status).lower(), "Unknown")


def get_health_status_color(status: str) -> str:
    """Return a UI color for a health status."""
    colors = {
        "healthy": "#16A34A",
        "degraded": "#F59E0B",
        "unhealthy": "#DC2626",
        "unknown": "#64748B",
    }

    return colors.get(str(status).lower(), "#64748B")
