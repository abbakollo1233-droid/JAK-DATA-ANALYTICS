"""
JAK Data Analytics
Dataset Service

Handles dataset-related business logic.

Features:
- Dataset registration
- Dataset retrieval
- Dataset listing
- Dataset searching
- Dataset metadata updates
- Dataset statistics
- Dataset status management
- Dataset deletion
- File validation

Database transactions are managed by the caller.
Physical file operations are handled carefully and separately.
"""

import hashlib
from pathlib import Path

from ..config.settings import (
    DATASETS_DIR,
    MAX_UPLOAD_SIZE_MB,
    ALLOWED_FILE_EXTENSIONS,
)

from ..database.repositories import dataset_repository


# ==================================================
# DATASET CONFIGURATION
# ==================================================

MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

ALLOWED_EXTENSIONS = {
    extension.lower()
    for extension in ALLOWED_FILE_EXTENSIONS
}


# ==================================================
# VALIDATE DATASET FILE
# ==================================================

def validate_dataset_file(file_path):
    """Validate dataset file extension and size."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError("Dataset file was not found.")

    if not path.is_file():
        raise ValueError("The selected path is not a file.")

    extension = path.suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format: {extension}"
        )

    file_size = path.stat().st_size

    if file_size > MAX_UPLOAD_SIZE_BYTES:
        raise ValueError(
            f"Dataset exceeds the {MAX_UPLOAD_SIZE_MB} MB upload limit."
        )

    if file_size == 0:
        raise ValueError("The uploaded dataset is empty.")

    return {
        "valid": True,
        "extension": extension,
        "file_size": file_size,
        "file_size_mb": round(
            file_size / (1024 * 1024), 2
        ),
    }


# ==================================================
# CALCULATE FILE HASH
# ==================================================

def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of a dataset file."""

    file_hash = hashlib.sha256()

    with open(file_path, "rb") as file:

        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b""
        ):
            file_hash.update(chunk)

    return file_hash.hexdigest()


# ==================================================
# GENERATE STORAGE PATH
# ==================================================

def generate_dataset_storage_path(
    user_id,
    filename,
):
    """
    Generate a storage location for a user's dataset.

    The filename is generated using a random identifier
    to avoid collisions and unsafe user-supplied names.
    """

    import uuid

    if not user_id:
        raise ValueError("User ID is required.")

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported dataset format.")

    user_directory = DATASETS_DIR / str(user_id)

    user_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    stored_filename = (
        f"{uuid.uuid4().hex}{extension}"
    )

    return user_directory / stored_filename


# ==================================================
# REGISTER DATASET
# ==================================================

def register_dataset(
    session,
    user_id,
    name,
    file_path,
    row_count,
    column_count,
    description=None,
    project_id=None,
    metadata=None,
):
    """Register an uploaded dataset in the database."""

    if not user_id:
        raise ValueError("User ID is required.")

    name = (name or "").strip()

    if not name:
        raise ValueError("Dataset name is required.")

    if row_count < 0 or column_count < 0:
        raise ValueError("Dataset dimensions cannot be negative.")

    validation = validate_dataset_file(file_path)

    path = Path(file_path)

    file_hash = calculate_file_hash(path)

    dataset_metadata = dict(metadata or {})

    dataset_metadata.update({
        "file_hash": file_hash,
        "file_extension": validation["extension"],
        "file_size_bytes": validation["file_size"],
        "file_size_mb": validation["file_size_mb"],
    })

    dataset = dataset_repository.create_dataset(
        session=session,
        user_id=user_id,
        name=name,
        file_path=str(path.resolve()),
        file_type=validation["extension"].replace(".", ""),
        file_size=validation["file_size"],
        row_count=row_count,
        column_count=column_count,
        description=description,
        project_id=project_id,
        metadata=dataset_metadata,
        status="completed",
    )

    return dataset


# ==================================================
# GET DATASET
# ==================================================

def get_dataset(
    session,
    dataset_id,
    user_id,
):
    """Retrieve a dataset belonging to a user."""

    if not dataset_id or not user_id:
        return None

    return dataset_repository.get_dataset_by_id(
        session,
        dataset_id,
        user_id,
    )


# ==================================================
# GET USER DATASETS
# ==================================================

def get_user_datasets(
    session,
    user_id,
    limit=100,
    offset=0,
    status=None,
):
    """Retrieve datasets belonging to a user."""

    if not user_id:
        return []

    datasets = dataset_repository.get_user_datasets(
        session,
        user_id,
        limit=limit,
        offset=offset,
    )

    if status:
        datasets = [
            dataset
            for dataset in datasets
            if dataset.status == status
        ]

    return datasets


# ==================================================
# SEARCH DATASETS
# ==================================================

def search_datasets(
    session,
    user_id,
    search_term,
    limit=100,
):
    """Search datasets belonging to a user."""

    if not user_id:
        return []

    search_term = (search_term or "").strip()

    if not search_term:
        return []

    return dataset_repository.search_user_datasets(
        session,
        user_id,
        search_term,
        limit=limit,
    )


# ==================================================
# UPDATE DATASET INFORMATION
# ==================================================

def update_dataset_information(
    session,
    dataset_id,
    user_id,
    name=None,
    description=None,
    project_id=None,
):
    """Update dataset information."""

    dataset = get_dataset(
        session,
        dataset_id,
        user_id,
    )

    if dataset is None:
        raise ValueError("Dataset was not found.")

    if name is not None:

        name = name.strip()

        if not name:
            raise ValueError("Dataset name cannot be empty.")

    if description is not None:
        description = description.strip() or None

    return dataset_repository.update_dataset(
        session=session,
        dataset_id=dataset_id,
        user_id=user_id,
        name=name,
        description=description,
        project_id=project_id,
    )


# ==================================================
# UPDATE DATASET STATISTICS
# ==================================================

def update_dataset_statistics(
    session,
    dataset_id,
    user_id,
    row_count,
    column_count,
    quality_score=None,
):
    """Update dataset dimensions and quality score."""

    if row_count < 0 or column_count < 0:
        raise ValueError("Dataset dimensions cannot be negative.")

    if quality_score is not None:

        if not 0 <= quality_score <= 100:
            raise ValueError(
                "Quality score must be between 0 and 100."
            )

    dataset = get_dataset(
        session,
        dataset_id,
        user_id,
    )

    if dataset is None:
        raise ValueError("Dataset was not found.")

    return dataset_repository.update_dataset_statistics(
        session,
        dataset_id,
        user_id,
        row_count,
        column_count,
        quality_score,
    )


# ==================================================
# UPDATE DATASET STATUS
# ==================================================

def change_dataset_status(
    session,
    dataset_id,
    user_id,
    status,
):
    """Change dataset processing status."""

    allowed_statuses = [
        "uploaded",
        "processing",
        "completed",
        "failed",
    ]

    if status not in allowed_statuses:
        raise ValueError("Invalid dataset status.")

    dataset = get_dataset(
        session,
        dataset_id,
        user_id,
    )

    if dataset is None:
        raise ValueError("Dataset was not found.")

    return dataset_repository.update_dataset_status(
        session,
        dataset_id,
        user_id,
        status,
    )


# ==================================================
# DELETE DATASET
# ==================================================

def delete_dataset(
    session,
    dataset_id,
    user_id,
    delete_file=False,
):
    """
    Delete a dataset database record.

    Physical file deletion is optional.

    The database transaction must be committed before
    the physical file is permanently deleted.
    """

    dataset = get_dataset(
        session,
        dataset_id,
        user_id,
    )

    if dataset is None:
        return False

    file_path = Path(dataset.file_path)

    # Ensure the file is inside the JAK storage directory.
    storage_root = DATASETS_DIR.resolve()

    try:
        resolved_path = file_path.resolve()

        resolved_path.relative_to(storage_root)

    except (ValueError, OSError):
        raise ValueError(
            "Dataset file is outside the permitted storage directory."
        )

    deleted = dataset_repository.delete_dataset(
        session,
        dataset_id,
        user_id,
    )

    if not deleted:
        return False

    # Return the file path for a service layer to delete
    # only after the database transaction commits.
    if delete_file:
        return {
            "deleted": True,
            "file_to_delete_after_commit": str(resolved_path),
        }

    return True


# ==================================================
# DATASET STATISTICS
# ==================================================

def get_dataset_statistics(
    session,
    user_id,
):
    """Retrieve dataset statistics for a user."""

    if not user_id:
        return {
            "total_datasets": 0,
            "total_rows": 0,
            "total_columns": 0,
        }

    return dataset_repository.get_dataset_statistics(
        session,
        user_id,
    )


# ==================================================
# COUNT DATASETS
# ==================================================

def count_datasets(
    session,
    user_id,
):
    """Count datasets belonging to a user."""

    if not user_id:
        return 0

    return dataset_repository.count_user_datasets(
        session,
        user_id,
    )