"""
JAK Data Analytics
Notification Preferences Service

Manages individual user notification preferences.

Features:
- Enable or disable notification categories
- Configure email and in-app notifications
- Configure notification frequency
- Manage quiet hours
- Retrieve and update preferences
- Reset preferences to defaults

Current storage:
Streamlit session state.

Production note:
Persist preferences in the database through a repository.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, time
from typing import Any, Dict, Optional

import streamlit as st


PREFERENCES_KEY = "jak_notification_preferences"

VALID_FREQUENCIES = {
    "immediate",
    "daily",
    "weekly",
    "never",
}

DEFAULT_PREFERENCES = {
    "channels": {
        "in_app": True,
        "email": True,
    },
    "categories": {
        "security": True,
        "account": True,
        "projects": True,
        "datasets": True,
        "analysis": True,
        "reports": True,
        "system_updates": True,
        "marketing": False,
    },
    "frequency": {
        "in_app": "immediate",
        "email": "immediate",
    },
    "quiet_hours": {
        "enabled": False,
        "start": "22:00",
        "end": "07:00",
    },
    "updated_at": None,
}


# ---------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------

def _get_user_id(user_id: Optional[str] = None) -> str:
    """Resolve the user ID from an argument or current session."""
    if user_id is not None:
        return str(user_id)

    for key in ("jak_user", "user", "authenticated_user"):
        user = st.session_state.get(key)

        if isinstance(user, dict):
            identifier = user.get("id") or user.get("user_id")

            if identifier is not None:
                return str(identifier)

    raise ValueError("A valid user ID is required.")


def _all_preferences() -> Dict[str, Any]:
    """Get or initialize the preference collection."""
    if PREFERENCES_KEY not in st.session_state:
        st.session_state[PREFERENCES_KEY] = {}

    return st.session_state[PREFERENCES_KEY]


def _validate_time(value: str) -> str:
    """Validate a 24-hour HH:MM time string."""
    try:
        parsed = datetime.strptime(value, "%H:%M")
        return parsed.strftime("%H:%M")
    except (ValueError, TypeError):
        raise ValueError("Time must use HH:MM format.")


def _merge_preferences(
    defaults: Dict[str, Any],
    saved: Dict[str, Any],
) -> Dict[str, Any]:
    """Merge saved preferences with defaults safely."""
    result = deepcopy(defaults)

    for section, values in saved.items():
        if (
            section in result
            and isinstance(result[section], dict)
            and isinstance(values, dict)
        ):
            result[section].update(values)
        elif section in result:
            result[section] = values

    return result


# ---------------------------------------------------------
# CREATE AND RETRIEVE
# ---------------------------------------------------------

def get_default_preferences() -> Dict[str, Any]:
    """Return a fresh copy of default preferences."""
    return deepcopy(DEFAULT_PREFERENCES)


def get_notification_preferences(
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve a user's notification preferences."""
    identifier = _get_user_id(user_id)
    records = _all_preferences()

    saved = records.get(identifier, {})

    return _merge_preferences(
        DEFAULT_PREFERENCES,
        saved,
    )


def initialize_notification_preferences(
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create default preferences if none exist."""
    identifier = _get_user_id(user_id)
    records = _all_preferences()

    if identifier not in records:
        preferences = get_default_preferences()
        preferences["updated_at"] = datetime.utcnow().isoformat()
        records[identifier] = preferences

    return get_notification_preferences(identifier)


# ---------------------------------------------------------
# UPDATE PREFERENCES
# ---------------------------------------------------------

def update_notification_preferences(
    updates: Dict[str, Any],
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update notification preferences.

    Only recognized settings are accepted.
    """
    if not isinstance(updates, dict):
        raise ValueError("Updates must be a dictionary.")

    identifier = _get_user_id(user_id)
    records = _all_preferences()

    current = get_notification_preferences(identifier)

    allowed_sections = {
        "channels",
        "categories",
        "frequency",
        "quiet_hours",
    }

    unknown_sections = set(updates) - allowed_sections

    if unknown_sections:
        raise ValueError(
            "Unknown preference sections: "
            + ", ".join(sorted(unknown_sections))
        )

    for section, values in updates.items():
        if not isinstance(values, dict):
            raise ValueError(
                f"Preference section '{section}' must be a dictionary."
            )

        if section not in current:
            raise ValueError(f"Unknown section: {section}")

        unknown_keys = set(values) - set(current[section])

        if unknown_keys:
            raise ValueError(
                f"Unknown settings in '{section}': "
                + ", ".join(sorted(unknown_keys))
            )

        for key, value in values.items():

            if section in {"channels", "categories"}:
                if not isinstance(value, bool):
                    raise ValueError(
                        f"'{key}' must be True or False."
                    )

            elif section == "frequency":
                value = str(value).lower().strip()

                if value not in VALID_FREQUENCIES:
                    raise ValueError(
                        f"Invalid frequency for '{key}'."
                    )

            elif section == "quiet_hours":
                if key == "enabled":
                    if not isinstance(value, bool):
                        raise ValueError(
                            "Quiet hours enabled must be True or False."
                        )

                elif key in {"start", "end"}:
                    value = _validate_time(value)

            current[section][key] = value

    current["updated_at"] = datetime.utcnow().isoformat()

    records[identifier] = current

    return deepcopy(current)


# ---------------------------------------------------------
# CHANNEL SETTINGS
# ---------------------------------------------------------

def set_channel_enabled(
    channel: str,
    enabled: bool,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Enable or disable a notification delivery channel."""
    return update_notification_preferences(
        {"channels": {channel: enabled}},
        user_id,
    )


def is_channel_enabled(
    channel: str,
    user_id: Optional[str] = None,
) -> bool:
    """Check whether a delivery channel is enabled."""
    preferences = get_notification_preferences(user_id)

    if channel not in preferences["channels"]:
        raise ValueError("Unknown notification channel.")

    return preferences["channels"][channel]


# ---------------------------------------------------------
# CATEGORY SETTINGS
# ---------------------------------------------------------

def set_category_enabled(
    category: str,
    enabled: bool,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Enable or disable a notification category."""
    return update_notification_preferences(
        {"categories": {category: enabled}},
        user_id,
    )


def is_category_enabled(
    category: str,
    user_id: Optional[str] = None,
) -> bool:
    """Check whether a notification category is enabled."""
    preferences = get_notification_preferences(user_id)

    if category not in preferences["categories"]:
        raise ValueError("Unknown notification category.")

    return preferences["categories"][category]


# ---------------------------------------------------------
# FREQUENCY SETTINGS
# ---------------------------------------------------------

def set_notification_frequency(
    channel: str,
    frequency: str,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Set the delivery frequency for a notification channel."""
    return update_notification_preferences(
        {"frequency": {channel: frequency}},
        user_id,
    )


def get_notification_frequency(
    channel: str,
    user_id: Optional[str] = None,
) -> str:
    """Get the configured delivery frequency."""
    preferences = get_notification_preferences(user_id)

    if channel not in preferences["frequency"]:
        raise ValueError("Unknown notification channel.")

    return preferences["frequency"][channel]


# ---------------------------------------------------------
# QUIET HOURS
# ---------------------------------------------------------

def configure_quiet_hours(
    enabled: bool,
    start: str = "22:00",
    end: str = "07:00",
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Configure notification quiet hours."""
    return update_notification_preferences(
        {
            "quiet_hours": {
                "enabled": enabled,
                "start": start,
                "end": end,
            }
        },
        user_id,
    )


def is_quiet_hours_active(
    user_id: Optional[str] = None,
    current_time: Optional[time] = None,
) -> bool:
    """
    Check whether the current time falls within quiet hours.

    Handles quiet periods that cross midnight, such as 22:00–07:00.

    The caller must provide current_time in the user's local timezone
    if local-time behaviour is required.
    """
    preferences = get_notification_preferences(user_id)
    settings = preferences["quiet_hours"]

    if not settings["enabled"]:
        return False

    start = datetime.strptime(
        settings["start"],
        "%H:%M",
    ).time()

    end = datetime.strptime(
        settings["end"],
        "%H:%M",
    ).time()

    if current_time is None:
        current_time = datetime.now().time()

    if start == end:
        return True

    if start < end:
        return start <= current_time < end

    return current_time >= start or current_time < end


# ---------------------------------------------------------
# DELIVERY DECISION
# ---------------------------------------------------------

def should_send_notification(
    category: str,
    channel: str = "in_app",
    user_id: Optional[str] = None,
    current_time: Optional[time] = None,
) -> bool:
    """
    Decide whether a notification should be delivered.

    This checks preferences only. It does not send email or
    create an in-app notification itself.
    """
    preferences = get_notification_preferences(user_id)

    if channel not in preferences["channels"]:
        raise ValueError("Unknown notification channel.")

    if category not in preferences["categories"]:
        raise ValueError("Unknown notification category.")

    if not preferences["channels"][channel]:
        return False

    if not preferences["categories"][category]:
        return False

    frequency = preferences["frequency"][channel]

    if frequency == "never":
        return False

    if channel == "in_app":
        return True

    if is_quiet_hours_active(
        user_id=user_id,
        current_time=current_time,
    ):
        return False

    return True


# ---------------------------------------------------------
# RESET AND DELETE
# ---------------------------------------------------------

def reset_notification_preferences(
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Restore a user's preferences to the default configuration."""
    identifier = _get_user_id(user_id)

    preferences = get_default_preferences()
    preferences["updated_at"] = datetime.utcnow().isoformat()

    _all_preferences()[identifier] = preferences

    return deepcopy(preferences)


def delete_notification_preferences(
    user_id: Optional[str] = None,
) -> bool:
    """Remove saved preferences for a user."""
    identifier = _get_user_id(user_id)
    records = _all_preferences()

    if identifier not in records:
        return False

    del records[identifier]

    return True


# ---------------------------------------------------------
# EXPORT
# ---------------------------------------------------------

def export_notification_preferences(
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a copy of a user's preferences for export."""
    return get_notification_preferences(user_id)
