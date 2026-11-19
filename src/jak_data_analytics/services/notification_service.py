"""
JAK Data Analytics
Notification Service

Manages application notifications for users.

Features:
- Create notifications
- Success, information, warning, and error notifications
- Mark notifications as read or unread
- Delete notifications
- Retrieve notification history
- Notification statistics
- Bulk notification operations

Current storage:
Streamlit session state.

Production note:
Connect this service to the database notification repository
before using it for persistent notifications.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import streamlit as st


NOTIFICATIONS_KEY = "jak_user_notifications"

VALID_TYPES = {
    "success",
    "info",
    "warning",
    "error",
    "system",
}

VALID_PRIORITIES = {
    "low",
    "normal",
    "high",
    "urgent",
}


# ---------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------

def _now() -> str:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _get_notifications() -> List[Dict[str, Any]]:
    """Get or initialize the notification collection."""
    if NOTIFICATIONS_KEY not in st.session_state:
        st.session_state[NOTIFICATIONS_KEY] = []

    return st.session_state[NOTIFICATIONS_KEY]


def _get_current_user_id() -> Optional[str]:
    """Get the current user's ID from supported session keys."""
    for key in ("jak_user", "user", "authenticated_user"):
        user = st.session_state.get(key)

        if isinstance(user, dict):
            user_id = user.get("id") or user.get("user_id")

            if user_id is not None:
                return str(user_id)

    return None


# ---------------------------------------------------------
# CREATE NOTIFICATIONS
# ---------------------------------------------------------

def create_notification(
    user_id: str,
    title: str,
    message: str,
    notification_type: str = "info",
    priority: str = "normal",
    action_url: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    expires_at: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a notification for a specific user.

    The notification is stored in the current Streamlit session.
    """
    if not user_id:
        raise ValueError("User ID is required.")

    if not title or not title.strip():
        raise ValueError("Notification title is required.")

    if not message or not message.strip():
        raise ValueError("Notification message is required.")

    notification_type = notification_type.lower().strip()
    priority = priority.lower().strip()

    if notification_type not in VALID_TYPES:
        raise ValueError("Invalid notification type.")

    if priority not in VALID_PRIORITIES:
        raise ValueError("Invalid notification priority.")

    notification = {
        "id": str(uuid4()),
        "user_id": str(user_id),
        "title": title.strip()[:200],
        "message": message.strip()[:2000],
        "type": notification_type,
        "priority": priority,
        "action_url": action_url,
        "metadata": metadata or {},
        "is_read": False,
        "created_at": _now(),
        "read_at": None,
        "expires_at": expires_at,
    }

    _get_notifications().append(notification)

    return notification


def notify_current_user(
    title: str,
    message: str,
    notification_type: str = "info",
    priority: str = "normal",
    action_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a notification for the currently authenticated user."""
    user_id = _get_current_user_id()

    if not user_id:
        raise ValueError("No authenticated user was found.")

    return create_notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        priority=priority,
        action_url=action_url,
    )


def create_system_notification(
    title: str,
    message: str,
    priority: str = "normal",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a system-wide notification record.

    This is a session-level record, not a broadcast to every user.
    A database-backed broadcast system will be added during integration.
    """
    if not title or not title.strip():
        raise ValueError("Notification title is required.")

    if not message or not message.strip():
        raise ValueError("Notification message is required.")

    priority = priority.lower().strip()

    if priority not in VALID_PRIORITIES:
        raise ValueError("Invalid notification priority.")

    notification = {
        "id": str(uuid4()),
        "user_id": None,
        "title": title.strip()[:200],
        "message": message.strip()[:2000],
        "type": "system",
        "priority": priority,
        "action_url": None,
        "metadata": metadata or {},
        "is_read": False,
        "created_at": _now(),
        "read_at": None,
        "expires_at": None,
    }

    _get_notifications().append(notification)

    return notification


# ---------------------------------------------------------
# RETRIEVE NOTIFICATIONS
# ---------------------------------------------------------

def get_user_notifications(
    user_id: Optional[str] = None,
    unread_only: bool = False,
    notification_type: Optional[str] = None,
    limit: Optional[int] = 50,
) -> List[Dict[str, Any]]:
    """Retrieve notifications belonging to a user."""
    if user_id is None:
        user_id = _get_current_user_id()

    if user_id is None:
        return []

    records = [
        item.copy()
        for item in _get_notifications()
        if item.get("user_id") == str(user_id)
    ]

    if unread_only:
        records = [
            item for item in records
            if not item.get("is_read", False)
        ]

    if notification_type:
        normalized_type = notification_type.lower().strip()

        if normalized_type not in VALID_TYPES:
            raise ValueError("Invalid notification type.")

        records = [
            item for item in records
            if item.get("type") == normalized_type
        ]

    records.sort(
        key=lambda item: item.get("created_at", ""),
        reverse=True,
    )

    if limit is not None:
        if limit < 1:
            raise ValueError("Limit must be greater than zero.")

        records = records[:limit]

    return records


def get_notification(
    notification_id: str,
    user_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieve one notification belonging to a user."""
    if user_id is None:
        user_id = _get_current_user_id()

    if user_id is None:
        return None

    for item in _get_notifications():
        if (
            item.get("id") == str(notification_id)
            and item.get("user_id") == str(user_id)
        ):
            return item.copy()

    return None


# ---------------------------------------------------------
# READ STATUS
# ---------------------------------------------------------

def mark_as_read(
    notification_id: str,
    user_id: Optional[str] = None,
) -> bool:
    """Mark a user's notification as read."""
    if user_id is None:
        user_id = _get_current_user_id()

    if user_id is None:
        return False

    for item in _get_notifications():
        if (
            item.get("id") == str(notification_id)
            and item.get("user_id") == str(user_id)
        ):
            item["is_read"] = True
            item["read_at"] = _now()
            return True

    return False


def mark_as_unread(
    notification_id: str,
    user_id: Optional[str] = None,
) -> bool:
    """Mark a user's notification as unread."""
    if user_id is None:
        user_id = _get_current_user_id()

    if user_id is None:
        return False

    for item in _get_notifications():
        if (
            item.get("id") == str(notification_id)
            and item.get("user_id") == str(user_id)
        ):
            item["is_read"] = False
            item["read_at"] = None
            return True

    return False


def mark_all_as_read(
    user_id: Optional[str] = None,
) -> int:
    """Mark all notifications belonging to a user as read."""
    if user_id is None:
        user_id = _get_current_user_id()

    if user_id is None:
        return 0

    updated = 0
    timestamp = _now()

    for item in _get_notifications():
        if (
            item.get("user_id") == str(user_id)
            and not item.get("is_read", False)
        ):
            item["is_read"] = True
            item["read_at"] = timestamp
            updated += 1

    return updated


# ---------------------------------------------------------
# DELETE NOTIFICATIONS
# ---------------------------------------------------------

def delete_notification(
    notification_id: str,
    user_id: Optional[str] = None,
) -> bool:
    """Delete a notification belonging to a user."""
    if user_id is None:
        user_id = _get_current_user_id()

    if user_id is None:
        return False

    notifications = _get_notifications()

    for index, item in enumerate(notifications):
        if (
            item.get("id") == str(notification_id)
            and item.get("user_id") == str(user_id)
        ):
            del notifications[index]
            return True

    return False


def delete_all_user_notifications(
    user_id: Optional[str] = None,
) -> int:
    """Delete all notifications belonging to a user."""
    if user_id is None:
        user_id = _get_current_user_id()

    if user_id is None:
        return 0

    notifications = _get_notifications()

    remaining = [
        item for item in notifications
        if item.get("user_id") != str(user_id)
    ]

    deleted = len(notifications) - len(remaining)

    st.session_state[NOTIFICATIONS_KEY] = remaining

    return deleted


def delete_read_notifications(
    user_id: Optional[str] = None,
) -> int:
    """Delete all read notifications belonging to a user."""
    if user_id is None:
        user_id = _get_current_user_id()

    if user_id is None:
        return 0

    notifications = _get_notifications()

    remaining = [
        item for item in notifications
        if not (
            item.get("user_id") == str(user_id)
            and item.get("is_read", False)
        )
    ]

    deleted = len(notifications) - len(remaining)

    st.session_state[NOTIFICATIONS_KEY] = remaining

    return deleted


# ---------------------------------------------------------
# NOTIFICATION STATISTICS
# ---------------------------------------------------------

def get_notification_statistics(
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Calculate notification statistics for a user."""
    records = get_user_notifications(
        user_id=user_id,
        limit=None,
    )

    total = len(records)

    unread = sum(
        1 for item in records
        if not item.get("is_read", False)
    )

    read = total - unread

    by_type = {
        item_type: sum(
            1 for item in records
            if item.get("type") == item_type
        )
        for item_type in VALID_TYPES
    }

    by_priority = {
        priority: sum(
            1 for item in records
            if item.get("priority") == priority
        )
        for priority in VALID_PRIORITIES
    }

    return {
        "total": total,
        "read": read,
        "unread": unread,
        "read_percentage": (
            round(read / total * 100, 2)
            if total
            else 0
        ),
        "unread_percentage": (
            round(unread / total * 100, 2)
            if total
            else 0
        ),
        "by_type": by_type,
        "by_priority": by_priority,
    }


def get_unread_count(
    user_id: Optional[str] = None,
) -> int:
    """Return the number of unread notifications."""
    return len(
        get_user_notifications(
            user_id=user_id,
            unread_only=True,
            limit=None,
        )
    )


# ---------------------------------------------------------
# EXPIRY MANAGEMENT
# ---------------------------------------------------------

def remove_expired_notifications() -> int:
    """
    Remove expired notifications.

    Expiry timestamps must be ISO 8601 strings with timezone
    information. Invalid expiry values are retained.
    """
    now = datetime.now(timezone.utc)
    notifications = _get_notifications()

    remaining = []

    for item in notifications:
        expires_at = item.get("expires_at")

        if not expires_at:
            remaining.append(item)
            continue

        try:
            expiry = datetime.fromisoformat(
                expires_at.replace("Z", "+00:00")
            )

            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)

            if expiry > now:
                remaining.append(item)

        except (ValueError, TypeError, AttributeError):
            remaining.append(item)

    deleted = len(notifications) - len(remaining)

    st.session_state[NOTIFICATIONS_KEY] = remaining

    return deleted


# ---------------------------------------------------------
# DISPLAY HELPERS
# ---------------------------------------------------------

def get_notification_icon(notification_type: str) -> str:
    """Return an icon for a notification type."""
    icons = {
        "success": "✅",
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌",
        "system": "🔔",
    }

    return icons.get(
        str(notification_type).lower(),
        "🔔",
    )


def get_notification_color(notification_type: str) -> str:
    """Return a display color for a notification type."""
    colors = {
        "success": "#16A34A",
        "info": "#2563EB",
        "warning": "#F59E0B",
        "error": "#DC2626",
        "system": "#64748B",
    }

    return colors.get(
        str(notification_type).lower(),
        "#64748B",
    )


def get_priority_color(priority: str) -> str:
    """Return a display color for a notification priority."""
    colors = {
        "low": "#64748B",
        "normal": "#2563EB",
        "high": "#F59E0B",
        "urgent": "#DC2626",
    }

    return colors.get(
        str(priority).lower(),
        "#64748B",
    )


# ---------------------------------------------------------
# EXPORT
# ---------------------------------------------------------

def export_user_notifications(
    user_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Export a user's notification records."""
    return get_user_notifications(
        user_id=user_id,
        limit=None,
    )
