"""
JAK Data Analytics
Data Catalog Service

Provides a central catalogue for dataset discovery
and metadata management.

Features:
- Dataset registration
- Dataset descriptions
- Dataset categorisation
- Dataset tagging
- Dataset ownership
- Dataset metadata
- Dataset search
- Dataset filtering
- Dataset statistics
- Dataset recommendations
- Catalogue export

This service is independent of Streamlit.
"""

from datetime import datetime, timezone
from uuid import uuid4
import re


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

SUPPORTED_DATASET_STATUSES = {
    "active",
    "archived",
    "draft",
    "processing",
    "restricted",
}

SUPPORTED_ACCESS_LEVELS = {
    "private",
    "shared",
    "public",
}

SUPPORTED_CATEGORIES = {
    "business",
    "finance",
    "education",
    "healthcare",
    "agriculture",
    "marketing",
    "transport",
    "manufacturing",
    "weather",
    "environment",
    "energy",
    "technology",
    "government",
    "research",
    "other",
}


# ---------------------------------------------------------
# GENERAL UTILITIES
# ---------------------------------------------------------

def current_timestamp():
    """Return the current UTC timestamp."""

    return datetime.now(
        timezone.utc
    ).isoformat()


def generate_catalog_id():
    """Generate a unique catalogue identifier."""

    return str(uuid4())


def normalize_text(value):
    """Normalize text for searching."""

    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value).strip(),
    )


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_dataset_metadata(metadata):
    """Validate dataset metadata."""

    if not isinstance(metadata, dict):
        raise ValueError(
            "Dataset metadata must be a dictionary."
        )

    required = [
        "dataset_id",
        "name",
        "owner_id",
    ]

    missing = [
        field
        for field in required
        if metadata.get(field) is None
        or metadata.get(field) == ""
    ]

    if missing:
        raise ValueError(
            f"Missing required metadata: {missing}"
        )

    if metadata.get("status") not in SUPPORTED_DATASET_STATUSES:
        raise ValueError(
            "Invalid dataset status."
        )

    if metadata.get("access_level") not in SUPPORTED_ACCESS_LEVELS:
        raise ValueError(
            "Invalid dataset access level."
        )

    return True


# ---------------------------------------------------------
# REGISTER DATASET
# ---------------------------------------------------------

def register_dataset(
    dataset_id,
    name,
    owner_id,
    description="",
    category="other",
    tags=None,
    source="upload",
    access_level="private",
    status="active",
    row_count=0,
    column_count=0,
    file_format=None,
    file_size_bytes=0,
    metadata=None,
):
    """
    Register a dataset in the catalogue.
    """

    if dataset_id is None:
        raise ValueError(
            "Dataset ID is required."
        )

    if not normalize_text(name):
        raise ValueError(
            "Dataset name is required."
        )

    if owner_id is None:
        raise ValueError(
            "Dataset owner is required."
        )

    if category not in SUPPORTED_CATEGORIES:
        raise ValueError(
            f"Unsupported category: {category}"
        )

    if status not in SUPPORTED_DATASET_STATUSES:
        raise ValueError(
            f"Unsupported status: {status}"
        )

    if access_level not in SUPPORTED_ACCESS_LEVELS:
        raise ValueError(
            f"Unsupported access level: {access_level}"
        )

    if row_count < 0 or column_count < 0:
        raise ValueError(
            "Dataset dimensions cannot be negative."
        )

    if file_size_bytes < 0:
        raise ValueError(
            "File size cannot be negative."
        )

    if tags is None:
        tags = []

    if not isinstance(tags, list):
        raise ValueError(
            "Tags must be provided as a list."
        )

    normalized_tags = list(dict.fromkeys(
        normalize_text(tag).lower()
        for tag in tags
        if normalize_text(tag)
    ))

    record = {
        "catalog_id": generate_catalog_id(),
        "dataset_id": str(dataset_id),
        "name": normalize_text(name),
        "description": normalize_text(description),
        "owner_id": str(owner_id),
        "category": category,
        "tags": normalized_tags,
        "source": normalize_text(source),
        "access_level": access_level,
        "status": status,
        "row_count": int(row_count),
        "column_count": int(column_count),
        "file_format": (
            normalize_text(file_format).lower()
            if file_format
            else None
        ),
        "file_size_bytes": int(file_size_bytes),
        "metadata": metadata or {},
        "created_at": current_timestamp(),
        "updated_at": current_timestamp(),
        "last_accessed": None,
        "access_count": 0,
    }

    validate_dataset_metadata(record)

    return record


# ---------------------------------------------------------
# UPDATE DATASET
# ---------------------------------------------------------

def update_dataset_metadata(
    record,
    updates,
):
    """
    Update editable dataset catalogue information.
    """

    if not isinstance(record, dict):
        raise ValueError(
            "A valid catalogue record is required."
        )

    if not isinstance(updates, dict):
        raise ValueError(
            "Updates must be a dictionary."
        )

    allowed_fields = {
        "name",
        "description",
        "category",
        "tags",
        "source",
        "access_level",
        "status",
        "metadata",
    }

    invalid_fields = set(updates) - allowed_fields

    if invalid_fields:
        raise ValueError(
            f"Fields cannot be updated: {sorted(invalid_fields)}"
        )

    updated = dict(record)

    for field, value in updates.items():

        if field in {
            "name",
            "description",
            "source",
        }:

            value = normalize_text(value)

            if field == "name" and not value:
                raise ValueError(
                    "Dataset name cannot be empty."
                )

        elif field == "category":

            if value not in SUPPORTED_CATEGORIES:
                raise ValueError(
                    "Invalid dataset category."
                )

        elif field == "status":

            if value not in SUPPORTED_DATASET_STATUSES:
                raise ValueError(
                    "Invalid dataset status."
                )

        elif field == "access_level":

            if value not in SUPPORTED_ACCESS_LEVELS:
                raise ValueError(
                    "Invalid access level."
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

        elif field == "metadata":

            if not isinstance(value, dict):
                raise ValueError(
                    "Metadata must be a dictionary."
                )

        updated[field] = value

    updated["updated_at"] = current_timestamp()

    validate_dataset_metadata(updated)

    return updated


# ---------------------------------------------------------
# TAG MANAGEMENT
# ---------------------------------------------------------

def add_dataset_tags(record, tags):
    """Add tags to a dataset."""

    if isinstance(tags, str):
        tags = [tags]

    if not isinstance(tags, list):
        raise ValueError(
            "Tags must be a list or string."
        )

    existing = list(
        record.get("tags", [])
    )

    combined = existing + [
        normalize_text(tag).lower()
        for tag in tags
        if normalize_text(tag)
    ]

    return update_dataset_metadata(
        record,
        {"tags": list(dict.fromkeys(combined))},
    )


def remove_dataset_tags(record, tags):
    """Remove selected tags."""

    if isinstance(tags, str):
        tags = [tags]

    remove = {
        normalize_text(tag).lower()
        for tag in tags
    }

    remaining = [
        tag
        for tag in record.get("tags", [])
        if tag not in remove
    ]

    return update_dataset_metadata(
        record,
        {"tags": remaining},
    )


# ---------------------------------------------------------
# ACCESS TRACKING
# ---------------------------------------------------------

def record_dataset_access(record):
    """
    Record a dataset access event.

    This function does not itself enforce permissions.
    Access control must be checked before calling it.
    """

    updated = dict(record)

    updated["access_count"] = (
        int(record.get("access_count", 0)) + 1
    )

    updated["last_accessed"] = current_timestamp()

    return updated


# ---------------------------------------------------------
# SEARCH
# ---------------------------------------------------------

def search_catalog(
    catalog,
    search_term,
    owner_id=None,
    category=None,
    status=None,
    access_level=None,
):
    """
    Search catalogue records.

    This function filters the supplied catalogue.
    It does not independently enforce access permissions.
    """

    if not isinstance(catalog, list):
        raise ValueError(
            "Catalogue must be a list."
        )

    query = normalize_text(
        search_term
    ).casefold()

    results = []

    for record in catalog:

        if not isinstance(record, dict):
            continue

        if owner_id is not None:

            if str(record.get("owner_id")) != str(owner_id):
                continue

        if category and record.get("category") != category:
            continue

        if status and record.get("status") != status:
            continue

        if (
            access_level
            and record.get("access_level") != access_level
        ):
            continue

        searchable = " ".join([
            str(record.get("name", "")),
            str(record.get("description", "")),
            str(record.get("category", "")),
            str(record.get("source", "")),
            " ".join(record.get("tags", [])),
        ]).casefold()

        if not query or query in searchable:
            results.append(record)

    return results


# ---------------------------------------------------------
# FILTERING
# ---------------------------------------------------------

def filter_catalog(
    catalog,
    categories=None,
    tags=None,
    statuses=None,
    formats=None,
    minimum_rows=None,
    maximum_rows=None,
):
    """Filter catalogue records using multiple conditions."""

    if not isinstance(catalog, list):
        raise ValueError(
            "Catalogue must be a list."
        )

    results = []

    for record in catalog:

        if categories and record.get("category") not in categories:
            continue

        if statuses and record.get("status") not in statuses:
            continue

        if formats and record.get("file_format") not in formats:
            continue

        record_tags = set(
            record.get("tags", [])
        )

        if tags and not set(tags).issubset(record_tags):
            continue

        rows = int(
            record.get("row_count", 0)
        )

        if minimum_rows is not None and rows < minimum_rows:
            continue

        if maximum_rows is not None and rows > maximum_rows:
            continue

        results.append(record)

    return results


# ---------------------------------------------------------
# DATASET LOOKUP
# ---------------------------------------------------------

def get_catalog_dataset(
    catalog,
    dataset_id,
    owner_id=None,
):
    """
    Retrieve a dataset from the catalogue.

    If owner_id is supplied, lookup is restricted
    to that owner.
    """

    for record in catalog:

        if str(record.get("dataset_id")) != str(dataset_id):
            continue

        if (
            owner_id is not None
            and str(record.get("owner_id")) != str(owner_id)
        ):
            continue

        return record

    return None


# ---------------------------------------------------------
# CATALOGUE STATISTICS
# ---------------------------------------------------------

def get_catalog_statistics(catalog):
    """Calculate catalogue statistics."""

    if not isinstance(catalog, list):
        raise ValueError(
            "Catalogue must be a list."
        )

    total = len(catalog)

    categories = {}
    formats = {}
    statuses = {}

    total_rows = 0
    total_storage = 0

    for record in catalog:

        category = record.get(
            "category",
            "other",
        )

        file_format = record.get(
            "file_format",
            "unknown",
        )

        status = record.get(
            "status",
            "unknown",
        )

        categories[category] = (
            categories.get(category, 0) + 1
        )

        formats[file_format] = (
            formats.get(file_format, 0) + 1
        )

        statuses[status] = (
            statuses.get(status, 0) + 1
        )

        total_rows += int(
            record.get("row_count", 0)
        )

        total_storage += int(
            record.get("file_size_bytes", 0)
        )

    return {
        "total_datasets": total,
        "total_rows": total_rows,
        "total_storage_bytes": total_storage,
        "average_rows_per_dataset": (
            round(total_rows / total, 2)
            if total
            else 0
        ),
        "categories": categories,
        "formats": formats,
        "statuses": statuses,
    }


# ---------------------------------------------------------
# TAG DISCOVERY
# ---------------------------------------------------------

def get_popular_tags(catalog, limit=20):
    """Return the most frequently used tags."""

    tag_counts = {}

    for record in catalog:

        for tag in record.get("tags", []):

            tag_counts[tag] = (
                tag_counts.get(tag, 0) + 1
            )

    sorted_tags = sorted(
        tag_counts.items(),
        key=lambda item: (-item[1], item[0]),
    )

    return [
        {
            "tag": tag,
            "count": count,
        }
        for tag, count in sorted_tags[:limit]
    ]


# ---------------------------------------------------------
# RELATED DATASETS
# ---------------------------------------------------------

def find_related_datasets(
    catalog,
    dataset_id,
    limit=10,
):
    """
    Find datasets sharing categories or tags.
    """

    target = None

    for record in catalog:

        if str(record.get("dataset_id")) == str(dataset_id):
            target = record
            break

    if target is None:
        return []

    target_tags = set(
        target.get("tags", [])
    )

    related = []

    for record in catalog:

        if str(record.get("dataset_id")) == str(dataset_id):
            continue

        shared_tags = target_tags.intersection(
            set(record.get("tags", []))
        )

        same_category = (
            record.get("category")
            == target.get("category")
        )

        score = (
            len(shared_tags)
            + (2 if same_category else 0)
        )

        if score > 0:

            related.append({
                "dataset": record,
                "similarity_score": score,
                "shared_tags": sorted(shared_tags),
                "same_category": same_category,
            })

    related.sort(
        key=lambda item: item["similarity_score"],
        reverse=True,
    )

    return related[:limit]


# ---------------------------------------------------------
# CATALOGUE EXPORT
# ---------------------------------------------------------

def export_catalog_metadata(catalog):
    """
    Convert catalogue records into a list
    suitable for JSON serialization.
    """

    if not isinstance(catalog, list):
        raise ValueError(
            "Catalogue must be a list."
        )

    return [
        dict(record)
        for record in catalog
    ]


# ---------------------------------------------------------
# CATALOGUE REPORT
# ---------------------------------------------------------

def generate_catalog_report(catalog):
    """Generate a complete catalogue report."""

    statistics = get_catalog_statistics(catalog)

    popular_tags = get_popular_tags(catalog)

    return {
        "generated_at": current_timestamp(),
        "statistics": statistics,
        "popular_tags": popular_tags,
        "datasets": export_catalog_metadata(catalog),
    }
