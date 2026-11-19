"""
JAK Data Analytics
Data Lineage Service

Tracks the history and origin of datasets.

Features:
- Dataset origin tracking
- Transformation history
- Parent and child dataset relationships
- Operation records
- Dataset version tracking
- Lineage summaries
- Lineage report generation
- Dataset dependency tracing

This service is independent of Streamlit.
"""

from datetime import datetime, timezone
from uuid import uuid4
import hashlib
import json


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

LINEAGE_VERSION = "1.0"

SUPPORTED_SOURCE_TYPES = {
    "upload",
    "database",
    "api",
    "manual",
    "generated",
    "transformation",
    "import",
}

SUPPORTED_OPERATION_TYPES = {
    "import",
    "cleaning",
    "transformation",
    "filtering",
    "merging",
    "aggregation",
    "validation",
    "analysis",
    "export",
    "other",
}


# ---------------------------------------------------------
# GENERAL UTILITIES
# ---------------------------------------------------------

def get_current_timestamp():
    """Return the current UTC timestamp."""

    return datetime.now(
        timezone.utc
    ).isoformat()


def generate_lineage_id():
    """Generate a unique lineage identifier."""

    return str(uuid4())


def generate_dataset_hash(data):
    """
    Generate a fingerprint for a dataset.

    The fingerprint is useful for identifying changes.
    """

    if data is None:
        raise ValueError(
            "Dataset is required."
        )

    if not hasattr(data, "shape"):
        raise ValueError(
            "Dataset must provide a shape attribute."
        )

    try:

        if hasattr(data, "to_csv"):

            content = data.to_csv(
                index=False,
                na_rep="<JAK_NULL>",
            )

        else:

            content = json.dumps(
                data,
                sort_keys=True,
                default=str,
            )

        return hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

    except Exception as error:

        raise ValueError(
            f"Could not generate dataset fingerprint: {error}"
        )


# ---------------------------------------------------------
# DATASET ORIGIN
# ---------------------------------------------------------

def create_dataset_origin(
    dataset_id,
    dataset_name,
    source_type="upload",
    source_details=None,
    user_id=None,
):
    """
    Create origin information for a dataset.
    """

    if not dataset_id:
        raise ValueError(
            "Dataset ID is required."
        )

    if not dataset_name:
        raise ValueError(
            "Dataset name is required."
        )

    if source_type not in SUPPORTED_SOURCE_TYPES:
        raise ValueError(
            f"Unsupported source type: {source_type}"
        )

    return {
        "lineage_id": generate_lineage_id(),
        "dataset_id": str(dataset_id),
        "dataset_name": str(dataset_name),
        "source_type": source_type,
        "source_details": source_details or {},
        "user_id": user_id,
        "created_at": get_current_timestamp(),
        "lineage_version": LINEAGE_VERSION,
    }


# ---------------------------------------------------------
# OPERATION RECORDS
# ---------------------------------------------------------

def create_operation_record(
    operation_type,
    operation_name,
    parameters=None,
    description=None,
    input_dataset_id=None,
    output_dataset_id=None,
    rows_before=None,
    rows_after=None,
    columns_before=None,
    columns_after=None,
    status="completed",
):
    """
    Create a record of a dataset operation.
    """

    if operation_type not in SUPPORTED_OPERATION_TYPES:
        raise ValueError(
            f"Unsupported operation type: {operation_type}"
        )

    if not operation_name:
        raise ValueError(
            "Operation name is required."
        )

    if status not in {
        "pending",
        "running",
        "completed",
        "failed",
    }:
        raise ValueError(
            "Invalid operation status."
        )

    return {
        "operation_id": generate_lineage_id(),
        "operation_type": operation_type,
        "operation_name": str(operation_name),
        "description": description or "",
        "parameters": parameters or {},
        "input_dataset_id": (
            str(input_dataset_id)
            if input_dataset_id is not None
            else None
        ),
        "output_dataset_id": (
            str(output_dataset_id)
            if output_dataset_id is not None
            else None
        ),
        "rows_before": rows_before,
        "rows_after": rows_after,
        "columns_before": columns_before,
        "columns_after": columns_after,
        "status": status,
        "executed_at": get_current_timestamp(),
    }


# ---------------------------------------------------------
# DATASET LINEAGE
# ---------------------------------------------------------

def create_dataset_lineage(
    dataset_id,
    dataset_name,
    source_type="upload",
    source_details=None,
    user_id=None,
    dataset_hash=None,
    rows=None,
    columns=None,
):
    """
    Create a complete initial lineage record.
    """

    origin = create_dataset_origin(
        dataset_id=dataset_id,
        dataset_name=dataset_name,
        source_type=source_type,
        source_details=source_details,
        user_id=user_id,
    )

    return {
        **origin,
        "dataset_hash": dataset_hash,
        "rows": rows,
        "columns": columns,
        "parent_dataset_ids": [],
        "child_dataset_ids": [],
        "operations": [],
        "version": 1,
        "last_updated": get_current_timestamp(),
    }


def validate_lineage(lineage):
    """Validate a lineage structure."""

    if not isinstance(lineage, dict):
        raise ValueError(
            "Lineage must be a dictionary."
        )

    required_fields = [
        "lineage_id",
        "dataset_id",
        "dataset_name",
        "operations",
        "parent_dataset_ids",
        "child_dataset_ids",
    ]

    missing = [
        field
        for field in required_fields
        if field not in lineage
    ]

    if missing:
        raise ValueError(
            f"Lineage is missing fields: {missing}"
        )

    if not isinstance(lineage["operations"], list):
        raise ValueError(
            "Lineage operations must be a list."
        )

    return True


# ---------------------------------------------------------
# ADD OPERATION
# ---------------------------------------------------------

def add_lineage_operation(
    lineage,
    operation_record,
):
    """
    Add an operation to a dataset's lineage.
    """

    validate_lineage(lineage)

    if not isinstance(operation_record, dict):
        raise ValueError(
            "A valid operation record is required."
        )

    updated = dict(lineage)

    updated["operations"] = [
        *lineage["operations"],
        operation_record,
    ]

    updated["version"] = (
        int(lineage.get("version", 1)) + 1
    )

    updated["last_updated"] = get_current_timestamp()

    return updated


# ---------------------------------------------------------
# DATASET RELATIONSHIPS
# ---------------------------------------------------------

def add_parent_dataset(
    lineage,
    parent_dataset_id,
):
    """
    Record a parent dataset relationship.
    """

    validate_lineage(lineage)

    parent_dataset_id = str(parent_dataset_id)

    if parent_dataset_id == str(lineage["dataset_id"]):
        raise ValueError(
            "A dataset cannot be its own parent."
        )

    updated = dict(lineage)

    parents = list(
        lineage.get("parent_dataset_ids", [])
    )

    if parent_dataset_id not in parents:
        parents.append(parent_dataset_id)

    updated["parent_dataset_ids"] = parents
    updated["last_updated"] = get_current_timestamp()

    return updated


def add_child_dataset(
    lineage,
    child_dataset_id,
):
    """
    Record a child dataset relationship.
    """

    validate_lineage(lineage)

    child_dataset_id = str(child_dataset_id)

    if child_dataset_id == str(lineage["dataset_id"]):
        raise ValueError(
            "A dataset cannot be its own child."
        )

    updated = dict(lineage)

    children = list(
        lineage.get("child_dataset_ids", [])
    )

    if child_dataset_id not in children:
        children.append(child_dataset_id)

    updated["child_dataset_ids"] = children
    updated["last_updated"] = get_current_timestamp()

    return updated


# ---------------------------------------------------------
# RECORD TRANSFORMATION
# ---------------------------------------------------------

def record_transformation(
    lineage,
    operation_name,
    parameters=None,
    description=None,
    output_dataset_id=None,
    rows_before=None,
    rows_after=None,
    columns_before=None,
    columns_after=None,
    status="completed",
):
    """
    Record a transformation performed on a dataset.
    """

    operation = create_operation_record(
        operation_type="transformation",
        operation_name=operation_name,
        parameters=parameters,
        description=description,
        input_dataset_id=lineage["dataset_id"],
        output_dataset_id=output_dataset_id,
        rows_before=rows_before,
        rows_after=rows_after,
        columns_before=columns_before,
        columns_after=columns_after,
        status=status,
    )

    return add_lineage_operation(
        lineage,
        operation,
    )


# ---------------------------------------------------------
# RECORD CLEANING
# ---------------------------------------------------------

def record_cleaning(
    lineage,
    operation_name,
    parameters=None,
    rows_before=None,
    rows_after=None,
):
    """
    Record a data cleaning operation.
    """

    operation = create_operation_record(
        operation_type="cleaning",
        operation_name=operation_name,
        parameters=parameters,
        input_dataset_id=lineage["dataset_id"],
        rows_before=rows_before,
        rows_after=rows_after,
    )

    return add_lineage_operation(
        lineage,
        operation,
    )


# ---------------------------------------------------------
# RECORD VALIDATION
# ---------------------------------------------------------

def record_validation(
    lineage,
    validation_name,
    validation_score=None,
    passed=None,
    details=None,
):
    """
    Record a dataset validation operation.
    """

    parameters = {
        "validation_score": validation_score,
        "passed": passed,
        "details": details or {},
    }

    operation = create_operation_record(
        operation_type="validation",
        operation_name=validation_name,
        parameters=parameters,
        input_dataset_id=lineage["dataset_id"],
    )

    return add_lineage_operation(
        lineage,
        operation,
    )


# ---------------------------------------------------------
# RECORD ANALYSIS
# ---------------------------------------------------------

def record_analysis(
    lineage,
    analysis_name,
    parameters=None,
    description=None,
):
    """
    Record an analysis performed on a dataset.
    """

    operation = create_operation_record(
        operation_type="analysis",
        operation_name=analysis_name,
        parameters=parameters,
        description=description,
        input_dataset_id=lineage["dataset_id"],
    )

    return add_lineage_operation(
        lineage,
        operation,
    )


# ---------------------------------------------------------
# RECORD EXPORT
# ---------------------------------------------------------

def record_export(
    lineage,
    export_format,
    output_file=None,
    rows_exported=None,
):
    """
    Record a dataset export.
    """

    operation = create_operation_record(
        operation_type="export",
        operation_name=f"Export to {export_format}",
        parameters={
            "format": export_format,
            "output_file": output_file,
            "rows_exported": rows_exported,
        },
        input_dataset_id=lineage["dataset_id"],
        rows_before=lineage.get("rows"),
        rows_after=rows_exported,
    )

    return add_lineage_operation(
        lineage,
        operation,
    )


# ---------------------------------------------------------
# UPDATE DATASET SNAPSHOT
# ---------------------------------------------------------

def update_lineage_snapshot(
    lineage,
    dataset_hash=None,
    rows=None,
    columns=None,
):
    """
    Update the current dataset information.
    """

    validate_lineage(lineage)

    updated = dict(lineage)

    if dataset_hash is not None:
        updated["dataset_hash"] = dataset_hash

    if rows is not None:
        updated["rows"] = rows

    if columns is not None:
        updated["columns"] = columns

    updated["last_updated"] = get_current_timestamp()

    return updated


# ---------------------------------------------------------
# LINEAGE SUMMARY
# ---------------------------------------------------------

def get_lineage_summary(lineage):
    """
    Generate a summary of dataset lineage.
    """

    validate_lineage(lineage)

    operations = lineage["operations"]

    completed = sum(
        operation.get("status") == "completed"
        for operation in operations
    )

    failed = sum(
        operation.get("status") == "failed"
        for operation in operations
    )

    return {
        "dataset_id": lineage["dataset_id"],
        "dataset_name": lineage["dataset_name"],
        "source_type": lineage.get("source_type"),
        "version": lineage.get("version", 1),
        "total_operations": len(operations),
        "completed_operations": completed,
        "failed_operations": failed,
        "parent_datasets": len(
            lineage.get("parent_dataset_ids", [])
        ),
        "child_datasets": len(
            lineage.get("child_dataset_ids", [])
        ),
        "rows": lineage.get("rows"),
        "columns": lineage.get("columns"),
        "created_at": lineage.get("created_at"),
        "last_updated": lineage.get("last_updated"),
    }


# ---------------------------------------------------------
# OPERATION HISTORY
# ---------------------------------------------------------

def get_operation_history(lineage):
    """
    Return all recorded operations.
    """

    validate_lineage(lineage)

    return list(
        lineage["operations"]
    )


def filter_operation_history(
    lineage,
    operation_type=None,
    status=None,
):
    """
    Filter operation history.
    """

    validate_lineage(lineage)

    results = []

    for operation in lineage["operations"]:

        if (
            operation_type
            and operation.get("operation_type") != operation_type
        ):
            continue

        if (
            status
            and operation.get("status") != status
        ):
            continue

        results.append(operation)

    return results


# ---------------------------------------------------------
# LINEAGE REPORT
# ---------------------------------------------------------

def generate_lineage_report(lineage):
    """
    Generate a report containing lineage information.
    """

    validate_lineage(lineage)

    summary = get_lineage_summary(lineage)

    return {
        "summary": summary,
        "origin": {
            "source_type": lineage.get("source_type"),
            "source_details": lineage.get("source_details", {}),
            "created_at": lineage.get("created_at"),
            "user_id": lineage.get("user_id"),
        },
        "relationships": {
            "parents": lineage.get(
                "parent_dataset_ids",
                [],
            ),
            "children": lineage.get(
                "child_dataset_ids",
                [],
            ),
        },
        "operations": get_operation_history(lineage),
    }


# ---------------------------------------------------------
# EXPORT LINEAGE
# ---------------------------------------------------------

def export_lineage_json(lineage, output_path=None):
    """
    Export lineage information as JSON.

    If output_path is omitted, JSON text is returned.
    """

    validate_lineage(lineage)

    content = json.dumps(
        lineage,
        indent=4,
        ensure_ascii=False,
        default=str,
    )

    if output_path is None:
        return content

    from pathlib import Path

    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        content,
        encoding="utf-8",
    )

    return str(path)


# ---------------------------------------------------------
# IMPORT LINEAGE
# ---------------------------------------------------------

def import_lineage_json(source):
    """
    Import lineage information from a JSON file
    or JSON text.
    """

    from pathlib import Path

    if isinstance(source, dict):
        lineage = source

    elif isinstance(source, Path):
        lineage = json.loads(
            source.read_text(encoding="utf-8")
        )

    elif isinstance(source, str):

        if source.lstrip().startswith("{"):
            lineage = json.loads(source)

        else:
            path = Path(source)

            lineage = json.loads(
                path.read_text(encoding="utf-8")
            )

    else:
        raise ValueError(
            "Source must be a dictionary, JSON string, or file path."
        )

    validate_lineage(lineage)

    return lineage


# ---------------------------------------------------------
# LINEAGE COMPARISON
# ---------------------------------------------------------

def compare_lineage_versions(
    first_lineage,
    second_lineage,
):
    """
    Compare two lineage snapshots of the same dataset.
    """

    validate_lineage(first_lineage)
    validate_lineage(second_lineage)

    if (
        str(first_lineage["dataset_id"])
        != str(second_lineage["dataset_id"])
    ):
        raise ValueError(
            "Cannot compare lineage records for different datasets."
        )

    first_hash = first_lineage.get("dataset_hash")
    second_hash = second_lineage.get("dataset_hash")

    return {
        "dataset_id": first_lineage["dataset_id"],
        "first_version": first_lineage.get("version"),
        "second_version": second_lineage.get("version"),
        "hashes_match": (
            first_hash == second_hash
            if first_hash and second_hash
            else None
        ),
        "rows_changed": (
            first_lineage.get("rows")
            != second_lineage.get("rows")
        ),
        "columns_changed": (
            first_lineage.get("columns")
            != second_lineage.get("columns")
        ),
        "operations_added": max(
            0,
            len(second_lineage["operations"])
            - len(first_lineage["operations"]),
        ),
    }
