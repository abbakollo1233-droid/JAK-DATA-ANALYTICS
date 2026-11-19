"""
JAK Data Analytics
Report Service

Handles report business logic and database operations.

Features:
- Register generated reports
- Retrieve reports
- List user reports
- Search reports
- Update report information
- Delete reports
- Report statistics
- File validation
- Report storage path generation
- Report download preparation

This module does not depend on Streamlit.

Database transactions are managed by the
database session context manager.
"""

import re
import uuid

from pathlib import Path
from datetime import datetime, timezone

from ..config.settings import REPORTS_DIR
from ..database.repositories import report_repository


# ==================================================
# CONSTANTS
# ==================================================

SUPPORTED_REPORT_FORMATS = [
    "pdf",
    "csv",
    "xlsx",
    "json",
    "html",
    "txt",
]

MAX_REPORT_TITLE_LENGTH = 200
MAX_REPORT_FILE_SIZE_MB = 500

REPORT_STATUSES = [
    "generated",
    "ready",
    "failed",
    "archived",
]


# ==================================================
# VALIDATION
# ==================================================

def validate_user_id(user_id):
    """Validate report owner ID."""

    if not isinstance(user_id, int) or isinstance(user_id, bool):
        raise ValueError(
            "A valid integer user ID is required."
        )

    if user_id <= 0:
        raise ValueError(
            "User ID must be greater than zero."
        )

    return True


def validate_report_id(report_id):
    """Validate report ID."""

    if not isinstance(report_id, int) or isinstance(report_id, bool):
        raise ValueError(
            "A valid integer report ID is required."
        )

    if report_id <= 0:
        raise ValueError(
            "Report ID must be greater than zero."
        )

    return True


def validate_report_title(title):
    """Validate report title."""

    if not isinstance(title, str):
        raise ValueError(
            "Report title must be text."
        )

    title = title.strip()

    if not title:
        raise ValueError(
            "Report title cannot be empty."
        )

    if len(title) > MAX_REPORT_TITLE_LENGTH:
        raise ValueError(
            f"Report title cannot exceed "
            f"{MAX_REPORT_TITLE_LENGTH} characters."
        )

    return title


def validate_report_format(file_type):
    """Validate report file format."""

    if not isinstance(file_type, str):
        raise ValueError(
            "Report format must be text."
        )

    file_type = file_type.lower().strip().lstrip(".")

    if file_type not in SUPPORTED_REPORT_FORMATS:
        raise ValueError(
            f"Unsupported report format: {file_type}"
        )

    return file_type


def validate_report_status(status):
    """Validate report status."""

    if status not in REPORT_STATUSES:
        raise ValueError(
            f"Unsupported report status: {status}"
        )

    return status


# ==================================================
# FILE VALIDATION
# ==================================================

def validate_report_file(file_path):
    """Validate an existing report file."""

    if not file_path:
        raise ValueError(
            "Report file path is required."
        )

    path = Path(file_path).expanduser()

    if not path.exists():
        raise FileNotFoundError(
            "Report file does not exist."
        )

    if not path.is_file():
        raise ValueError(
            "Report path must point to a file."
        )

    if path.suffix.lower().lstrip(".") not in SUPPORTED_REPORT_FORMATS:
        raise ValueError(
            "The report file format is not supported."
        )

    file_size = path.stat().st_size

    maximum_size = (
        MAX_REPORT_FILE_SIZE_MB * 1024 * 1024
    )

    if file_size > maximum_size:
        raise ValueError(
            "Report file exceeds the maximum allowed size."
        )

    if file_size == 0:
        raise ValueError(
            "Report file is empty."
        )

    return {
        "path": path.resolve(),
        "file_name": path.name,
        "file_type": path.suffix.lower().lstrip("."),
        "file_size": file_size,
    }


# ==================================================
# STORAGE PATH
# ==================================================

def generate_report_storage_path(
    user_id,
    file_type,
):
    """Generate a unique report storage path."""

    validate_user_id(user_id)

    file_type = validate_report_format(
        file_type
    )

    directory = (
        REPORTS_DIR / f"user_{user_id}"
    )

    directory.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = (
        f"jak_report_{uuid.uuid4().hex}.{file_type}"
    )

    return directory / filename


# ==================================================
# REGISTER REPORT
# ==================================================

def register_report(
    session,
    user_id,
    title,
    report_type,
    file_path,
    dataset_id=None,
    metadata=None,
):
    """Register an existing report in the database."""

    validate_user_id(user_id)

    title = validate_report_title(
        title
    )

    if not isinstance(report_type, str) or not report_type.strip():
        raise ValueError(
            "Report type is required."
        )

    if dataset_id is not None:
        if not isinstance(dataset_id, int) or isinstance(dataset_id, bool):
            raise ValueError(
                "Dataset ID must be an integer."
            )

        if dataset_id <= 0:
            raise ValueError(
                "Dataset ID must be greater than zero."
            )

    file_info = validate_report_file(
        file_path
    )

    if metadata is None:
        metadata = {}

    if not isinstance(metadata, dict):
        raise ValueError(
            "Report metadata must be a dictionary."
        )

    return report_repository.create_report(
        session=session,
        user_id=user_id,
        title=title,
        report_type=report_type.strip(),
        file_path=str(file_info["path"]),
        file_type=file_info["file_type"],
        file_size=file_info["file_size"],
        dataset_id=dataset_id,
        metadata=metadata,
    )


# ==================================================
# GET REPORT
# ==================================================

def get_report(
    session,
    report_id,
    user_id,
):
    """Retrieve a report belonging to a user."""

    validate_report_id(report_id)
    validate_user_id(user_id)

    return report_repository.get_report_by_id(
        session=session,
        report_id=report_id,
        user_id=user_id,
    )


# ==================================================
# LIST USER REPORTS
# ==================================================

def get_user_reports(
    session,
    user_id,
    limit=100,
    offset=0,
    dataset_id=None,
):
    """Retrieve reports belonging to a user."""

    validate_user_id(user_id)

    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError(
            "Limit must be an integer."
        )

    if not isinstance(offset, int) or isinstance(offset, bool):
        raise ValueError(
            "Offset must be an integer."
        )

    if limit < 1 or limit > 500:
        raise ValueError(
            "Limit must be between 1 and 500."
        )

    if offset < 0:
        raise ValueError(
            "Offset cannot be negative."
        )

    reports = report_repository.get_user_reports(
        session=session,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )

    if dataset_id is not None:
        reports = [
            report
            for report in reports
            if report.dataset_id == dataset_id
        ]

    return reports


# ==================================================
# COUNT REPORTS
# ==================================================

def count_user_reports(
    session,
    user_id,
):
    """Count reports belonging to a user."""

    validate_user_id(user_id)

    return report_repository.count_user_reports(
        session=session,
        user_id=user_id,
    )


# ==================================================
# SEARCH REPORTS
# ==================================================

def search_reports(
    session,
    user_id,
    search_term,
):
    """Search a user's reports."""

    validate_user_id(user_id)

    if not isinstance(search_term, str):
        raise ValueError(
            "Search term must be text."
        )

    search_term = search_term.strip()

    if not search_term:
        return []

    return report_repository.search_user_reports(
        session=session,
        user_id=user_id,
        search_term=search_term,
    )


# ==================================================
# UPDATE REPORT
# ==================================================

def update_report(
    session,
    report_id,
    user_id,
    title=None,
    metadata=None,
):
    """Update report information."""

    validate_report_id(report_id)
    validate_user_id(user_id)

    report = get_report(
        session,
        report_id,
        user_id,
    )

    if report is None:
        return None

    updates = {}

    if title is not None:
        updates["title"] = validate_report_title(
            title
        )

    if metadata is not None:
        if not isinstance(metadata, dict):
            raise ValueError(
                "Metadata must be a dictionary."
            )

        updates["metadata"] = metadata

    if not updates:
        return report

    return report_repository.update_report(
        session=session,
        report_id=report_id,
        user_id=user_id,
        **updates,
    )


# ==================================================
# UPDATE REPORT STATUS
# ==================================================

def update_report_status(
    session,
    report_id,
    user_id,
    status,
):
    """Update a report's status."""

    validate_report_id(report_id)
    validate_user_id(user_id)

    validate_report_status(
        status
    )

    report = get_report(
        session,
        report_id,
        user_id,
    )

    if report is None:
        return None

    metadata = dict(
        report.report_metadata or {}
    )

    metadata["status"] = status
    metadata["status_updated_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    return report_repository.update_report(
        session=session,
        report_id=report_id,
        user_id=user_id,
        metadata=metadata,
    )


# ==================================================
# DELETE REPORT
# ==================================================

def delete_report(
    session,
    report_id,
    user_id,
    delete_file=False,
):
    """
    Delete a report database record.

    If delete_file=True, return the safe file path
    for deletion after the database transaction commits.

    Physical file deletion is deliberately separated
    from database deletion.
    """

    validate_report_id(report_id)
    validate_user_id(user_id)

    if not isinstance(delete_file, bool):
        raise ValueError(
            "delete_file must be True or False."
        )

    report = get_report(
        session,
        report_id,
        user_id,
    )

    if report is None:
        return False

    file_path = report.file_path

    deleted = report_repository.delete_report(
        session=session,
        report_id=report_id,
        user_id=user_id,
    )

    if not deleted:
        return False

    if delete_file:
        return {
            "deleted": True,
            "file_path": file_path,
        }

    return True


# ==================================================
# SAFE PHYSICAL FILE DELETION
# ==================================================

def delete_report_file(file_path, user_id):
    """
    Delete a report file after its database record
    has been successfully deleted.

    Only files inside the user's report directory
    are eligible for deletion.
    """

    validate_user_id(user_id)

    if not file_path:
        return False

    path = Path(file_path).expanduser().resolve()

    allowed_directory = (
        REPORTS_DIR / f"user_{user_id}"
    ).resolve()

    try:
        path.relative_to(
            allowed_directory
        )
    except ValueError:
        raise ValueError(
            "File is outside the user's report directory."
        )

    if not path.exists():
        return False

    if not path.is_file():
        raise ValueError(
            "The requested path is not a file."
        )

    path.unlink()

    return True


# ==================================================
# REPORT STATISTICS
# ==================================================

def get_report_statistics(
    session,
    user_id,
):
    """Retrieve report statistics for a user."""

    validate_user_id(user_id)

    return report_repository.get_report_statistics(
        session=session,
        user_id=user_id,
    )


# ==================================================
# REPORT DOWNLOAD INFORMATION
# ==================================================

def prepare_report_download(
    session,
    report_id,
    user_id,
):
    """Prepare report information for a download request."""

    report = get_report(
        session,
        report_id,
        user_id,
    )

    if report is None:
        return None

    file_info = validate_report_file(
        report.file_path
    )

    return {
        "report_id": report.id,
        "title": report.title,
        "file_name": file_info["file_name"],
        "file_path": str(file_info["path"]),
        "file_type": file_info["file_type"],
        "file_size": file_info["file_size"],
    }