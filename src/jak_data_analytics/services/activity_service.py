"""
JAK Data Analytics
Activity Service

Manages application activity tracking.

Features:
- Record user activities
- Retrieve activity history
- Retrieve recent activities
- Search activity records
- Filter activities by action
- Count user activities
- Generate activity statistics
- Track important application events

All activity records are scoped to their owners.

This module does not depend on Streamlit.
"""

from datetime import datetime, timezone

from ..database.repositories import activity_repository


# ==================================================
# CONSTANTS
# ==================================================

SUPPORTED_ACTIVITY_ACTIONS = [
    "login",
    "logout",
    "registration",
    "profile_update",
    "password_change",
    "email_change",
    "project_created",
    "project_updated",
    "project_deleted",
    "dataset_uploaded",
    "dataset_updated",
    "dataset_deleted",
    "data_profiled",
    "data_cleaned",
    "data_transformed",
    "statistical_analysis",
    "visualization_created",
    "dashboard_created",
    "dashboard_updated",
    "dashboard_deleted",
    "machine_learning",
    "prediction_generated",
    "forecast_generated",
    "anomaly_detection",
    "recommendation_generated",
    "report_generated",
    "report_deleted",
    "settings_updated",
    "other",
]

MAX_DESCRIPTION_LENGTH = 2000
MAX_SEARCH_LENGTH = 200


# ==================================================
# VALIDATION
# ==================================================

def validate_user_id(user_id):
    """Validate activity owner ID."""

    if not isinstance(user_id, int) or isinstance(user_id, bool):
        raise ValueError(
            "A valid integer user ID is required."
        )

    if user_id <= 0:
        raise ValueError(
            "User ID must be greater than zero."
        )

    return True


def validate_activity_id(activity_id):
    """Validate activity record ID."""

    if not isinstance(activity_id, int) or isinstance(activity_id, bool):
        raise ValueError(
            "A valid integer activity ID is required."
        )

    if activity_id <= 0:
        raise ValueError(
            "Activity ID must be greater than zero."
        )

    return True


def validate_action(action):
    """Validate activity action."""

    if not isinstance(action, str):
        raise ValueError(
            "Activity action must be text."
        )

    action = action.strip().lower()

    if not action:
        raise ValueError(
            "Activity action cannot be empty."
        )

    if action not in SUPPORTED_ACTIVITY_ACTIONS:
        raise ValueError(
            f"Unsupported activity action: {action}"
        )

    return action


def validate_description(description):
    """Validate activity description."""

    if description is None:
        return ""

    if not isinstance(description, str):
        raise ValueError(
            "Activity description must be text."
        )

    description = description.strip()

    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise ValueError(
            f"Description cannot exceed "
            f"{MAX_DESCRIPTION_LENGTH} characters."
        )

    return description


def validate_metadata(metadata):
    """Validate activity metadata."""

    if metadata is None:
        return {}

    if not isinstance(metadata, dict):
        raise ValueError(
            "Activity metadata must be a dictionary."
        )

    return metadata


# ==================================================
# CREATE ACTIVITY
# ==================================================

def record_activity(
    session,
    user_id,
    action,
    description=None,
    metadata=None,
    ip_address=None,
):
    """
    Record a user activity.

    The database session controls transaction commits.
    """

    validate_user_id(user_id)

    action = validate_action(
        action
    )

    description = validate_description(
        description
    )

    metadata = validate_metadata(
        metadata
    )

    if ip_address is not None:
        if not isinstance(ip_address, str):
            raise ValueError(
                "IP address must be text."
            )

        ip_address = ip_address.strip() or None

        if ip_address and len(ip_address) > 45:
            raise ValueError(
                "IP address is too long."
            )

    return activity_repository.create_activity(
        session=session,
        user_id=user_id,
        action=action,
        description=description,
        metadata=metadata,
        ip_address=ip_address,
    )


# ==================================================
# GET ACTIVITY
# ==================================================

def get_activity(
    session,
    activity_id,
    user_id,
):
    """Retrieve one activity belonging to a user."""

    validate_activity_id(activity_id)
    validate_user_id(user_id)

    return activity_repository.get_activity_by_id(
        session=session,
        activity_id=activity_id,
        user_id=user_id,
    )


# ==================================================
# GET USER ACTIVITIES
# ==================================================

def get_user_activities(
    session,
    user_id,
    limit=100,
    offset=0,
):
    """Retrieve a user's activity history."""

    validate_user_id(user_id)

    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError(
            "Limit must be an integer."
        )

    if not isinstance(offset, int) or isinstance(offset, bool):
        raise ValueError(
            "Offset must be an integer."
        )

    if limit < 1 or limit > 1000:
        raise ValueError(
            "Limit must be between 1 and 1000."
        )

    if offset < 0:
        raise ValueError(
            "Offset cannot be negative."
        )

    return activity_repository.get_user_activities(
        session=session,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )


# ==================================================
# COUNT ACTIVITIES
# ==================================================

def count_user_activities(
    session,
    user_id,
):
    """Count activities belonging to a user."""

    validate_user_id(user_id)

    return activity_repository.count_user_activities(
        session=session,
        user_id=user_id,
    )


# ==================================================
# SEARCH ACTIVITIES
# ==================================================

def search_activities(
    session,
    user_id,
    search_term,
):
    """Search a user's activity history."""

    validate_user_id(user_id)

    if not isinstance(search_term, str):
        raise ValueError(
            "Search term must be text."
        )

    search_term = search_term.strip()

    if not search_term:
        return []

    if len(search_term) > MAX_SEARCH_LENGTH:
        raise ValueError(
            f"Search term cannot exceed "
            f"{MAX_SEARCH_LENGTH} characters."
        )

    return activity_repository.search_user_activities(
        session=session,
        user_id=user_id,
        search_term=search_term,
    )


# ==================================================
# FILTER BY ACTION
# ==================================================

def get_activities_by_action(
    session,
    user_id,
    action,
):
    """Retrieve activities belonging to a specific action."""

    validate_user_id(user_id)

    action = validate_action(
        action
    )

    return activity_repository.get_activities_by_action(
        session=session,
        user_id=user_id,
        action=action,
    )


# ==================================================
# RECENT ACTIVITIES
# ==================================================

def get_recent_activities(
    session,
    user_id,
    limit=10,
):
    """Retrieve the most recent user activities."""

    validate_user_id(user_id)

    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError(
            "Limit must be an integer."
        )

    if limit < 1 or limit > 100:
        raise ValueError(
            "Limit must be between 1 and 100."
        )

    return activity_repository.get_recent_activities(
        session=session,
        user_id=user_id,
        limit=limit,
    )


# ==================================================
# ACTIVITY STATISTICS
# ==================================================

def get_activity_statistics(
    session,
    user_id,
):
    """Retrieve activity statistics for a user."""

    validate_user_id(user_id)

    return activity_repository.get_activity_statistics(
        session=session,
        user_id=user_id,
    )


# ==================================================
# RECORD LOGIN
# ==================================================

def record_login(
    session,
    user_id,
    ip_address=None,
):
    """Record a successful login."""

    return record_activity(
        session=session,
        user_id=user_id,
        action="login",
        description="User successfully logged in.",
        metadata={
            "event": "authentication",
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        },
        ip_address=ip_address,
    )


# ==================================================
# RECORD LOGOUT
# ==================================================

def record_logout(
    session,
    user_id,
    ip_address=None,
):
    """Record a user logout."""

    return record_activity(
        session=session,
        user_id=user_id,
        action="logout",
        description="User logged out.",
        metadata={
            "event": "authentication",
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        },
        ip_address=ip_address,
    )


# ==================================================
# RECORD DATASET UPLOAD
# ==================================================

def record_dataset_upload(
    session,
    user_id,
    dataset_name,
    dataset_id=None,
):
    """Record a dataset upload."""

    return record_activity(
        session=session,
        user_id=user_id,
        action="dataset_uploaded",
        description=(
            f"Uploaded dataset: {dataset_name}"
        ),
        metadata={
            "dataset_id": dataset_id,
            "dataset_name": dataset_name,
        },
    )


# ==================================================
# RECORD DATA CLEANING
# ==================================================

def record_data_cleaning(
    session,
    user_id,
    dataset_name,
    details=None,
):
    """Record a data cleaning operation."""

    return record_activity(
        session=session,
        user_id=user_id,
        action="data_cleaned",
        description=(
            f"Performed data cleaning on {dataset_name}."
        ),
        metadata={
            "dataset_name": dataset_name,
            "details": details or {},
        },
    )


# ==================================================
# RECORD ANALYSIS
# ==================================================

def record_analysis(
    session,
    user_id,
    analysis_type,
    description=None,
    metadata=None,
):
    """Record an analytical operation."""

    if not isinstance(analysis_type, str):
        raise ValueError(
            "Analysis type must be text."
        )

    analysis_type = analysis_type.strip().lower()

    action_mapping = {
        "statistics": "statistical_analysis",
        "statistical_analysis": "statistical_analysis",
        "machine_learning": "machine_learning",
        "forecasting": "forecast_generated",
        "anomaly_detection": "anomaly_detection",
        "visualization": "visualization_created",
        "recommendations": "recommendation_generated",
        "profiling": "data_profiled",
    }

    action = action_mapping.get(
        analysis_type
    )

    if action is None:
        action = "other"

    return record_activity(
        session=session,
        user_id=user_id,
        action=action,
        description=description or (
            f"Performed {analysis_type.replace('_', ' ')}."
        ),
        metadata=metadata or {
            "analysis_type": analysis_type,
        },
    )


# ==================================================
# RECORD REPORT GENERATION
# ==================================================

def record_report_generation(
    session,
    user_id,
    report_title,
    report_id=None,
):
    """Record report generation."""

    return record_activity(
        session=session,
        user_id=user_id,
        action="report_generated",
        description=(
            f"Generated report: {report_title}"
        ),
        metadata={
            "report_id": report_id,
            "report_title": report_title,
        },
    )


# ==================================================
# RECORD DASHBOARD CREATION
# ==================================================

def record_dashboard_creation(
    session,
    user_id,
    dashboard_name,
    dashboard_id=None,
):
    """Record dashboard creation."""

    return record_activity(
        session=session,
        user_id=user_id,
        action="dashboard_created",
        description=(
            f"Created dashboard: {dashboard_name}"
        ),
        metadata={
            "dashboard_id": dashboard_id,
            "dashboard_name": dashboard_name,
        },
    )


# ==================================================
# RECORD PROFILE UPDATE
# ==================================================

def record_profile_update(
    session,
    user_id,
    changed_fields=None,
):
    """Record a profile update."""

    return record_activity(
        session=session,
        user_id=user_id,
        action="profile_update",
        description="Updated account profile.",
        metadata={
            "changed_fields": changed_fields or [],
        },
    )


# ==================================================
# RECORD SETTINGS UPDATE
# ==================================================

def record_settings_update(
    session,
    user_id,
    setting_names=None,
):
    """Record account settings changes."""

    return record_activity(
        session=session,
        user_id=user_id,
        action="settings_updated",
        description="Updated account settings.",
        metadata={
            "settings": setting_names or [],
        },
    )