"""
JAK Data Analytics — Security Settings Service

Manages application security preferences, including:
- Password policy settings
- Session timeout settings
- Two-factor authentication requirements
- Login attempt limits
- Account lockout duration
- Security notification preferences

Development note:
Settings are stored in Streamlit session state.
For production, store global settings in the database and enforce
security policies in the authentication and session services.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Optional

import streamlit as st


SETTINGS_KEY = "jak_security_settings"
SETTINGS_HISTORY_KEY = "jak_security_settings_history"


DEFAULT_SECURITY_SETTINGS = {
    "password": {
        "minimum_length": 10,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_number": True,
        "require_special_character": True,
        "password_expiry_days": 0,
        "prevent_password_reuse": 5,
    },
    "authentication": {
        "require_email_verification": True,
        "allow_two_factor_authentication": True,
        "require_two_factor_for_admins": True,
        "require_two_factor_for_all_users": False,
        "allow_backup_codes": True,
    },
    "sessions": {
        "session_timeout_minutes": 60,
        "maximum_active_sessions": 3,
        "idle_timeout_enabled": True,
        "remember_me_enabled": True,
        "remember_me_days": 30,
    },
    "login_protection": {
        "maximum_login_attempts": 5,
        "account_lockout_minutes": 15,
        "progressive_lockout": True,
        "notify_on_new_login": True,
        "notify_on_failed_login": True,
    },
    "access": {
        "allow_user_registration": True,
        "require_admin_approval": False,
        "allow_multiple_devices": True,
    },
    "updated_at": None,
    "updated_by": None,
}


class SecuritySettingsError(Exception):
    """Raised when security settings are invalid."""


def _get_store() -> dict:
    """Return the current security settings store."""
    if SETTINGS_KEY not in st.session_state:
        st.session_state[SETTINGS_KEY] = deepcopy(
            DEFAULT_SECURITY_SETTINGS
        )

    return st.session_state[SETTINGS_KEY]


def _get_history() -> list:
    """Return the settings change history."""
    if SETTINGS_HISTORY_KEY not in st.session_state:
        st.session_state[SETTINGS_HISTORY_KEY] = []

    return st.session_state[SETTINGS_HISTORY_KEY]


def get_security_settings() -> dict:
    """Return a safe copy of all security settings."""
    return deepcopy(_get_store())


def get_security_setting(
    category: str,
    setting: str,
    default: Any = None,
) -> Any:
    """Retrieve one security setting."""
    settings = _get_store()

    category_settings = settings.get(category)

    if not isinstance(category_settings, dict):
        return default

    return deepcopy(category_settings.get(setting, default))


def _validate_integer(
    value: Any,
    name: str,
    minimum: int,
    maximum: int,
) -> int:
    """Validate an integer setting."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise SecuritySettingsError(
            f"{name} must be a whole number."
        )

    if not minimum <= value <= maximum:
        raise SecuritySettingsError(
            f"{name} must be between {minimum} and {maximum}."
        )

    return value


def _validate_boolean(value: Any, name: str) -> bool:
    """Validate a boolean setting."""
    if not isinstance(value, bool):
        raise SecuritySettingsError(
            f"{name} must be True or False."
        )

    return value


def validate_security_settings(settings: dict) -> dict:
    """
    Validate a complete settings object.

    Returns a normalized copy or raises SecuritySettingsError.
    """
    if not isinstance(settings, dict):
        raise SecuritySettingsError(
            "Security settings must be a dictionary."
        )

    validated = deepcopy(DEFAULT_SECURITY_SETTINGS)

    integer_rules = {
        "password": {
            "minimum_length": (8, 128),
            "password_expiry_days": (0, 365),
            "prevent_password_reuse": (0, 50),
        },
        "sessions": {
            "session_timeout_minutes": (5, 1440),
            "maximum_active_sessions": (1, 100),
            "remember_me_days": (1, 365),
        },
        "login_protection": {
            "maximum_login_attempts": (3, 20),
            "account_lockout_minutes": (1, 1440),
        },
    }

    boolean_rules = {
        "password": [
            "require_uppercase",
            "require_lowercase",
            "require_number",
            "require_special_character",
        ],
        "authentication": [
            "require_email_verification",
            "allow_two_factor_authentication",
            "require_two_factor_for_admins",
            "require_two_factor_for_all_users",
            "allow_backup_codes",
        ],
        "sessions": [
            "idle_timeout_enabled",
            "remember_me_enabled",
        ],
        "login_protection": [
            "progressive_lockout",
            "notify_on_new_login",
            "notify_on_failed_login",
        ],
        "access": [
            "allow_user_registration",
            "require_admin_approval",
            "allow_multiple_devices",
        ],
    }

    for category, rules in integer_rules.items():
        supplied = settings.get(category, {})

        if not isinstance(supplied, dict):
            raise SecuritySettingsError(
                f"Invalid settings category: {category}."
            )

        for key, limits in rules.items():
            if key in supplied:
                validated[category][key] = _validate_integer(
                    supplied[key],
                    key.replace("_", " ").title(),
                    limits[0],
                    limits[1],
                )

    for category, keys in boolean_rules.items():
        supplied = settings.get(category, {})

        if not isinstance(supplied, dict):
            raise SecuritySettingsError(
                f"Invalid settings category: {category}."
            )

        for key in keys:
            if key in supplied:
                validated[category][key] = _validate_boolean(
                    supplied[key],
                    key.replace("_", " ").title(),
                )

    if (
        validated["authentication"]["require_two_factor_for_all_users"]
        and not validated["authentication"]["allow_two_factor_authentication"]
    ):
        raise SecuritySettingsError(
            "Two-factor authentication cannot be required "
            "when it is disabled."
        )

    if (
        validated["authentication"]["require_two_factor_for_admins"]
        and not validated["authentication"]["allow_two_factor_authentication"]
    ):
        raise SecuritySettingsError(
            "Administrator two-factor authentication cannot be required "
            "when two-factor authentication is disabled."
        )

    if (
        validated["sessions"]["remember_me_enabled"] is False
        and "remember_me_days" in settings.get("sessions", {})
    ):
        # Retain the configured value, but it will not be used
        # while Remember Me is disabled.
        pass

    return validated


def update_security_settings(
    updates: dict,
    updated_by: Optional[str] = None,
) -> dict:
    """
    Update security settings.

    Only supplied categories and setting names are changed.
    Unknown settings are ignored.
    """
    if not isinstance(updates, dict):
        raise SecuritySettingsError(
            "Updates must be supplied as a dictionary."
        )

    current = get_security_settings()

    merged = deepcopy(current)

    for category, values in updates.items():
        if category not in DEFAULT_SECURITY_SETTINGS:
            continue

        if category in ("updated_at", "updated_by"):
            continue

        if not isinstance(values, dict):
            raise SecuritySettingsError(
                f"Settings for {category} must be a dictionary."
            )

        for key, value in values.items():
            if key in DEFAULT_SECURITY_SETTINGS[category]:
                merged[category][key] = value

    validated = validate_security_settings(merged)

    validated["updated_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    validated["updated_by"] = (
        str(updated_by).strip()[:150]
        if updated_by
        else "system"
    )

    st.session_state[SETTINGS_KEY] = validated

    history = _get_history()

    history.append({
        "updated_at": validated["updated_at"],
        "updated_by": validated["updated_by"],
        "changed_categories": list(updates.keys()),
    })

    # Keep the latest 100 history entries.
    st.session_state[SETTINGS_HISTORY_KEY] = history[-100:]

    return get_security_settings()


def reset_security_settings(
    updated_by: Optional[str] = None,
) -> dict:
    """Restore the default security settings."""
    defaults = deepcopy(DEFAULT_SECURITY_SETTINGS)

    return update_security_settings(
        defaults,
        updated_by=updated_by or "system",
    )


def get_password_policy() -> dict:
    """Return password policy settings."""
    return get_security_settings()["password"]


def get_session_policy() -> dict:
    """Return session policy settings."""
    return get_security_settings()["sessions"]


def get_login_protection_policy() -> dict:
    """Return login protection settings."""
    return get_security_settings()["login_protection"]


def get_authentication_policy() -> dict:
    """Return authentication policy settings."""
    return get_security_settings()["authentication"]


def get_access_policy() -> dict:
    """Return account access settings."""
    return get_security_settings()["access"]


def is_two_factor_required(role: str = "user") -> bool:
    """
    Determine whether two-factor authentication is required
    according to the configured policy.
    """
    policy = get_authentication_policy()

    if not policy["allow_two_factor_authentication"]:
        return False

    if policy["require_two_factor_for_all_users"]:
        return True

    if (
        str(role).strip().lower() == "admin"
        and policy["require_two_factor_for_admins"]
    ):
        return True

    return False


def is_registration_allowed() -> bool:
    """Check whether new user registration is enabled."""
    policy = get_access_policy()

    return policy["allow_user_registration"]


def requires_admin_approval() -> bool:
    """Check whether new accounts require administrator approval."""
    policy = get_access_policy()

    return policy["require_admin_approval"]


def get_settings_history(limit: int = 20) -> list:
    """Return recent security settings changes."""
    if (
        isinstance(limit, bool)
        or not isinstance(limit, int)
        or limit < 1
    ):
        raise SecuritySettingsError(
            "History limit must be a positive whole number."
        )

    history = _get_history()

    return deepcopy(history[-limit:][::-1])


def get_security_settings_summary() -> dict:
    """Return a simple summary suitable for an admin dashboard."""
    settings = get_security_settings()

    return {
        "minimum_password_length":
            settings["password"]["minimum_length"],

        "two_factor_enabled":
            settings["authentication"][
                "allow_two_factor_authentication"
            ],

        "two_factor_required_for_admins":
            settings["authentication"][
                "require_two_factor_for_admins"
            ],

        "session_timeout_minutes":
            settings["sessions"]["session_timeout_minutes"],

        "maximum_login_attempts":
            settings["login_protection"][
                "maximum_login_attempts"
            ],

        "account_lockout_minutes":
            settings["login_protection"][
                "account_lockout_minutes"
            ],

        "registration_enabled":
            settings["access"]["allow_user_registration"],

        "last_updated":
            settings["updated_at"],

        "updated_by":
            settings["updated_by"],
    }


def export_security_settings() -> dict:
    """
    Export settings without exposing secrets.

    This service does not store passwords, TOTP secrets,
    API keys, or backup codes.
    """
    return {
        "application": "JAK Data Analytics",
        "exported_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "settings": get_security_settings(),
    }
