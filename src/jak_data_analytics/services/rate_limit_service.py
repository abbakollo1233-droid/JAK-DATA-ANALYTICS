"""
JAK Data Analytics - Rate Limit Service

Provides basic sliding-window rate limiting for development.

IMPORTANT:
This implementation stores counters in Streamlit session state.
It is not sufficient for production security because different
users and browser sessions may have separate state.

Production should use a shared backend such as Redis or a
database-backed rate limiter.
"""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Any, Deque, Dict, Optional
import hashlib

import streamlit as st


RATE_LIMIT_STATE_KEY = "jak_rate_limit_events"
BLOCK_STATE_KEY = "jak_rate_limit_blocks"


DEFAULT_LIMIT = 60
DEFAULT_WINDOW_SECONDS = 60
DEFAULT_BLOCK_SECONDS = 300

MAX_TRACKED_KEYS = 5000


def _utc_now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(timezone.utc)


def _get_event_store() -> Dict[str, Deque[datetime]]:
    """Get or initialize the event store."""

    store = st.session_state.get(RATE_LIMIT_STATE_KEY)

    if not isinstance(store, dict):
        store = defaultdict(deque)
        st.session_state[RATE_LIMIT_STATE_KEY] = store

    return store


def _get_block_store() -> Dict[str, datetime]:
    """Get or initialize the blocked-key store."""

    store = st.session_state.get(BLOCK_STATE_KEY)

    if not isinstance(store, dict):
        store = {}
        st.session_state[BLOCK_STATE_KEY] = store

    return store


def _make_key(
    identifier: Any,
    action: str,
) -> str:
    """
    Create a hashed rate-limit key.

    The original identifier is not stored in the key.
    """

    raw_value = f"{action}:{identifier}"
    return hashlib.sha256(
        raw_value.encode("utf-8")
    ).hexdigest()


def _cleanup_events(
    events: Deque[datetime],
    window_seconds: int,
    now: datetime,
) -> None:
    """Remove events outside the active time window."""

    cutoff = now - timedelta(seconds=window_seconds)

    while events and events[0] <= cutoff:
        events.popleft()


def _cleanup_blocks(now: datetime) -> None:
    """Remove expired temporary blocks."""

    blocks = _get_block_store()

    expired_keys = [
        key
        for key, blocked_until in blocks.items()
        if now >= blocked_until
    ]

    for key in expired_keys:
        blocks.pop(key, None)


def check_rate_limit(
    identifier: Any,
    action: str = "general",
    limit: int = DEFAULT_LIMIT,
    window_seconds: int = DEFAULT_WINDOW_SECONDS,
    block_seconds: int = DEFAULT_BLOCK_SECONDS,
) -> Dict[str, Any]:
    """
    Check whether an identifier can perform an action.

    This function does not record a new request.
    Use record_request() after a permitted request.
    """

    if identifier is None or str(identifier).strip() == "":
        return {
            "allowed": False,
            "message": "A valid identifier is required.",
            "remaining": 0,
        }

    try:
        limit = max(1, int(limit))
        window_seconds = max(1, int(window_seconds))
        block_seconds = max(1, int(block_seconds))
    except (TypeError, ValueError):
        return {
            "allowed": False,
            "message": "Invalid rate-limit configuration.",
            "remaining": 0,
        }

    now = _utc_now()
    key = _make_key(identifier, action)

    _cleanup_blocks(now)

    blocks = _get_block_store()

    if key in blocks:
        blocked_until = blocks[key]
        seconds_left = max(
            0,
            int((blocked_until - now).total_seconds()),
        )

        return {
            "allowed": False,
            "message": "Too many requests. Please try again later.",
            "remaining": 0,
            "retry_after_seconds": seconds_left,
        }

    store = _get_event_store()
    events = store.setdefault(key, deque())

    _cleanup_events(events, window_seconds, now)

    request_count = len(events)
    remaining = max(0, limit - request_count)

    if request_count >= limit:
        return {
            "allowed": False,
            "message": "Rate limit exceeded. Please try again later.",
            "remaining": 0,
            "retry_after_seconds": max(
                1,
                int(
                    (
                        events[0]
                        + timedelta(seconds=window_seconds)
                        - now
                    ).total_seconds()
                ),
            ),
        }

    return {
        "allowed": True,
        "message": "Request allowed.",
        "remaining": remaining,
        "limit": limit,
        "window_seconds": window_seconds,
    }


def record_request(
    identifier: Any,
    action: str = "general",
    limit: int = DEFAULT_LIMIT,
    window_seconds: int = DEFAULT_WINDOW_SECONDS,
    block_seconds: int = DEFAULT_BLOCK_SECONDS,
    block_on_limit: bool = False,
) -> Dict[str, Any]:
    """
    Record a permitted request.

    If the configured limit is reached, the request is rejected.
    Optionally apply a temporary block.
    """

    check = check_rate_limit(
        identifier=identifier,
        action=action,
        limit=limit,
        window_seconds=window_seconds,
        block_seconds=block_seconds,
    )

    if not check["allowed"]:
        return check

    key = _make_key(identifier, action)
    now = _utc_now()

    store = _get_event_store()
    events = store.setdefault(key, deque())

    events.append(now)

    try:
        limit = max(1, int(limit))
        window_seconds = max(1, int(window_seconds))
    except (TypeError, ValueError):
        limit = DEFAULT_LIMIT
        window_seconds = DEFAULT_WINDOW_SECONDS

    _cleanup_events(events, window_seconds, now)

    remaining = max(0, limit - len(events))

    if len(events) >= limit and block_on_limit:
        try:
            block_seconds = max(1, int(block_seconds))
        except (TypeError, ValueError):
            block_seconds = DEFAULT_BLOCK_SECONDS

        _get_block_store()[key] = (
            now + timedelta(seconds=block_seconds)
        )

    _trim_stores()

    return {
        "allowed": True,
        "message": "Request recorded.",
        "remaining": remaining,
        "request_count": len(events),
        "limit": limit,
    }


def enforce_rate_limit(
    identifier: Any,
    action: str = "general",
    limit: int = DEFAULT_LIMIT,
    window_seconds: int = DEFAULT_WINDOW_SECONDS,
    block_seconds: int = DEFAULT_BLOCK_SECONDS,
    block_on_limit: bool = False,
) -> Dict[str, Any]:
    """
    Check and record a request in one operation.

    Use this when every call should count toward the limit.
    """

    return record_request(
        identifier=identifier,
        action=action,
        limit=limit,
        window_seconds=window_seconds,
        block_seconds=block_seconds,
        block_on_limit=block_on_limit,
    )


def reset_rate_limit(
    identifier: Any,
    action: str = "general",
) -> Dict[str, Any]:
    """Reset rate-limit events and temporary blocks for a key."""

    key = _make_key(identifier, action)

    _get_event_store().pop(key, None)
    _get_block_store().pop(key, None)

    return {
        "success": True,
        "message": "Rate limit reset successfully.",
    }


def block_identifier(
    identifier: Any,
    action: str = "general",
    duration_seconds: int = DEFAULT_BLOCK_SECONDS,
) -> Dict[str, Any]:
    """Temporarily block an identifier for a particular action."""

    try:
        duration_seconds = max(1, int(duration_seconds))
    except (TypeError, ValueError):
        duration_seconds = DEFAULT_BLOCK_SECONDS

    key = _make_key(identifier, action)

    blocked_until = (
        _utc_now() + timedelta(seconds=duration_seconds)
    )

    _get_block_store()[key] = blocked_until

    return {
        "success": True,
        "message": "Identifier temporarily blocked.",
        "duration_seconds": duration_seconds,
        "blocked_until": blocked_until.isoformat(),
    }


def unblock_identifier(
    identifier: Any,
    action: str = "general",
) -> Dict[str, Any]:
    """Remove a temporary block."""

    key = _make_key(identifier, action)
    removed = _get_block_store().pop(key, None) is not None

    return {
        "success": True,
        "message": (
            "Block removed."
            if removed
            else "No active block was found."
        ),
    }


def get_rate_limit_status(
    identifier: Any,
    action: str = "general",
    limit: int = DEFAULT_LIMIT,
    window_seconds: int = DEFAULT_WINDOW_SECONDS,
) -> Dict[str, Any]:
    """Return the current rate-limit status without recording a request."""

    return check_rate_limit(
        identifier=identifier,
        action=action,
        limit=limit,
        window_seconds=window_seconds,
    )


def get_rate_limit_statistics() -> Dict[str, int]:
    """Return basic statistics about the current in-memory stores."""

    now = _utc_now()

    _cleanup_blocks(now)

    event_store = _get_event_store()
    block_store = _get_block_store()

    active_keys = sum(
        1 for events in event_store.values() if events
    )

    total_events = sum(
        len(events) for events in event_store.values()
    )

    return {
        "tracked_keys": len(event_store),
        "active_keys": active_keys,
        "total_events": total_events,
        "blocked_keys": len(block_store),
    }


def _trim_stores() -> None:
    """Prevent development stores from growing indefinitely."""

    event_store = _get_event_store()
    block_store = _get_block_store()

    if len(event_store) > MAX_TRACKED_KEYS:
        keys = list(event_store.keys())

        for key in keys[: len(event_store) - MAX_TRACKED_KEYS]:
            event_store.pop(key, None)

    if len(block_store) > MAX_TRACKED_KEYS:
        keys = list(block_store.keys())

        for key in keys[: len(block_store) - MAX_TRACKED_KEYS]:
            block_store.pop(key, None)


def clear_rate_limit_data() -> None:
    """
    Clear all rate-limit information.

    Development and testing only.
    Never expose this function to ordinary users.
    """

    st.session_state[RATE_LIMIT_STATE_KEY] = defaultdict(deque)
    st.session_state[BLOCK_STATE_KEY] = {}
