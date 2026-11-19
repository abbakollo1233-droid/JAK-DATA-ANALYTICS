"""
JAK Data Analytics
Data Import Service

Handles importing and validating datasets from:
- CSV
- Excel
- JSON
- Parquet

This service is independent of Streamlit.
"""

import json
from pathlib import Path

import pandas as pd

from ..config.constants import (
    SUPPORTED_FILE_FORMATS,
    MAX_UPLOAD_SIZE_MB,
)


# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------

MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

SUPPORTED_EXTENSIONS = {
    extension.lower()
    for extension in SUPPORTED_FILE_FORMATS
}


# ---------------------------------------------------------
# FILE VALIDATION
# ---------------------------------------------------------

def validate_import_file(file_path):
    """
    Validate a dataset file before importing it.

    Returns:
        tuple: (is_valid, error_message)
    """

    path = Path(file_path)

    if not path.exists():
        return False, "The selected file does not exist."

    if not path.is_file():
        return False, "The selected path is not a file."

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return False, (
            f"Unsupported file format: {path.suffix}. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    try:
        file_size = path.stat().st_size
    except OSError:
        return False, "Unable to read file information."

    if file_size == 0:
        return False, "The selected file is empty."

    if file_size > MAX_UPLOAD_SIZE_BYTES:
        return False, (
            f"File exceeds the maximum allowed size "
            f"of {MAX_UPLOAD_SIZE_MB} MB."
        )

    return True, None


# ---------------------------------------------------------
# CSV IMPORT
# ---------------------------------------------------------

def import_csv(
    file_path,
    encoding="utf-8",
    delimiter=",",
):
    """
    Import a CSV dataset.
    """

    return pd.read_csv(
        file_path,
        encoding=encoding,
        sep=delimiter,
        low_memory=False,
    )


# ---------------------------------------------------------
# EXCEL IMPORT
# ---------------------------------------------------------

def import_excel(
    file_path,
    sheet_name=0,
):
    """
    Import an Excel worksheet.

    sheet_name can be:
        - Worksheet name
        - Worksheet index
        - None to import all worksheets
    """

    return pd.read_excel(
        file_path,
        sheet_name=sheet_name,
    )


# ---------------------------------------------------------
# JSON IMPORT
# ---------------------------------------------------------

def import_json(
    file_path,
    orient=None,
):
    """
    Import JSON data.

    Supports normal JSON records and JSON orientations
    supported by Pandas.
    """

    if orient:
        return pd.read_json(
            file_path,
            orient=orient,
        )

    try:
        return pd.read_json(file_path)

    except ValueError:
        with open(
            file_path,
            "r",
            encoding="utf-8",
        ) as file:

            content = json.load(file)

        return pd.json_normalize(content)


# ---------------------------------------------------------
# PARQUET IMPORT
# ---------------------------------------------------------

def import_parquet(file_path):
    """
    Import a Parquet dataset.
    """

    return pd.read_parquet(file_path)


# ---------------------------------------------------------
# AUTOMATIC FILE IMPORT
# ---------------------------------------------------------

def import_dataset(
    file_path,
    sheet_name=0,
    encoding="utf-8",
    delimiter=",",
    json_orient=None,
):
    """
    Automatically detect the file format and import it.

    Returns:
        dict containing:
            success
            message
            dataframe
            file_name
            file_type
    """

    path = Path(file_path)

    is_valid, error = validate_import_file(path)

    if not is_valid:
        return {
            "success": False,
            "message": error,
            "dataframe": None,
            "file_name": path.name,
            "file_type": path.suffix.lower(),
        }

    extension = path.suffix.lower()

    try:

        if extension == ".csv":

            dataframe = import_csv(
                path,
                encoding=encoding,
                delimiter=delimiter,
            )

        elif extension in {".xlsx", ".xls"}:

            dataframe = import_excel(
                path,
                sheet_name=sheet_name,
            )

            if isinstance(dataframe, dict):
                return {
                    "success": True,
                    "message": "Excel worksheets imported successfully.",
                    "dataframe": dataframe,
                    "file_name": path.name,
                    "file_type": extension,
                }

        elif extension == ".json":

            dataframe = import_json(
                path,
                orient=json_orient,
            )

        elif extension == ".parquet":

            dataframe = import_parquet(path)

        else:

            raise ValueError(
                "This file format is not supported."
            )

        if not isinstance(dataframe, pd.DataFrame):
            raise ValueError(
                "The imported file did not produce a valid DataFrame."
            )

        if dataframe.empty:
            raise ValueError(
                "The imported dataset contains no records."
            )

        return {
            "success": True,
            "message": "Dataset imported successfully.",
            "dataframe": dataframe,
            "file_name": path.name,
            "file_type": extension,
        }

    except Exception as error:

        return {
            "success": False,
            "message": f"Import failed: {error}",
            "dataframe": None,
            "file_name": path.name,
            "file_type": extension,
        }


# ---------------------------------------------------------
# EXCEL WORKSHEET INFORMATION
# ---------------------------------------------------------

def get_excel_sheets(file_path):
    """
    Return worksheet names from an Excel workbook.
    """

    path = Path(file_path)

    if path.suffix.lower() not in {".xlsx", ".xls"}:
        raise ValueError("The selected file is not an Excel workbook.")

    excel_file = pd.ExcelFile(path)

    return excel_file.sheet_names


# ---------------------------------------------------------
# DATASET VALIDATION
# ---------------------------------------------------------

def validate_imported_dataframe(data):
    """
    Validate an imported DataFrame.
    """

    if not isinstance(data, pd.DataFrame):
        return False, "Imported data must be a Pandas DataFrame."

    if data.empty:
        return False, "The dataset contains no records."

    if len(data.columns) == 0:
        return False, "The dataset contains no columns."

    if data.columns.duplicated().any():
        return False, "The dataset contains duplicate column names."

    if any(
        str(column).strip() == ""
        for column in data.columns
    ):
        return False, "The dataset contains empty column names."

    return True, None


# ---------------------------------------------------------
# DATASET INFORMATION
# ---------------------------------------------------------

def get_import_information(data):
    """
    Extract basic information about an imported dataset.
    """

    is_valid, error = validate_imported_dataframe(data)

    if not is_valid:
        raise ValueError(error)

    return {
        "rows": int(data.shape[0]),
        "columns": int(data.shape[1]),
        "total_cells": int(data.size),
        "missing_values": int(data.isna().sum().sum()),
        "duplicate_rows": int(data.duplicated().sum()),
        "memory_usage_bytes": int(
            data.memory_usage(deep=True).sum()
        ),
        "column_names": [
            str(column)
            for column in data.columns
        ],
        "column_types": {
            str(column): str(dtype)
            for column, dtype in data.dtypes.items()
        },
    }


# ---------------------------------------------------------
# NORMALISE COLUMN NAMES
# ---------------------------------------------------------

def normalize_column_names(data):
    """
    Clean column names while preserving the original DataFrame.

    Example:
        Employee Name -> employee_name
        Monthly Salary -> monthly_salary
    """

    if not isinstance(data, pd.DataFrame):
        raise ValueError("A valid DataFrame is required.")

    result = data.copy()

    normalized_names = []

    for column in result.columns:

        name = str(column).strip().lower()

        name = name.replace(" ", "_")

        name = "".join(
            character
            if character.isalnum() or character == "_"
            else "_"
            for character in name
        )

        while "__" in name:
            name = name.replace("__", "_")

        name = name.strip("_") or "column"

        normalized_names.append(name)

    # Ensure names remain unique after normalisation.
    unique_names = []
    used_names = {}

    for name in normalized_names:

        count = used_names.get(name, 0) + 1
        used_names[name] = count

        if count == 1:
            unique_names.append(name)
        else:
            unique_names.append(f"{name}_{count}")

    result.columns = unique_names

    return result


# ---------------------------------------------------------
# EXPORT DATASET
# ---------------------------------------------------------

def export_dataset(
    data,
    file_path,
    file_format=None,
):
    """
    Export a DataFrame to CSV, Excel, JSON, or Parquet.

    Returns:
        dict containing success and message.
    """

    if not isinstance(data, pd.DataFrame):
        return {
            "success": False,
            "message": "A valid DataFrame is required.",
        }

    if data.empty:
        return {
            "success": False,
            "message": "Cannot export an empty dataset.",
        }

    path = Path(file_path)

    extension = (
        str(file_format).lower()
        if file_format
        else path.suffix.lower().lstrip(".")
    )

    if extension.startswith("."):
        extension = extension[1:]

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:

        if extension == "csv":

            data.to_csv(
                path,
                index=False,
            )

        elif extension in {"xlsx", "excel"}:

            if path.suffix.lower() != ".xlsx":
                path = path.with_suffix(".xlsx")

            data.to_excel(
                path,
                index=False,
            )

        elif extension == "json":

            data.to_json(
                path,
                orient="records",
                indent=4,
                date_format="iso",
            )

        elif extension == "parquet":

            data.to_parquet(
                path,
                index=False,
            )

        else:

            return {
                "success": False,
                "message": "Unsupported export format.",
            }

        return {
            "success": True,
            "message": "Dataset exported successfully.",
            "file_path": str(path),
        }

    except Exception as error:

        return {
            "success": False,
            "message": f"Export failed: {error}",
        }
