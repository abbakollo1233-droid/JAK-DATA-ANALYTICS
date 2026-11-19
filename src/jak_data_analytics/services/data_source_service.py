"""
JAK Data Analytics
Data Source Management Service

Manages external data source configurations.

Features:
- Register data sources
- Update connection details
- API and SQL source types
- Activate and deactivate connections
- Search and filter sources
- Connection status tracking
- Connection test history
- Source statistics
- Safe metadata export

Security:
- Never stores database passwords.
- Never stores API keys or access tokens.
- Credentials must be retrieved from a secure
  secrets manager when a connection is used.
"""

from datetime import datetime, timezone
from uuid import uuid4


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

SUPPORTED_SOURCE_TYPES = {
    "api",
    "sqlite",
    "postgresql",
    "mysql",
}

SUPPORTED_SOURCE_STATUSES = {
    "active",
    "inactive",
    "error",
    "testing",
}

SUPPORTED_AUTH_TYPES = {
    "none",
    "api_key",
    "bearer",
    "database",
}

SENSITIVE_FIELDS = {
    "password",
    "api_key",
    "token",
    "access_token",
    "secret",
    "client_secret",
    "authorization",
}


# ---------------------------------------------------------
# UTILITIES
# ---------------------------------------------------------

def current_timestamp():
    """Return the current UTC timestamp."""

    return datetime.now(
        timezone.utc
    ).isoformat()


def generate_source_id():
    """Generate a unique data source ID."""

    return str(uuid4())


def normalize_text(value):
    """Normalize text values."""

    if value is None:
        return ""

    return " ".join(
        str(value).strip().split()
    )


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_source_configuration(
    name,
    source_type,
    configuration,
):
    """Validate a data source configuration."""

    if not normalize_text(name):
        raise ValueError(
            "Data source name is required."
        )

    source_type = str(
        source_type
    ).strip().lower()

    if source_type not in SUPPORTED_SOURCE_TYPES:
        raise ValueError(
            f"Unsupported source type: {source_type}"
        )

    if not isinstance(configuration, dict):
        raise ValueError(
            "Configuration must be a dictionary."
        )

    if source_type == "api":

        if not configuration.get("url"):
            raise ValueError(
                "API URL is required."
            )

        if not str(
            configuration["url"]
        ).startswith("https://"):
            raise ValueError(
                "External API sources must use HTTPS."
            )

    elif source_type == "sqlite":

        if not configuration.get("database_path"):
            raise ValueError(
                "SQLite database path is required."
            )

    elif source_type in {
        "postgresql",
        "mysql",
    }:

        required = [
            "host",
            "database",
            "username",
        ]

        missing = [
            field
            for field in required
            if not configuration.get(field)
        ]

        if missing:
            raise ValueError(
                f"Missing database settings: {missing}"
            )

    return True


# ---------------------------------------------------------
# REMOVE SENSITIVE VALUES
# ---------------------------------------------------------

def sanitize_configuration(configuration):
    """
    Remove credentials and sensitive values.

    Credentials must be managed separately through
    a secure secrets manager.
    """

    if not isinstance(configuration, dict):
        raise ValueError(
            "Configuration must be a dictionary."
        )

    sanitized = {}

    for key, value in configuration.items():

        normalized_key = str(key).lower()

        if any(
            sensitive in normalized_key
            for sensitive in SENSITIVE_FIELDS
        ):
            continue

        if isinstance(value, dict):

            sanitized[key] = sanitize_configuration(
                value
            )

        elif isinstance(value, list):

            sanitized[key] = [
                sanitize_configuration(item)
                if isinstance(item, dict)
                else item
                for item in value
            ]

        else:
            sanitized[key] = value

    return sanitized


# ---------------------------------------------------------
# REGISTER DATA SOURCE
# ---------------------------------------------------------

def register_data_source(
    name,
    source_type,
    configuration,
    owner_id,
    description="",
    authentication_type="none",
    tags=None,
):
    """Register a new data source."""

    source_type = str(
        source_type
    ).strip().lower()

    authentication_type = str(
        authentication_type
    ).strip().lower()

    validate_source_configuration(
        name,
        source_type,
        configuration,
    )

    if owner_id is None:
        raise ValueError(
            "Data source owner is required."
        )

    if authentication_type not in SUPPORTED_AUTH_TYPES:
        raise ValueError(
            "Unsupported authentication type."
        )

    if tags is None:
        tags = []

    if not isinstance(tags, list):
        raise ValueError(
            "Tags must be a list."
        )

    safe_tags = list(dict.fromkeys(
        normalize_text(tag).lower()
        for tag in tags
        if normalize_text(tag)
    ))

    record = {
        "source_id": generate_source_id(),
        "name": normalize_text(name),
        "source_type": source_type,
        "description": normalize_text(description),
        "owner_id": str(owner_id),
        "configuration": sanitize_configuration(
            configuration
        ),
        "authentication_type": authentication_type,
        "tags": safe_tags,
        "status": "inactive",
        "is_active": False,
        "last_tested_at": None,
        "last_successful_connection": None,
        "last_error": None,
        "connection_test_count": 0,
        "created_at": current_timestamp(),
        "updated_at": current_timestamp(),
    }

    return record


# ---------------------------------------------------------
# UPDATE DATA SOURCE
# ---------------------------------------------------------

def update_data_source(
    record,
    updates,
):
    """Update an existing data source."""

    if not isinstance(record, dict):
        raise ValueError(
            "Invalid data source record."
        )

    if not isinstance(updates, dict):
        raise ValueError(
            "Updates must be a dictionary."
        )

    allowed_fields = {
        "name",
        "description",
        "configuration",
        "authentication_type",
        "tags",
    }

    invalid = set(updates) - allowed_fields

    if invalid:
        raise ValueError(
            f"Fields cannot be updated: {sorted(invalid)}"
        )

    updated = dict(record)

    for field, value in updates.items():

        if field in {
            "name",
            "description",
        }:

            value = normalize_text(value)

            if field == "name" and not value:
                raise ValueError(
                    "Data source name cannot be empty."
                )

        elif field == "configuration":

            validate_source_configuration(
                updated["name"],
                updated["source_type"],
                value,
            )

            value = sanitize_configuration(
                value
            )

        elif field == "authentication_type":

            if value not in SUPPORTED_AUTH_TYPES:
                raise ValueError(
                    "Unsupported authentication type."
                )

        elif field == "tags":

            if not isinstance(value, list):
                raise ValueError(
                    "Tags must be a list."
                )

            value = list(dict.fromkeys(
                normalize_text(tag).lower()
                for tag in value
                if normalize_text(tag)
            ))

        updated[field] = value

    updated["updated_at"] = current_timestamp()

    return updated


# ---------------------------------------------------------
# ACTIVATE SOURCE
# ---------------------------------------------------------

def activate_data_source(record):
    """Activate a configured data source."""

    if not isinstance(record, dict):
        raise ValueError(
            "Invalid data source record."
        )

    updated = dict(record)

    updated["is_active"] = True
    updated["status"] = "active"
    updated["last_error"] = None
    updated["updated_at"] = current_timestamp()

    return updated


# ---------------------------------------------------------
# DEACTIVATE SOURCE
# ---------------------------------------------------------

def deactivate_data_source(record):
    """Deactivate a data source."""

    if not isinstance(record, dict):
        raise ValueError(
            "Invalid data source record."
        )

    updated = dict(record)

    updated["is_active"] = False
    updated["status"] = "inactive"
    updated["updated_at"] = current_timestamp()

    return updated


# ---------------------------------------------------------
# RECORD CONNECTION TEST
# ---------------------------------------------------------

def record_connection_test(
    record,
    success,
    error_message=None,
):
    """
    Record a connection test result.

    The caller must perform the actual API or SQL
    connection test before calling this function.
    """

    if not isinstance(record, dict):
        raise ValueError(
            "Invalid data source record."
        )

    updated = dict(record)

    updated["connection_test_count"] = (
        int(
            record.get(
                "connection_test_count",
                0,
            )
        ) + 1
    )

    updated["last_tested_at"] = current_timestamp()

    if success:

        updated["status"] = "active"
        updated["is_active"] = True
        updated["last_successful_connection"] = (
            current_timestamp()
        )
        updated["last_error"] = None

    else:

        updated["status"] = "error"
        updated["is_active"] = False
        updated["last_error"] = normalize_text(
            error_message or "Connection failed."
        )

    updated["updated_at"] = current_timestamp()

    return updated


# ---------------------------------------------------------
# FIND DATA SOURCE
# ---------------------------------------------------------

def get_data_source(
    sources,
    source_id,
    owner_id=None,
):
    """Find a data source by ID."""

    for record in sources:

        if str(record.get("source_id")) != str(source_id):
            continue

        if (
            owner_id is not None
            and str(record.get("owner_id")) != str(owner_id)
        ):
            continue

        return record

    return None


# ---------------------------------------------------------
# SEARCH DATA SOURCES
# ---------------------------------------------------------

def search_data_sources(
    sources,
    search_term="",
    owner_id=None,
    source_type=None,
    status=None,
    active_only=False,
):
    """Search and filter data sources."""

    query = normalize_text(
        search_term
    ).casefold()

    results = []

    for record in sources:

        if (
            owner_id is not None
            and str(record.get("owner_id")) != str(owner_id)
        ):
            continue

        if (
            source_type
            and record.get("source_type") != source_type
        ):
            continue

        if (
            status
            and record.get("status") != status
        ):
            continue

        if (
            active_only
            and not record.get("is_active")
        ):
            continue

        searchable = " ".join([
            str(record.get("name", "")),
            str(record.get("description", "")),
            str(record.get("source_type", "")),
            " ".join(record.get("tags", [])),
        ]).casefold()

        if query and query not in searchable:
            continue

        results.append(record)

    return results


# ---------------------------------------------------------
# DELETE DATA SOURCE
# ---------------------------------------------------------

def delete_data_source(
    sources,
    source_id,
    owner_id,
):
    """
    Remove a data source from a supplied collection.

    This does not delete the external database,
    remote API or any dataset already imported.
    """

    remaining = []

    deleted = None

    for record in sources:

        matches = (
            str(record.get("source_id")) == str(source_id)
            and str(record.get("owner_id")) == str(owner_id)
        )

        if matches:
            deleted = record
        else:
            remaining.append(record)

    return {
        "deleted": deleted is not None,
        "record": deleted,
        "sources": remaining,
    }


# ---------------------------------------------------------
# SOURCE STATISTICS
# ---------------------------------------------------------

def get_data_source_statistics(sources):
    """Calculate data source statistics."""

    statistics = {
        "total_sources": len(sources),
        "active_sources": 0,
        "inactive_sources": 0,
        "error_sources": 0,
        "testing_sources": 0,
        "by_type": {},
        "total_connection_tests": 0,
    }

    for record in sources:

        status = record.get(
            "status",
            "inactive",
        )

        source_type = record.get(
            "source_type",
            "unknown",
        )

        if status == "active":
            statistics["active_sources"] += 1

        elif status == "inactive":
            statistics["inactive_sources"] += 1

        elif status == "error":
            statistics["error_sources"] += 1

        elif status == "testing":
            statistics["testing_sources"] += 1

        statistics["by_type"][source_type] = (
            statistics["by_type"].get(source_type, 0) + 1
        )

        statistics["total_connection_tests"] += int(
            record.get(
                "connection_test_count",
                0,
            )
        )

    return statistics


# ---------------------------------------------------------
# SOURCE EXPORT
# ---------------------------------------------------------

def export_data_source_metadata(sources):
    """
    Export safe data source metadata.

    Credentials are removed before export.
    """

    exported = []

    for record in sources:

        safe_record = dict(record)

        safe_record["configuration"] = (
            sanitize_configuration(
                safe_record.get(
                    "configuration",
                    {},
                )
            )
        )

        exported.append(safe_record)

    return exported


# ---------------------------------------------------------
# SOURCE REPORT
# ---------------------------------------------------------

def generate_data_source_report(sources):
    """Generate a complete source management report."""

    return {
        "generated_at": current_timestamp(),
        "statistics": get_data_source_statistics(
            sources
        ),
        "sources": export_data_source_metadata(
            sources
        ),
    }
