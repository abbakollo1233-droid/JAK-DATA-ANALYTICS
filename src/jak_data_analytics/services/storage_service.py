"""
JAK Data Analytics
Dataset Storage Service

Handles physical dataset storage:
- Save uploaded files
- Generate unique filenames
- Retrieve stored files
- Calculate file hashes
- Check storage information
- Delete stored files safely

This service does not depend on Streamlit.
"""

import hashlib
import shutil
import uuid

from pathlib import Path
from datetime import datetime, timezone

from ..config.settings import (
    STORAGE_DIR,
    DATASETS_DIR,
    REPORTS_DIR,
    MODELS_DIR,
)

from ..config.constants import (
    SUPPORTED_FILE_FORMATS,
    MAX_UPLOAD_SIZE_MB,
)


# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------

MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

ALLOWED_EXTENSIONS = {
    extension.lower()
    for extension in SUPPORTED_FILE_FORMATS
}


# ---------------------------------------------------------
# DIRECTORY MANAGEMENT
# ---------------------------------------------------------

def ensure_storage_directories():
    """
    Create required storage directories if they do not exist.
    """

    directories = [
        STORAGE_DIR,
        DATASETS_DIR,
        REPORTS_DIR,
        MODELS_DIR,
    ]

    for directory in directories:
        Path(directory).mkdir(
            parents=True,
            exist_ok=True,
        )

    return True


def get_storage_directories():
    """
    Return the configured storage directories.
    """

    ensure_storage_directories()

    return {
        "root": str(STORAGE_DIR),
        "datasets": str(DATASETS_DIR),
        "reports": str(REPORTS_DIR),
        "models": str(MODELS_DIR),
    }


# ---------------------------------------------------------
# FILE VALIDATION
# ---------------------------------------------------------

def validate_storage_file(file_path):
    """
    Validate a file before storing it.
    """

    path = Path(file_path)

    if not path.exists():
        return False, "File does not exist."

    if not path.is_file():
        return False, "The selected path is not a file."

    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return False, "Unsupported dataset file format."

    try:
        size = path.stat().st_size
    except OSError:
        return False, "Unable to read file information."

    if size == 0:
        return False, "The selected file is empty."

    if size > MAX_UPLOAD_SIZE_BYTES:
        return False, (
            f"File exceeds the maximum size of "
            f"{MAX_UPLOAD_SIZE_MB} MB."
        )

    return True, None


# ---------------------------------------------------------
# SAFE FILENAME GENERATION
# ---------------------------------------------------------

def sanitize_filename(filename):
    """
    Remove unsafe characters from a filename.
    """

    filename = Path(str(filename)).name

    stem = Path(filename).stem
    extension = Path(filename).suffix.lower()

    safe_stem = "".join(
        character
        if character.isalnum() or character in {"-", "_"}
        else "_"
        for character in stem
    )

    safe_stem = safe_stem.strip("._-")

    if not safe_stem:
        safe_stem = "dataset"

    return f"{safe_stem}{extension}"


def generate_storage_filename(original_filename):
    """
    Generate a unique filename while preserving its extension.
    """

    safe_name = sanitize_filename(original_filename)

    extension = Path(safe_name).suffix.lower()

    unique_id = uuid.uuid4().hex

    return f"{unique_id}{extension}"


# ---------------------------------------------------------
# FILE HASH
# ---------------------------------------------------------

def calculate_file_hash(file_path):
    """
    Calculate the SHA-256 hash of a file.
    """

    path = Path(file_path)

    if not path.exists() or not path.is_file():
        raise FileNotFoundError("File not found.")

    sha256 = hashlib.sha256()

    with open(path, "rb") as file:

        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            sha256.update(chunk)

    return sha256.hexdigest()


# ---------------------------------------------------------
# STORAGE PATH
# ---------------------------------------------------------

def get_user_storage_directory(user_id):
    """
    Get or create a user's dataset storage directory.
    """

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise ValueError("Invalid user ID.")

    if user_id <= 0:
        raise ValueError("User ID must be positive.")

    ensure_storage_directories()

    directory = DATASETS_DIR / f"user_{user_id}"

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return directory


def get_dataset_storage_path(user_id, filename):
    """
    Generate a safe storage path for a user's dataset.
    """

    directory = get_user_storage_directory(user_id)

    stored_filename = generate_storage_filename(filename)

    return directory / stored_filename


# ---------------------------------------------------------
# SAVE DATASET FILE
# ---------------------------------------------------------

def save_dataset_file(
    source_path,
    user_id,
    original_filename=None,
):
    """
    Copy a dataset into the user's storage directory.

    Returns:
        dict containing:
            success
            message
            file_path
            original_filename
            stored_filename
            file_size
            file_hash
    """

    source = Path(source_path)

    is_valid, error = validate_storage_file(source)

    if not is_valid:
        return {
            "success": False,
            "message": error,
            "file_path": None,
        }

    try:

        original_filename = (
            original_filename
            or source.name
        )

        destination = get_dataset_storage_path(
            user_id,
            original_filename,
        )

        shutil.copy2(
            source,
            destination,
        )

        file_size = destination.stat().st_size

        file_hash = calculate_file_hash(destination)

        return {
            "success": True,
            "message": "Dataset saved successfully.",
            "file_path": str(destination),
            "original_filename": str(original_filename),
            "stored_filename": destination.name,
            "file_size": file_size,
            "file_hash": file_hash,
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

    except Exception as error:

        return {
            "success": False,
            "message": f"Unable to save dataset: {error}",
            "file_path": None,
        }


# ---------------------------------------------------------
# RETRIEVE STORED DATASET
# ---------------------------------------------------------

def get_stored_dataset_path(user_id, stored_filename):
    """
    Retrieve a dataset path belonging to a user.

    Prevents access to files outside the user's directory.
    """

    directory = get_user_storage_directory(user_id)

    filename = Path(str(stored_filename)).name

    if filename != str(stored_filename):
        raise ValueError("Invalid stored filename.")

    path = directory / filename

    resolved_directory = directory.resolve()
    resolved_path = path.resolve()

    if not resolved_path.is_relative_to(resolved_directory):
        raise PermissionError("Invalid storage location.")

    if not resolved_path.exists():
        return None

    if not resolved_path.is_file():
        return None

    return resolved_path


def read_stored_dataset(user_id, stored_filename):
    """
    Read a stored dataset into a Pandas DataFrame.
    """

    from ..services.data_import_service import import_dataset

    path = get_stored_dataset_path(
        user_id,
        stored_filename,
    )

    if path is None:
        return {
            "success": False,
            "message": "Stored dataset was not found.",
            "dataframe": None,
        }

    return import_dataset(path)


# ---------------------------------------------------------
# FILE INFORMATION
# ---------------------------------------------------------

def get_stored_file_information(user_id, stored_filename):
    """
    Retrieve information about a stored dataset.
    """

    path = get_stored_dataset_path(
        user_id,
        stored_filename,
    )

    if path is None:
        return None

    stat = path.stat()

    return {
        "filename": path.name,
        "extension": path.suffix.lower(),
        "file_size": stat.st_size,
        "file_size_mb": round(
            stat.st_size / (1024 * 1024),
            3,
        ),
        "created_at": datetime.fromtimestamp(
            stat.st_ctime,
            timezone.utc,
        ).isoformat(),
        "modified_at": datetime.fromtimestamp(
            stat.st_mtime,
            timezone.utc,
        ).isoformat(),
        "file_hash": calculate_file_hash(path),
    }


# ---------------------------------------------------------
# DELETE STORED DATASET
# ---------------------------------------------------------

def delete_stored_dataset(user_id, stored_filename):
    """
    Delete a stored dataset belonging to a user.
    """

    try:

        path = get_stored_dataset_path(
            user_id,
            stored_filename,
        )

        if path is None:
            return {
                "success": False,
                "message": "Dataset file was not found.",
            }

        path.unlink()

        return {
            "success": True,
            "message": "Dataset file deleted successfully.",
        }

    except (ValueError, PermissionError) as error:

        return {
            "success": False,
            "message": str(error),
        }

    except OSError:

        return {
            "success": False,
            "message": "Unable to delete dataset file.",
        }


# ---------------------------------------------------------
# USER STORAGE USAGE
# ---------------------------------------------------------

def get_user_storage_usage(user_id):
    """
    Calculate the total dataset storage used by a user.
    """

    directory = get_user_storage_directory(user_id)

    total_bytes = 0
    file_count = 0

    for path in directory.iterdir():

        if path.is_file():

            total_bytes += path.stat().st_size
            file_count += 1

    return {
        "user_id": int(user_id),
        "file_count": file_count,
        "total_bytes": total_bytes,
        "total_mb": round(
            total_bytes / (1024 * 1024),
            3,
        ),
        "total_gb": round(
            total_bytes / (1024 ** 3),
            4,
        ),
    }


# ---------------------------------------------------------
# ADMIN STORAGE OVERVIEW
# ---------------------------------------------------------

def get_storage_overview():
    """
    Calculate total storage usage across configured directories.
    """

    ensure_storage_directories()

    directories = {
        "datasets": DATASETS_DIR,
        "reports": REPORTS_DIR,
        "models": MODELS_DIR,
    }

    overview = {}

    for name, directory in directories.items():

        total_bytes = 0
        file_count = 0

        for path in directory.rglob("*"):

            if path.is_file():

                total_bytes += path.stat().st_size
                file_count += 1

        overview[name] = {
            "file_count": file_count,
            "total_bytes": total_bytes,
            "total_mb": round(
                total_bytes / (1024 * 1024),
                3,
            ),
        }

    overview["total_bytes"] = sum(
        item["total_bytes"]
        for item in overview.values()
        if isinstance(item, dict)
    )

    overview["total_mb"] = round(
        overview["total_bytes"] / (1024 * 1024),
        3,
    )

    return overview
