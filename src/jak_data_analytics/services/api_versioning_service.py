"""
JAK Data Analytics — API Versioning Service

Manages API versions and their lifecycle.

Features:
- API version registration
- Version activation and deactivation
- Default version management
- Deprecation management
- Release dates
- End-of-life dates
- Breaking change documentation
- Version comparison
- Version statistics

Development implementation:
Records are stored in Streamlit session state.

Production recommendation:
Persist version records in the database and enforce
version availability in the actual API routing layer.
"""

from __future__ import annotations

import re

from copy import deepcopy
from datetime import datetime, timezone
from typing import Optional

import streamlit as st


API_VERSION_STORE = "jak_api_versions"
API_VERSION_DEFAULT = "jak_api_default_version"


class APIVersionError(Exception):
    """Raised when API version operations fail."""


DEFAULT_VERSION = {
    "version": "v1",
    "name": "Initial API",
    "description": "Initial JAK Data Analytics API version.",
    "status": "active",
    "is_default": True,
    "release_date": None,
    "deprecation_date": None,
    "end_of_life_date": None,
    "breaking_changes": [],
    "created_at": None,
    "updated_at": None,
}


VALID_STATUSES = {
    "active",
    "inactive",
    "deprecated",
    "retired",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_store() -> dict:
    """Return the API version store."""
    if API_VERSION_STORE not in st.session_state:
        st.session_state[API_VERSION_STORE] = {}

    store = st.session_state[API_VERSION_STORE]

    if "v1" not in store:
        initial = deepcopy(DEFAULT_VERSION)
        initial["created_at"] = _now()
        initial["updated_at"] = _now()
        store["v1"] = initial

    if API_VERSION_DEFAULT not in st.session_state:
        st.session_state[API_VERSION_DEFAULT] = "v1"

    return store


def _validate_version(version: str) -> str:
    """Validate an API version identifier."""
    if not isinstance(version, str):
        raise APIVersionError(
            "API version must be a string."
        )

    version = version.strip().lower()

    if not re.fullmatch(r"v[1-9][0-9]*", version):
        raise APIVersionError(
            "Version must follow the format v1, v2, v3, etc."
        )

    return version


def _validate_text(
    value: str,
    field_name: str,
    maximum_length: int = 500,
) -> str:
    """Validate required text."""
    if not isinstance(value, str):
        raise APIVersionError(
            f"{field_name} must be text."
        )

    value = value.strip()

    if not value:
        raise APIVersionError(
            f"{field_name} is required."
        )

    if len(value) > maximum_length:
        raise APIVersionError(
            f"{field_name} cannot exceed {maximum_length} characters."
        )

    return value


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    """Parse an optional ISO date or datetime."""
    if value is None:
        return None

    if not isinstance(value, str):
        raise APIVersionError(
            "Dates must be supplied as ISO-formatted strings."
        )

    try:
        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed.astimezone(timezone.utc)

    except ValueError as exc:
        raise APIVersionError(
            f"Invalid date format: {value}"
        ) from exc


def _validate_dates(
    release_date: Optional[str],
    deprecation_date: Optional[str],
    end_of_life_date: Optional[str],
) -> None:
    """Ensure lifecycle dates are logically consistent."""
    release = _parse_date(release_date)
    deprecation = _parse_date(deprecation_date)
    end_of_life = _parse_date(end_of_life_date)

    if release and deprecation:
        if deprecation < release:
            raise APIVersionError(
                "Deprecation date cannot precede release date."
            )

    if release and end_of_life:
        if end_of_life < release:
            raise APIVersionError(
                "End-of-life date cannot precede release date."
            )

    if deprecation and end_of_life:
        if end_of_life < deprecation:
            raise APIVersionError(
                "End-of-life date cannot precede deprecation date."
            )


def _public_record(record: dict) -> dict:
    """Return a safe copy of a version record."""
    return deepcopy(record)


def register_api_version(
    version: str,
    name: str,
    description: str,
    release_date: Optional[str] = None,
    set_as_default: bool = False,
    activate: bool = True,
) -> dict:
    """Register a new API version."""
    version = _validate_version(version)

    name = _validate_text(
        name,
        "Version name",
        100,
    )

    description = _validate_text(
        description,
        "Version description",
        2000,
    )

    if not isinstance(set_as_default, bool):
        raise APIVersionError(
            "set_as_default must be True or False."
        )

    if not isinstance(activate, bool):
        raise APIVersionError(
            "activate must be True or False."
        )

    _validate_dates(
        release_date,
        None,
        None,
    )

    store = _get_store()

    if version in store:
        raise APIVersionError(
            f"API version {version} already exists."
        )

    if not activate and set_as_default:
        raise APIVersionError(
            "An inactive version cannot be the default version."
        )

    now = _now()

    record = {
        "version": version,
        "name": name,
        "description": description,
        "status": "active" if activate else "inactive",
        "is_default": False,
        "release_date": release_date,
        "deprecation_date": None,
        "end_of_life_date": None,
        "breaking_changes": [],
        "created_at": now,
        "updated_at": now,
    }

    store[version] = record

    if set_as_default:
        set_default_api_version(version)

    return _public_record(record)


def get_api_version(version: str) -> Optional[dict]:
    """Retrieve an API version."""
    version = _validate_version(version)

    record = _get_store().get(version)

    if record is None:
        return None

    return _public_record(record)


def list_api_versions(
    status: Optional[str] = None,
) -> list[dict]:
    """List registered API versions."""
    store = _get_store()

    if status is not None:
        status = status.strip().lower()

        if status not in VALID_STATUSES:
            raise APIVersionError(
                "Invalid API version status."
            )

    versions = list(store.values())

    def version_number(record: dict) -> int:
        return int(record["version"][1:])

    if status:
        versions = [
            item for item in versions
            if item["status"] == status
        ]

    versions.sort(
        key=version_number,
        reverse=True,
    )

    return [
        _public_record(item)
        for item in versions
    ]


def get_default_api_version() -> str:
    """Return the current default API version."""
    store = _get_store()

    default_version = st.session_state.get(
        API_VERSION_DEFAULT
    )

    if default_version not in store:
        raise APIVersionError(
            "The configured default API version does not exist."
        )

    return default_version


def set_default_api_version(version: str) -> bool:
    """Set the default API version."""
    version = _validate_version(version)

    store = _get_store()

    if version not in store:
        raise APIVersionError(
            "The requested API version does not exist."
        )

    record = store[version]

    if record["status"] != "active":
        raise APIVersionError(
            "Only active API versions can be the default."
        )

    for item in store.values():
        item["is_default"] = False

    record["is_default"] = True
    record["updated_at"] = _now()

    st.session_state[API_VERSION_DEFAULT] = version

    return True


def activate_api_version(version: str) -> bool:
    """Activate an inactive API version."""
    version = _validate_version(version)

    store = _get_store()

    if version not in store:
        raise APIVersionError(
            "API version not found."
        )

    record = store[version]

    if record["status"] == "retired":
        raise APIVersionError(
            "A retired API version cannot be reactivated."
        )

    if record["status"] == "deprecated":
        raise APIVersionError(
            "A deprecated API version cannot be reactivated."
        )

    record["status"] = "active"
    record["updated_at"] = _now()

    return True


def deactivate_api_version(version: str) -> bool:
    """Deactivate an active API version."""
    version = _validate_version(version)

    store = _get_store()

    if version not in store:
        raise APIVersionError(
            "API version not found."
        )

    record = store[version]

    if record["is_default"]:
        raise APIVersionError(
            "Change the default version before deactivating this version."
        )

    if record["status"] == "retired":
        raise APIVersionError(
            "This API version has already been retired."
        )

    record["status"] = "inactive"
    record["updated_at"] = _now()

    return True


def deprecate_api_version(
    version: str,
    deprecation_date: Optional[str] = None,
    end_of_life_date: Optional[str] = None,
) -> bool:
    """Mark an API version as deprecated."""
    version = _validate_version(version)

    store = _get_store()

    if version not in store:
        raise APIVersionError(
            "API version not found."
        )

    record = store[version]

    if record["status"] == "retired":
        raise APIVersionError(
            "A retired API version cannot be deprecated."
        )

    if record["is_default"]:
        raise APIVersionError(
            "Change the default version before deprecating it."
        )

    if deprecation_date is None:
        deprecation_date = _now()

    _validate_dates(
        record["release_date"],
        deprecation_date,
        end_of_life_date,
    )

    record["status"] = "deprecated"
    record["deprecation_date"] = deprecation_date
    record["end_of_life_date"] = end_of_life_date
    record["updated_at"] = _now()

    return True


def retire_api_version(version: str) -> bool:
    """Permanently retire an API version."""
    version = _validate_version(version)

    store = _get_store()

    if version not in store:
        raise APIVersionError(
            "API version not found."
        )

    record = store[version]

    if record["is_default"]:
        raise APIVersionError(
            "Change the default version before retiring it."
        )

    record["status"] = "retired"
    record["is_default"] = False
    record["end_of_life_date"] = _now()
    record["updated_at"] = _now()

    return True


def add_breaking_change(
    version: str,
    title: str,
    description: str,
    migration_guide: Optional[str] = None,
) -> dict:
    """Document a breaking change in an API version."""
    version = _validate_version(version)

    title = _validate_text(
        title,
        "Breaking change title",
        200,
    )

    description = _validate_text(
        description,
        "Breaking change description",
        2000,
    )

    if migration_guide is not None:
        migration_guide = _validate_text(
            migration_guide,
            "Migration guide",
            2000,
        )

    store = _get_store()

    if version not in store:
        raise APIVersionError(
            "API version not found."
        )

    change = {
        "id": f"BC-{len(store[version]['breaking_changes']) + 1:04d}",
        "title": title,
        "description": description,
        "migration_guide": migration_guide,
        "created_at": _now(),
    }

    store[version]["breaking_changes"].append(change)
    store[version]["updated_at"] = _now()

    return deepcopy(change)


def get_breaking_changes(version: str) -> list[dict]:
    """Retrieve documented breaking changes."""
    version = _validate_version(version)

    store = _get_store()

    if version not in store:
        raise APIVersionError(
            "API version not found."
        )

    return deepcopy(
        store[version]["breaking_changes"]
    )


def compare_api_versions(
    first_version: str,
    second_version: str,
) -> dict:
    """Compare two registered API versions."""
    first_version = _validate_version(first_version)
    second_version = _validate_version(second_version)

    store = _get_store()

    if first_version not in store:
        raise APIVersionError(
            f"{first_version} does not exist."
        )

    if second_version not in store:
        raise APIVersionError(
            f"{second_version} does not exist."
        )

    first = store[first_version]
    second = store[second_version]

    first_changes = first["breaking_changes"]
    second_changes = second["breaking_changes"]

    return {
        "first_version": first_version,
        "second_version": second_version,
        "first_status": first["status"],
        "second_status": second["status"],
        "first_breaking_changes": len(first_changes),
        "second_breaking_changes": len(second_changes),
        "breaking_changes": {
            "first": deepcopy(first_changes),
            "second": deepcopy(second_changes),
        },
        "is_same_version": first_version == second_version,
    }


def get_api_version_statistics() -> dict:
    """Return API version management statistics."""
    versions = list_api_versions()

    status_counts = {
        status: sum(
            1 for item in versions
            if item["status"] == status
        )
        for status in VALID_STATUSES
    }

    return {
        "total_versions": len(versions),
        "active_versions": status_counts["active"],
        "inactive_versions": status_counts["inactive"],
        "deprecated_versions": status_counts["deprecated"],
        "retired_versions": status_counts["retired"],
        "default_version": get_default_api_version(),
        "total_breaking_changes": sum(
            len(item["breaking_changes"])
            for item in versions
        ),
    }


def export_api_versions() -> dict:
    """Export all API version information."""
    return {
        "application": "JAK Data Analytics",
        "exported_at": _now(),
        "default_version": get_default_api_version(),
        "versions": list_api_versions(),
    }
