"""
JAK Data Analytics
Dataset Repository

Handles database operations for datasets.

Features:
- Register uploaded datasets
- Retrieve datasets
- List user datasets
- Search datasets
- Update dataset information
- Update dataset statistics
- Change dataset status
- Delete dataset records
- Count datasets

Security:
All user-specific operations check dataset ownership.

Important:
Deleting a dataset record does not delete its physical
file. Physical file cleanup is handled by the storage service.

Transactions are managed by the service layer.
"""

from sqlalchemy import select, func, or_

from ..models import Dataset


# ==================================================
# CREATE DATASET
# ==================================================

def create_dataset(
    session,
    user_id,
    name,
    original_filename=None,
    file_path=None,
    file_format=None,
    file_size=0,
    description=None,
    project_id=None,
    row_count=0,
    column_count=0,
    dataset_metadata=None
):
    """Register a dataset in the database."""

    if not user_id:
        raise ValueError("User ID is required.")

    name = name.strip()

    if not name:
        raise ValueError("Dataset name is required.")

    if file_size < 0:
        raise ValueError("File size cannot be negative.")

    if row_count < 0 or column_count < 0:
        raise ValueError("Dataset dimensions cannot be negative.")

    dataset = Dataset(
        user_id=user_id,
        project_id=project_id,
        name=name,
        description=description,
        original_filename=original_filename,
        file_path=file_path,
        file_format=file_format,
        file_size=file_size,
        row_count=row_count,
        column_count=column_count,
        dataset_metadata=dataset_metadata,
        status="uploaded"
    )

    session.add(dataset)
    session.flush()

    return dataset


# ==================================================
# GET DATASET BY ID
# ==================================================

def get_dataset_by_id(
    session,
    dataset_id,
    user_id
):
    """Retrieve a dataset belonging to a specific user."""

    statement = select(Dataset).where(
        Dataset.id == dataset_id,
        Dataset.user_id == user_id
    )

    return session.execute(
        statement
    ).scalar_one_or_none()


# ==================================================
# GET USER DATASETS
# ==================================================

def get_user_datasets(
    session,
    user_id,
    limit=100,
    offset=0,
    status=None,
    project_id=None
):
    """Retrieve datasets belonging to a user."""

    statement = select(Dataset).where(
        Dataset.user_id == user_id
    )

    if status:
        statement = statement.where(
            Dataset.status == status
        )

    if project_id is not None:
        statement = statement.where(
            Dataset.project_id == project_id
        )

    statement = (
        statement
        .order_by(
            Dataset.created_at.desc(),
            Dataset.id.desc()
        )
        .offset(max(0, offset))
        .limit(max(1, min(limit, 500)))
    )

    return list(
        session.execute(statement).scalars().all()
    )


# ==================================================
# COUNT USER DATASETS
# ==================================================

def count_user_datasets(
    session,
    user_id,
    status=None
):
    """Count datasets belonging to a user."""

    statement = select(
        func.count(Dataset.id)
    ).where(
        Dataset.user_id == user_id
    )

    if status:
        statement = statement.where(
            Dataset.status == status
        )

    return session.execute(
        statement
    ).scalar_one()


# ==================================================
# SEARCH USER DATASETS
# ==================================================

def search_user_datasets(
    session,
    user_id,
    search_term,
    limit=100
):
    """Search datasets by name, description or filename."""

    search_term = search_term.strip()

    if not search_term:
        return []

    pattern = f"%{search_term}%"

    statement = (
        select(Dataset)
        .where(
            Dataset.user_id == user_id,
            or_(
                Dataset.name.ilike(pattern),
                Dataset.description.ilike(pattern),
                Dataset.original_filename.ilike(pattern)
            )
        )
        .order_by(Dataset.created_at.desc())
        .limit(max(1, min(limit, 200)))
    )

    return list(
        session.execute(statement).scalars().all()
    )


# ==================================================
# UPDATE DATASET INFORMATION
# ==================================================

def update_dataset(
    session,
    dataset_id,
    user_id,
    name=None,
    description=None,
    project_id=None,
    dataset_metadata=None
):
    """Update dataset information after checking ownership."""

    dataset = get_dataset_by_id(
        session,
        dataset_id,
        user_id
    )

    if dataset is None:
        return None

    if name is not None:

        name = name.strip()

        if not name:
            raise ValueError("Dataset name cannot be empty.")

        dataset.name = name

    if description is not None:
        dataset.description = description

    if project_id is not None:
        dataset.project_id = project_id

    if dataset_metadata is not None:
        dataset.dataset_metadata = dataset_metadata

    session.flush()

    return dataset


# ==================================================
# UPDATE DATASET STATISTICS
# ==================================================

def update_dataset_statistics(
    session,
    dataset_id,
    user_id,
    row_count,
    column_count,
    quality_score=None
):
    """Update dataset dimensions and quality score."""

    if row_count < 0 or column_count < 0:
        raise ValueError("Dataset dimensions cannot be negative.")

    if quality_score is not None:

        if not 0 <= quality_score <= 100:
            raise ValueError("Quality score must be between 0 and 100.")

    dataset = get_dataset_by_id(
        session,
        dataset_id,
        user_id
    )

    if dataset is None:
        return None

    dataset.row_count = row_count
    dataset.column_count = column_count

    if quality_score is not None:
        dataset.quality_score = quality_score

    session.flush()

    return dataset


# ==================================================
# UPDATE DATASET STATUS
# ==================================================

def update_dataset_status(
    session,
    dataset_id,
    user_id,
    status
):
    """Change dataset processing status."""

    allowed_statuses = {
        "uploaded",
        "processing",
        "completed",
        "failed"
    }

    status = status.strip().lower()

    if status not in allowed_statuses:
        raise ValueError("Invalid dataset status.")

    dataset = get_dataset_by_id(
        session,
        dataset_id,
        user_id
    )

    if dataset is None:
        return None

    dataset.status = status

    session.flush()

    return dataset


# ==================================================
# UPDATE DATASET FILE LOCATION
# ==================================================

def update_dataset_file(
    session,
    dataset_id,
    user_id,
    file_path,
    original_filename=None,
    file_format=None,
    file_size=None
):
    """Update the physical storage reference for a dataset."""

    if not file_path:
        raise ValueError("File path is required.")

    dataset = get_dataset_by_id(
        session,
        dataset_id,
        user_id
    )

    if dataset is None:
        return None

    dataset.file_path = file_path

    if original_filename is not None:
        dataset.original_filename = original_filename

    if file_format is not None:
        dataset.file_format = file_format

    if file_size is not None:

        if file_size < 0:
            raise ValueError("File size cannot be negative.")

        dataset.file_size = file_size

    session.flush()

    return dataset


# ==================================================
# GET DATASET STATISTICS
# ==================================================

def get_dataset_statistics(
    session,
    user_id
):
    """Return dataset statistics for a user."""

    statement = (
        select(
            func.count(Dataset.id),
            func.coalesce(func.sum(Dataset.row_count), 0),
            func.coalesce(func.sum(Dataset.file_size), 0),
            func.coalesce(func.sum(Dataset.column_count), 0)
        )
        .where(Dataset.user_id == user_id)
    )

    total, rows, size, columns = session.execute(
        statement
    ).one()

    return {
        "total_datasets": total,
        "total_rows": rows,
        "total_file_size": size,
        "total_columns": columns
    }


# ==================================================
# DELETE DATASET RECORD
# ==================================================

def delete_dataset(
    session,
    dataset_id,
    user_id
):
    """
    Delete a dataset database record.

    This does not remove the physical dataset file.
    The storage service must handle file cleanup separately.
    """

    dataset = get_dataset_by_id(
        session,
        dataset_id,
        user_id
    )

    if dataset is None:
        return False

    session.delete(dataset)
    session.flush()

    return True