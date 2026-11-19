"""
JAK Data Analytics
Data Cleaning Service

Provides reusable dataset cleaning functionality.

Features:
- Missing value detection
- Missing value treatment
- Duplicate removal
- Text cleaning
- Data type conversion
- Outlier treatment
- Column removal
- Column renaming
- Cleaning summaries

Original datasets are never modified.
All cleaning operations return a new DataFrame.
"""

import pandas as pd
import numpy as np


# ==================================================
# VALIDATE DATAFRAME
# ==================================================

def validate_dataframe(data):
    """Validate the input dataset."""

    if not isinstance(data, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    if data.empty:
        raise ValueError("The dataset is empty.")

    return True


# ==================================================
# GET CLEANING SUMMARY
# ==================================================

def get_cleaning_summary(data):
    """Generate a summary of dataset quality issues."""

    validate_dataframe(data)

    return {
        "total_rows": len(data),
        "total_columns": len(data.columns),
        "missing_values": int(
            data.isna().sum().sum()
        ),
        "duplicate_rows": int(
            data.duplicated().sum()
        ),
        "columns_with_missing_values": int(
            data.isna().any().sum()
        ),
        "constant_columns": int(
            (data.nunique(dropna=True) <= 1).sum()
        ),
    }


# ==================================================
# HANDLE MISSING VALUES
# ==================================================

def handle_missing_values(
    data,
    strategy="mean",
    columns=None,
    fill_value=None,
):
    """
    Handle missing values.

    Strategies:
    - drop_rows
    - drop_columns
    - mean
    - median
    - mode
    - constant
    - forward_fill
    - backward_fill
    """

    validate_dataframe(data)

    cleaned = data.copy()

    selected_columns = (
        columns if columns is not None
        else cleaned.columns.tolist()
    )

    missing_columns = [
        column
        for column in selected_columns
        if column not in cleaned.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Unknown columns: {missing_columns}"
        )

    if strategy == "drop_rows":

        return cleaned.dropna(
            subset=selected_columns
        ).copy()

    if strategy == "drop_columns":

        columns_to_drop = [
            column
            for column in selected_columns
            if cleaned[column].isna().any()
        ]

        return cleaned.drop(
            columns=columns_to_drop
        ).copy()

    if strategy == "forward_fill":

        cleaned[selected_columns] = (
            cleaned[selected_columns].ffill()
        )

        return cleaned

    if strategy == "backward_fill":

        cleaned[selected_columns] = (
            cleaned[selected_columns].bfill()
        )

        return cleaned

    for column in selected_columns:

        series = cleaned[column]

        if not series.isna().any():
            continue

        if strategy == "mean":

            if pd.api.types.is_numeric_dtype(series):
                value = series.mean()
            else:
                continue

        elif strategy == "median":

            if pd.api.types.is_numeric_dtype(series):
                value = series.median()
            else:
                continue

        elif strategy == "mode":

            modes = series.mode(dropna=True)

            if modes.empty:
                continue

            value = modes.iloc[0]

        elif strategy == "constant":

            if fill_value is None:
                raise ValueError(
                    "A fill value is required for constant strategy."
                )

            value = fill_value

        else:
            raise ValueError(
                f"Unsupported missing value strategy: {strategy}"
            )

        if pd.notna(value):
            cleaned[column] = series.fillna(value)

    return cleaned


# ==================================================
# REMOVE DUPLICATES
# ==================================================

def remove_duplicates(
    data,
    subset=None,
    keep="first",
):
    """Remove duplicate rows."""

    validate_dataframe(data)

    if keep not in ["first", "last", False]:
        raise ValueError("Invalid duplicate retention option.")

    if subset is not None:

        missing_columns = [
            column
            for column in subset
            if column not in data.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Unknown columns: {missing_columns}"
            )

    return data.drop_duplicates(
        subset=subset,
        keep=keep
    ).copy()


# ==================================================
# CLEAN TEXT COLUMNS
# ==================================================

def clean_text_columns(
    data,
    columns=None,
    strip_whitespace=True,
    remove_extra_spaces=True,
    case="none",
):
    """
    Clean text columns.

    Case options:
    - none
    - lower
    - upper
    - title
    """

    validate_dataframe(data)

    cleaned = data.copy()

    if case not in [
        "none",
        "lower",
        "upper",
        "title",
    ]:
        raise ValueError("Invalid text case option.")

    selected_columns = (
        columns if columns is not None
        else cleaned.select_dtypes(
            include=["object", "string"]
        ).columns.tolist()
    )

    for column in selected_columns:

        if column not in cleaned.columns:
            raise ValueError(
                f"Unknown column: {column}"
            )

        if not (
            pd.api.types.is_object_dtype(cleaned[column])
            or pd.api.types.is_string_dtype(cleaned[column])
        ):
            continue

        series = cleaned[column].astype("string")

        if strip_whitespace:
            series = series.str.strip()

        if remove_extra_spaces:
            series = series.str.replace(
                r"\s+",
                " ",
                regex=True
            )

        if case == "lower":
            series = series.str.lower()

        elif case == "upper":
            series = series.str.upper()

        elif case == "title":
            series = series.str.title()

        cleaned[column] = series

    return cleaned


# ==================================================
# CONVERT DATA TYPES
# ==================================================

def convert_column_type(
    data,
    column,
    target_type,
    errors="raise",
):
    """
    Convert a column to another data type.

    Supported types:
    - integer
    - float
    - string
    - category
    - boolean
    - datetime
    """

    validate_dataframe(data)

    if column not in data.columns:
        raise ValueError(
            f"Unknown column: {column}"
        )

    if errors not in ["raise", "coerce"]:
        raise ValueError(
            "Errors must be 'raise' or 'coerce'."
        )

    cleaned = data.copy()

    series = cleaned[column]

    if target_type == "integer":

        if errors == "coerce":
            cleaned[column] = pd.to_numeric(
                series,
                errors="coerce"
            ).round().astype("Int64")
        else:
            numeric = pd.to_numeric(
                series,
                errors="raise"
            )

            if numeric.dropna().mod(1).ne(0).any():
                raise ValueError(
                    "Column contains non-integer values."
                )

            cleaned[column] = numeric.astype("Int64")

    elif target_type == "float":

        cleaned[column] = pd.to_numeric(
            series,
            errors=errors
        )

    elif target_type == "string":

        cleaned[column] = series.astype("string")

    elif target_type == "category":

        cleaned[column] = series.astype("category")

    elif target_type == "boolean":

        if errors == "coerce":

            mapping = {
                "true": True,
                "false": False,
                "1": True,
                "0": False,
                "yes": True,
                "no": False,
            }

            cleaned[column] = (
                series.astype("string")
                .str.strip()
                .str.lower()
                .map(mapping)
                .astype("boolean")
            )

        else:

            mapping = {
                "true": True,
                "false": False,
                "1": True,
                "0": False,
                "yes": True,
                "no": False,
            }

            normalized = (
                series.astype("string")
                .str.strip()
                .str.lower()
            )

            unknown = normalized.notna() & ~normalized.isin(
                mapping.keys()
            )

            if unknown.any():
                raise ValueError(
                    "Column contains unsupported boolean values."
                )

            cleaned[column] = (
                normalized.map(mapping).astype("boolean")
            )

    elif target_type == "datetime":

        cleaned[column] = pd.to_datetime(
            series,
            errors=errors
        )

    else:
        raise ValueError(
            f"Unsupported target type: {target_type}"
        )

    return cleaned


# ==================================================
# REMOVE OUTLIERS
# ==================================================

def remove_outliers_iqr(
    data,
    columns=None,
    multiplier=1.5,
):
    """Remove rows containing IQR outliers in selected columns."""

    validate_dataframe(data)

    if multiplier <= 0:
        raise ValueError(
            "IQR multiplier must be greater than zero."
        )

    cleaned = data.copy()

    if columns is None:
        columns = cleaned.select_dtypes(
            include=np.number
        ).columns.tolist()

    for column in columns:

        if column not in cleaned.columns:
            raise ValueError(
                f"Unknown column: {column}"
            )

        if not pd.api.types.is_numeric_dtype(
            cleaned[column]
        ):
            continue

        series = cleaned[column].dropna()

        if series.empty:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)

        iqr = q3 - q1

        lower = q1 - multiplier * iqr
        upper = q3 + multiplier * iqr

        mask = (
            cleaned[column].isna()
            | (
                cleaned[column].between(
                    lower,
                    upper,
                    inclusive="both"
                )
            )
        )

        cleaned = cleaned.loc[mask].copy()

    return cleaned


# ==================================================
# CAP OUTLIERS
# ==================================================

def cap_outliers_iqr(
    data,
    columns=None,
    multiplier=1.5,
):
    """Cap numerical outliers at IQR boundaries."""

    validate_dataframe(data)

    if multiplier <= 0:
        raise ValueError(
            "IQR multiplier must be greater than zero."
        )

    cleaned = data.copy()

    if columns is None:
        columns = cleaned.select_dtypes(
            include=np.number
        ).columns.tolist()

    for column in columns:

        if column not in cleaned.columns:
            raise ValueError(
                f"Unknown column: {column}"
            )

        if not pd.api.types.is_numeric_dtype(
            cleaned[column]
        ):
            continue

        series = cleaned[column].dropna()

        if series.empty:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)

        iqr = q3 - q1

        lower = q1 - multiplier * iqr
        upper = q3 + multiplier * iqr

        cleaned[column] = cleaned[column].clip(
            lower=lower,
            upper=upper
        )

    return cleaned


# ==================================================
# REMOVE COLUMNS
# ==================================================

def remove_columns(
    data,
    columns,
):
    """Remove selected columns."""

    validate_dataframe(data)

    if isinstance(columns, str):
        columns = [columns]

    missing = [
        column
        for column in columns
        if column not in data.columns
    ]

    if missing:
        raise ValueError(
            f"Unknown columns: {missing}"
        )

    return data.drop(
        columns=columns
    ).copy()


# ==================================================
# RENAME COLUMNS
# ==================================================

def rename_columns(
    data,
    rename_mapping,
):
    """Rename dataset columns."""

    validate_dataframe(data)

    if not isinstance(rename_mapping, dict):
        raise TypeError(
            "Rename mapping must be a dictionary."
        )

    missing = [
        column
        for column in rename_mapping
        if column not in data.columns
    ]

    if missing:
        raise ValueError(
            f"Unknown columns: {missing}"
        )

    return data.rename(
        columns=rename_mapping
    ).copy()


# ==================================================
# COMPLETE CLEANING REPORT
# ==================================================

def generate_cleaning_report(
    original_data,
    cleaned_data,
):
    """Compare original and cleaned datasets."""

    validate_dataframe(original_data)
    validate_dataframe(cleaned_data)

    original = get_cleaning_summary(original_data)
    cleaned = get_cleaning_summary(cleaned_data)

    return {
        "original": original,
        "cleaned": cleaned,
        "rows_removed": (
            original["total_rows"]
            - cleaned["total_rows"]
        ),
        "columns_removed": (
            original["total_columns"]
            - cleaned["total_columns"]
        ),
        "missing_values_removed": (
            original["missing_values"]
            - cleaned["missing_values"]
        ),
        "duplicates_removed": (
            original["duplicate_rows"]
            - cleaned["duplicate_rows"]
        ),
    }