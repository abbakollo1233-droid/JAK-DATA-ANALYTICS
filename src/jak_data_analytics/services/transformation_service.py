"""
JAK Data Analytics
Data Transformation Service

Provides reusable dataset transformation functionality.

Features:
- Calculated columns
- Mathematical operations
- Column renaming
- Column removal
- Sorting
- Filtering
- Grouping and aggregation
- Dataset merging
- Dataset concatenation
- Text transformations
- Date transformations

Original datasets are never modified.
"""

import operator
import pandas as pd
import numpy as np


# ==================================================
# VALIDATE DATAFRAME
# ==================================================

def validate_dataframe(data):
    """Validate input DataFrame."""

    if not isinstance(data, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    if data.empty:
        raise ValueError("The dataset is empty.")

    return True


# ==================================================
# CREATE CALCULATED COLUMN
# ==================================================

def create_calculated_column(
    data,
    new_column,
    column_a,
    column_b=None,
    operation="add",
    constant=None,
):
    """
    Create a calculated column.

    Supported operations:
    - add
    - subtract
    - multiply
    - divide
    - modulo
    - power
    """

    validate_dataframe(data)

    new_column = (new_column or "").strip()

    if not new_column:
        raise ValueError("New column name is required.")

    if column_a not in data.columns:
        raise ValueError(f"Unknown column: {column_a}")

    operations = {
        "add": operator.add,
        "subtract": operator.sub,
        "multiply": operator.mul,
        "divide": operator.truediv,
        "modulo": operator.mod,
        "power": operator.pow,
    }

    if operation not in operations:
        raise ValueError("Unsupported mathematical operation.")

    cleaned = data.copy()

    left = cleaned[column_a]

    if column_b is not None:

        if column_b not in cleaned.columns:
            raise ValueError(
                f"Unknown column: {column_b}"
            )

        right = cleaned[column_b]

    else:

        if constant is None:
            raise ValueError(
                "Provide a second column or a constant."
            )

        right = constant

    if operation in ["divide", "modulo"]:

        if isinstance(right, (int, float)) and right == 0:
            raise ValueError("Division by zero is not allowed.")

        if isinstance(right, pd.Series) and (right == 0).any():
            raise ValueError(
                "The second column contains zero values."
            )

    cleaned[new_column] = operations[operation](
        left,
        right
    )

    return cleaned


# ==================================================
# RENAME COLUMNS
# ==================================================

def rename_columns(
    data,
    rename_mapping,
):
    """Rename one or more columns."""

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

    new_names = [
        rename_mapping.get(column, column)
        for column in data.columns
    ]

    if len(new_names) != len(set(new_names)):
        raise ValueError(
            "Renaming would create duplicate column names."
        )

    return data.rename(
        columns=rename_mapping
    ).copy()


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
# SORT DATASET
# ==================================================

def sort_dataset(
    data,
    column,
    ascending=True,
):
    """Sort dataset using a selected column."""

    validate_dataframe(data)

    if column not in data.columns:
        raise ValueError(
            f"Unknown column: {column}"
        )

    return data.sort_values(
        by=column,
        ascending=ascending,
        na_position="last"
    ).reset_index(drop=True)


# ==================================================
# FILTER DATASET
# ==================================================

def filter_dataset(
    data,
    column,
    operator_name,
    value,
):
    """
    Filter rows using a comparison operation.

    Supported operators:
    - equal
    - not_equal
    - greater_than
    - greater_equal
    - less_than
    - less_equal
    - contains
    - not_contains
    - starts_with
    - ends_with
    - is_null
    - not_null
    """

    validate_dataframe(data)

    if column not in data.columns:
        raise ValueError(
            f"Unknown column: {column}"
        )

    series = data[column]

    if operator_name == "equal":
        mask = series == value

    elif operator_name == "not_equal":
        mask = series != value

    elif operator_name == "greater_than":
        mask = series > value

    elif operator_name == "greater_equal":
        mask = series >= value

    elif operator_name == "less_than":
        mask = series < value

    elif operator_name == "less_equal":
        mask = series <= value

    elif operator_name == "contains":
        mask = series.astype("string").str.contains(
            str(value),
            case=False,
            na=False,
            regex=False
        )

    elif operator_name == "not_contains":
        mask = ~series.astype("string").str.contains(
            str(value),
            case=False,
            na=False,
            regex=False
        )

    elif operator_name == "starts_with":
        mask = series.astype("string").str.startswith(
            str(value),
            na=False
        )

    elif operator_name == "ends_with":
        mask = series.astype("string").str.endswith(
            str(value),
            na=False
        )

    elif operator_name == "is_null":
        mask = series.isna()

    elif operator_name == "not_null":
        mask = series.notna()

    else:
        raise ValueError(
            "Unsupported filter operator."
        )

    return data.loc[mask].copy()


# ==================================================
# GROUP AND AGGREGATE
# ==================================================

def group_and_aggregate(
    data,
    group_columns,
    aggregation_columns,
    aggregation="sum",
):
    """
    Group data and calculate aggregate values.

    Supported aggregations:
    - sum
    - mean
    - median
    - min
    - max
    - count
    - std
    """

    validate_dataframe(data)

    if isinstance(group_columns, str):
        group_columns = [group_columns]

    if isinstance(aggregation_columns, str):
        aggregation_columns = [aggregation_columns]

    missing = [
        column
        for column in group_columns + aggregation_columns
        if column not in data.columns
    ]

    if missing:
        raise ValueError(
            f"Unknown columns: {missing}"
        )

    allowed = [
        "sum",
        "mean",
        "median",
        "min",
        "max",
        "count",
        "std",
    ]

    if aggregation not in allowed:
        raise ValueError(
            "Unsupported aggregation method."
        )

    grouped = data.groupby(
        group_columns,
        dropna=False
    )[aggregation_columns]

    result = getattr(grouped, aggregation)()

    return result.reset_index()


# ==================================================
# MERGE DATASETS
# ==================================================

def merge_datasets(
    left_data,
    right_data,
    on,
    how="inner",
    suffixes=("_left", "_right"),
):
    """
    Merge two datasets using common columns.

    Supported join types:
    - inner
    - left
    - right
    - outer
    """

    validate_dataframe(left_data)
    validate_dataframe(right_data)

    if isinstance(on, str):
        on = [on]

    if not on:
        raise ValueError(
            "At least one merge column is required."
        )

    if not set(on).issubset(left_data.columns):
        raise ValueError(
            "Merge columns are missing from the left dataset."
        )

    if not set(on).issubset(right_data.columns):
        raise ValueError(
            "Merge columns are missing from the right dataset."
        )

    if how not in ["inner", "left", "right", "outer"]:
        raise ValueError("Unsupported merge type.")

    return pd.merge(
        left_data,
        right_data,
        on=on,
        how=how,
        suffixes=suffixes,
    )


# ==================================================
# CONCATENATE DATASETS
# ==================================================

def concatenate_datasets(
    datasets,
    axis=0,
    ignore_index=True,
):
    """Combine multiple datasets vertically or horizontally."""

    if not datasets:
        raise ValueError("At least one dataset is required.")

    for dataset in datasets:
        validate_dataframe(dataset)

    if axis not in [0, 1]:
        raise ValueError("Axis must be 0 or 1.")

    return pd.concat(
        datasets,
        axis=axis,
        ignore_index=ignore_index
    )


# ==================================================
# TEXT TRANSFORMATION
# ==================================================

def transform_text_column(
    data,
    column,
    operation="lower",
):
    """
    Transform text values.

    Operations:
    - lower
    - upper
    - title
    - strip
    - remove_spaces
    """

    validate_dataframe(data)

    if column not in data.columns:
        raise ValueError(
            f"Unknown column: {column}"
        )

    if operation not in [
        "lower",
        "upper",
        "title",
        "strip",
        "remove_spaces",
    ]:
        raise ValueError(
            "Unsupported text transformation."
        )

    cleaned = data.copy()

    series = cleaned[column].astype("string")

    if operation == "lower":
        series = series.str.lower()

    elif operation == "upper":
        series = series.str.upper()

    elif operation == "title":
        series = series.str.title()

    elif operation == "strip":
        series = series.str.strip()

    elif operation == "remove_spaces":
        series = series.str.replace(
            r"\s+",
            "",
            regex=True
        )

    cleaned[column] = series

    return cleaned


# ==================================================
# DATE TRANSFORMATION
# ==================================================

def transform_date_column(
    data,
    column,
    operation="year",
):
    """
    Extract date components.

    Supported operations:
    - year
    - month
    - day
    - day_name
    - quarter
    - weekday
    """

    validate_dataframe(data)

    if column not in data.columns:
        raise ValueError(
            f"Unknown column: {column}"
        )

    allowed = [
        "year",
        "month",
        "day",
        "day_name",
        "quarter",
        "weekday",
    ]

    if operation not in allowed:
        raise ValueError(
            "Unsupported date transformation."
        )

    cleaned = data.copy()

    dates = pd.to_datetime(
        cleaned[column],
        errors="coerce"
    )

    new_column = f"{column}_{operation}"

    if operation == "year":
        values = dates.dt.year

    elif operation == "month":
        values = dates.dt.month

    elif operation == "day":
        values = dates.dt.day

    elif operation == "day_name":
        values = dates.dt.day_name()

    elif operation == "quarter":
        values = dates.dt.quarter

    elif operation == "weekday":
        values = dates.dt.weekday

    cleaned[new_column] = values

    return cleaned


# ==================================================
# COMPLETE TRANSFORMATION SUMMARY
# ==================================================

def get_transformation_summary(
    original_data,
    transformed_data,
):
    """Compare original and transformed datasets."""

    validate_dataframe(original_data)
    validate_dataframe(transformed_data)

    return {
        "original_rows": len(original_data),
        "transformed_rows": len(transformed_data),
        "original_columns": len(original_data.columns),
        "transformed_columns": len(transformed_data.columns),
        "rows_added": (
            len(transformed_data)
            - len(original_data)
        ),
        "columns_added": (
            len(transformed_data.columns)
            - len(original_data.columns)
        ),
        "original_memory_mb": round(
            original_data.memory_usage(deep=True).sum()
            / (1024 * 1024),
            2
        ),
        "transformed_memory_mb": round(
            transformed_data.memory_usage(deep=True).sum()
            / (1024 * 1024),
            2
        ),
    }