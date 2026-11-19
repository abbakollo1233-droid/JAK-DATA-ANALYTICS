"""
JAK Data Analytics
Data Export Service

Exports datasets into common file formats:
- CSV
- Excel
- JSON
- Parquet

Also provides:
- Export validation
- Excel sheet selection
- CSV delimiter configuration
- JSON orientation settings
- Export metadata
- File size information

This service is independent of Streamlit.
"""

from pathlib import Path
from datetime import datetime, timezone
import json

import pandas as pd


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

SUPPORTED_EXPORT_FORMATS = {
    "csv",
    "xlsx",
    "json",
    "parquet",
}

DEFAULT_ENCODING = "utf-8-sig"


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_export_data(data):
    """
    Validate a DataFrame before exporting.
    """

    if not isinstance(data, pd.DataFrame):
        raise ValueError(
            "Export data must be a Pandas DataFrame."
        )

    if data.empty:
        raise ValueError(
            "Cannot export an empty dataset."
        )

    if data.columns.duplicated().any():
        raise ValueError(
            "Dataset contains duplicate column names."
        )

    return True


def validate_export_format(file_format):
    """
    Validate the requested export format.
    """

    file_format = str(file_format).lower().strip()

    if file_format.startswith("."):
        file_format = file_format[1:]

    if file_format not in SUPPORTED_EXPORT_FORMATS:
        raise ValueError(
            f"Unsupported export format: {file_format}. "
            f"Supported formats: "
            f"{', '.join(sorted(SUPPORTED_EXPORT_FORMATS))}"
        )

    return file_format


def validate_output_path(output_path, file_format):
    """
    Validate the output path and extension.
    """

    path = Path(output_path)

    if path.suffix.lower() != f".{file_format}":
        path = path.with_suffix(f".{file_format}")

    if path.exists() and path.is_dir():
        raise ValueError(
            "Output path points to a directory."
        )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return path


# ---------------------------------------------------------
# FILE NAME GENERATION
# ---------------------------------------------------------

def generate_export_filename(
    dataset_name="dataset",
    file_format="csv",
):
    """
    Generate a safe export filename.
    """

    file_format = validate_export_format(file_format)

    safe_name = "".join(
        character if character.isalnum() or character in "-_"
        else "_"
        for character in str(dataset_name).strip()
    )

    safe_name = safe_name.strip("_") or "dataset"

    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%d_%H%M%S")

    return f"{safe_name}_{timestamp}.{file_format}"


# ---------------------------------------------------------
# CSV EXPORT
# ---------------------------------------------------------

def export_csv(
    data,
    output_path,
    encoding=DEFAULT_ENCODING,
    delimiter=",",
    include_index=False,
):
    """
    Export a DataFrame to CSV.
    """

    validate_export_data(data)

    path = validate_output_path(
        output_path,
        "csv",
    )

    if len(delimiter) != 1:
        raise ValueError(
            "CSV delimiter must be exactly one character."
        )

    data.to_csv(
        path,
        index=include_index,
        encoding=encoding,
        sep=delimiter,
    )

    return path


# ---------------------------------------------------------
# EXCEL EXPORT
# ---------------------------------------------------------

def export_excel(
    data,
    output_path,
    sheet_name="Data",
    include_index=False,
):
    """
    Export a DataFrame to an Excel workbook.
    """

    validate_export_data(data)

    path = validate_output_path(
        output_path,
        "xlsx",
    )

    sheet_name = str(sheet_name).strip()

    if not sheet_name:
        sheet_name = "Data"

    if len(sheet_name) > 31:
        raise ValueError(
            "Excel sheet names cannot exceed 31 characters."
        )

    invalid_characters = set(r"[]:*?/\\")
    
    if any(character in invalid_characters for character in sheet_name):
        raise ValueError(
            "Excel sheet name contains invalid characters."
        )

    data.to_excel(
        path,
        index=include_index,
        sheet_name=sheet_name,
        engine="openpyxl",
    )

    return path


# ---------------------------------------------------------
# JSON EXPORT
# ---------------------------------------------------------

def export_json(
    data,
    output_path,
    orient="records",
    indent=4,
    date_format="iso",
):
    """
    Export a DataFrame to JSON.
    """

    validate_export_data(data)

    path = validate_output_path(
        output_path,
        "json",
    )

    supported_orientations = {
        "split",
        "records",
        "index",
        "columns",
        "values",
        "table",
    }

    if orient not in supported_orientations:
        raise ValueError(
            "Unsupported JSON orientation."
        )

    json_data = data.to_json(
        orient=orient,
        indent=indent,
        date_format=date_format,
        force_ascii=False,
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(json_data)

    return path


# ---------------------------------------------------------
# PARQUET EXPORT
# ---------------------------------------------------------

def export_parquet(
    data,
    output_path,
    compression="snappy",
):
    """
    Export a DataFrame to Parquet.

    Requires pyarrow or fastparquet.
    """

    validate_export_data(data)

    path = validate_output_path(
        output_path,
        "parquet",
    )

    supported_compression = {
        "snappy",
        "gzip",
        "brotli",
        "lz4",
        "zstd",
        "none",
    }

    if compression not in supported_compression:
        raise ValueError(
            "Unsupported Parquet compression."
        )

    selected_compression = (
        None if compression == "none"
        else compression
    )

    data.to_parquet(
        path,
        index=False,
        compression=selected_compression,
    )

    return path


# ---------------------------------------------------------
# MAIN EXPORT FUNCTION
# ---------------------------------------------------------

def export_dataset(
    data,
    output_path,
    file_format=None,
    **options,
):
    """
    Export a dataset using the selected format.

    If file_format is omitted, the file extension
    is used to determine the format.
    """

    validate_export_data(data)

    path = Path(output_path)

    if file_format is None:

        if not path.suffix:
            raise ValueError(
                "Specify an export format or file extension."
            )

        file_format = path.suffix

    file_format = validate_export_format(
        file_format
    )

    if file_format == "csv":

        result_path = export_csv(
            data,
            path,
            **options,
        )

    elif file_format == "xlsx":

        result_path = export_excel(
            data,
            path,
            **options,
        )

    elif file_format == "json":

        result_path = export_json(
            data,
            path,
            **options,
        )

    elif file_format == "parquet":

        result_path = export_parquet(
            data,
            path,
            **options,
        )

    else:
        raise ValueError(
            "Unsupported export format."
        )

    return {
        "success": True,
        "file_path": str(result_path),
        "file_name": result_path.name,
        "file_format": file_format,
        "file_size_bytes": result_path.stat().st_size,
        "rows_exported": len(data),
        "columns_exported": len(data.columns),
        "exported_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }


# ---------------------------------------------------------
# EXPORT TO MEMORY
# ---------------------------------------------------------

def export_dataset_to_memory(
    data,
    file_format="csv",
    **options,
):
    """
    Export a dataset into memory.

    Useful for downloads from Streamlit without
    creating a permanent file.
    """

    from io import BytesIO, StringIO

    validate_export_data(data)

    file_format = validate_export_format(
        file_format
    )

    if file_format == "csv":

        output = StringIO()

        data.to_csv(
            output,
            index=options.get("include_index", False),
            sep=options.get("delimiter", ","),
        )

        return output.getvalue().encode(
            options.get("encoding", DEFAULT_ENCODING)
        )

    if file_format == "xlsx":

        output = BytesIO()

        sheet_name = options.get(
            "sheet_name",
            "Data",
        )

        if not sheet_name or len(sheet_name) > 31:
            raise ValueError(
                "Excel sheet name must contain 1–31 characters."
            )

        if any(character in r"[]:*?/\\" for character in sheet_name):
            raise ValueError(
                "Excel sheet name contains invalid characters."
            )

        with pd.ExcelWriter(
            output,
            engine="openpyxl",
        ) as writer:

            data.to_excel(
                writer,
                index=options.get("include_index", False),
                sheet_name=sheet_name,
            )

        return output.getvalue()

    if file_format == "json":

        return data.to_json(
            orient=options.get("orient", "records"),
            indent=options.get("indent", 4),
            date_format=options.get("date_format", "iso"),
            force_ascii=False,
        ).encode("utf-8")

    if file_format == "parquet":

        output = BytesIO()

        compression = options.get(
            "compression",
            "snappy",
        )

        if compression == "none":
            compression = None

        data.to_parquet(
            output,
            index=False,
            compression=compression,
        )

        return output.getvalue()

    raise ValueError(
        "Unsupported export format."
    )


# ---------------------------------------------------------
# EXPORT INFORMATION
# ---------------------------------------------------------

def get_export_information(file_path):
    """
    Retrieve information about an exported file.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            "Exported file does not exist."
        )

    if not path.is_file():
        raise ValueError(
            "The supplied path is not a file."
        )

    size_bytes = path.stat().st_size

    return {
        "file_name": path.name,
        "file_path": str(path.resolve()),
        "file_format": path.suffix.lower().lstrip("."),
        "file_size_bytes": size_bytes,
        "file_size_kb": round(
            size_bytes / 1024,
            2,
        ),
        "file_size_mb": round(
            size_bytes / (1024 * 1024),
            2,
        ),
        "created_at": datetime.fromtimestamp(
            path.stat().st_ctime,
            timezone.utc,
        ).isoformat(),
        "modified_at": datetime.fromtimestamp(
            path.stat().st_mtime,
            timezone.utc,
        ).isoformat(),
    }


# ---------------------------------------------------------
# EXPORT SUMMARY
# ---------------------------------------------------------

def generate_export_summary(
    data,
    export_result,
):
    """
    Generate a summary of an export operation.
    """

    validate_export_data(data)

    if not isinstance(export_result, dict):
        raise ValueError(
            "A valid export result is required."
        )

    return {
        "dataset_rows": len(data),
        "dataset_columns": len(data.columns),
        "export_successful": export_result.get(
            "success",
            False,
        ),
        "file_name": export_result.get(
            "file_name",
        ),
        "file_format": export_result.get(
            "file_format",
        ),
        "file_size_bytes": export_result.get(
            "file_size_bytes",
        ),
        "exported_at": export_result.get(
            "exported_at",
        ),
    }
