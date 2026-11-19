"""
JAK Data Analytics
Dataset Comparison Service

Provides reusable dataset comparison capabilities:
- Compare dataset structures
- Compare row and column counts
- Compare column data types
- Compare numerical statistics
- Identify missing and additional columns
- Compare records between datasets
- Identify added and removed records
- Compare categorical distributions
- Generate comparison reports

This service is independent of Streamlit.
"""

import pandas as pd
import numpy as np


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_comparison_datasets(
    first,
    second,
):
    """
    Validate two datasets before comparison.
    """

    if not isinstance(first, pd.DataFrame):
        return False, "The first dataset must be a DataFrame."

    if not isinstance(second, pd.DataFrame):
        return False, "The second dataset must be a DataFrame."

    if first.empty:
        return False, "The first dataset is empty."

    if second.empty:
        return False, "The second dataset is empty."

    if first.columns.duplicated().any():
        return False, "The first dataset has duplicate column names."

    if second.columns.duplicated().any():
        return False, "The second dataset has duplicate column names."

    return True, None


# ---------------------------------------------------------
# DATASET OVERVIEW
# ---------------------------------------------------------

def get_dataset_overview(data, dataset_name="Dataset"):
    """
    Return basic information about a dataset.
    """

    if not isinstance(data, pd.DataFrame):
        raise ValueError("A valid DataFrame is required.")

    return {
        "dataset": dataset_name,
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
    }


def compare_dataset_overview(
    first,
    second,
    first_name="Dataset A",
    second_name="Dataset B",
):
    """
    Compare the general structure of two datasets.
    """

    is_valid, error = validate_comparison_datasets(
        first,
        second,
    )

    if not is_valid:
        raise ValueError(error)

    first_info = get_dataset_overview(
        first,
        first_name,
    )

    second_info = get_dataset_overview(
        second,
        second_name,
    )

    metrics = [
        "rows",
        "columns",
        "total_cells",
        "missing_values",
        "duplicate_rows",
        "memory_usage_bytes",
    ]

    records = []

    for metric in metrics:

        value_a = first_info[metric]
        value_b = second_info[metric]

        records.append({
            "Metric": metric.replace("_", " ").title(),
            first_name: value_a,
            second_name: value_b,
            "Difference": value_b - value_a,
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------
# COLUMN COMPARISON
# ---------------------------------------------------------

def compare_columns(first, second):
    """
    Identify common, missing, and additional columns.
    """

    is_valid, error = validate_comparison_datasets(
        first,
        second,
    )

    if not is_valid:
        raise ValueError(error)

    first_columns = set(first.columns)
    second_columns = set(second.columns)

    common = sorted(
        first_columns.intersection(second_columns),
        key=str,
    )

    only_first = sorted(
        first_columns - second_columns,
        key=str,
    )

    only_second = sorted(
        second_columns - first_columns,
        key=str,
    )

    return {
        "common_columns": common,
        "only_in_first": only_first,
        "only_in_second": only_second,
        "common_count": len(common),
        "only_first_count": len(only_first),
        "only_second_count": len(only_second),
    }


# ---------------------------------------------------------
# DATA TYPE COMPARISON
# ---------------------------------------------------------

def compare_column_types(first, second):
    """
    Compare data types of common columns.
    """

    comparison = compare_columns(first, second)

    records = []

    for column in comparison["common_columns"]:

        first_type = str(first[column].dtype)
        second_type = str(second[column].dtype)

        records.append({
            "Column": column,
            "First Dataset Type": first_type,
            "Second Dataset Type": second_type,
            "Types Match": first_type == second_type,
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------
# NUMERICAL STATISTICS COMPARISON
# ---------------------------------------------------------

def compare_numerical_statistics(
    first,
    second,
    columns=None,
):
    """
    Compare numerical statistics for common columns.

    Includes:
        Mean, median, minimum, maximum, standard deviation.
    """

    is_valid, error = validate_comparison_datasets(
        first,
        second,
    )

    if not is_valid:
        raise ValueError(error)

    first_numeric = set(
        first.select_dtypes(include="number").columns
    )

    second_numeric = set(
        second.select_dtypes(include="number").columns
    )

    common_numeric = sorted(
        first_numeric.intersection(second_numeric),
        key=str,
    )

    if columns is not None:

        requested = set(columns)

        common_numeric = [
            column
            for column in common_numeric
            if column in requested
        ]

    records = []

    for column in common_numeric:

        values_a = pd.to_numeric(
            first[column],
            errors="coerce",
        ).replace([np.inf, -np.inf], np.nan).dropna()

        values_b = pd.to_numeric(
            second[column],
            errors="coerce",
        ).replace([np.inf, -np.inf], np.nan).dropna()

        statistics = {
            "Mean": (
                values_a.mean(),
                values_b.mean(),
            ),
            "Median": (
                values_a.median(),
                values_b.median(),
            ),
            "Minimum": (
                values_a.min(),
                values_b.min(),
            ),
            "Maximum": (
                values_a.max(),
                values_b.max(),
            ),
            "Standard Deviation": (
                values_a.std(),
                values_b.std(),
            ),
        }

        for statistic, values in statistics.items():

            value_a, value_b = values

            records.append({
                "Column": column,
                "Statistic": statistic,
                "First Dataset": value_a,
                "Second Dataset": value_b,
                "Difference": (
                    value_b - value_a
                    if pd.notna(value_a) and pd.notna(value_b)
                    else np.nan
                ),
            })

    return pd.DataFrame(records)


# ---------------------------------------------------------
# CATEGORICAL DISTRIBUTION COMPARISON
# ---------------------------------------------------------

def compare_categorical_distribution(
    first,
    second,
    column,
):
    """
    Compare category frequencies in a common column.
    """

    is_valid, error = validate_comparison_datasets(
        first,
        second,
    )

    if not is_valid:
        raise ValueError(error)

    if column not in first.columns:
        raise ValueError(
            "Column does not exist in the first dataset."
        )

    if column not in second.columns:
        raise ValueError(
            "Column does not exist in the second dataset."
        )

    frequencies_a = (
        first[column]
        .value_counts(normalize=True, dropna=False)
        * 100
    )

    frequencies_b = (
        second[column]
        .value_counts(normalize=True, dropna=False)
        * 100
    )

    result = pd.DataFrame({
        "First Dataset Percentage": frequencies_a,
        "Second Dataset Percentage": frequencies_b,
    }).fillna(0)

    result.index = result.index.map(str)

    result.index.name = "Category"

    result["Difference"] = (
        result["Second Dataset Percentage"]
        - result["First Dataset Percentage"]
    )

    return result.reset_index()


# ---------------------------------------------------------
# RECORD COMPARISON
# ---------------------------------------------------------

def compare_records(
    first,
    second,
    key_columns,
):
    """
    Compare records using one or more key columns.

    Returns:
        Records only in the first dataset.
        Records only in the second dataset.
        Records found in both datasets.

    Key columns must uniquely identify records in each dataset.
    """

    is_valid, error = validate_comparison_datasets(
        first,
        second,
    )

    if not is_valid:
        raise ValueError(error)

    if isinstance(key_columns, str):
        key_columns = [key_columns]

    if not key_columns:
        raise ValueError("At least one key column is required.")

    for column in key_columns:

        if column not in first.columns:
            raise ValueError(
                f"Key column '{column}' is missing from the first dataset."
            )

        if column not in second.columns:
            raise ValueError(
                f"Key column '{column}' is missing from the second dataset."
            )

    if first[key_columns].isna().any().any():
        raise ValueError(
            "First dataset contains missing key values."
        )

    if second[key_columns].isna().any().any():
        raise ValueError(
            "Second dataset contains missing key values."
        )

    if first.duplicated(subset=key_columns).any():
        raise ValueError(
            "First dataset contains duplicate key combinations."
        )

    if second.duplicated(subset=key_columns).any():
        raise ValueError(
            "Second dataset contains duplicate key combinations."
        )

    first_keys = pd.MultiIndex.from_frame(
        first[key_columns]
    )

    second_keys = pd.MultiIndex.from_frame(
        second[key_columns]
    )

    second_key_set = set(second_keys)
    first_key_set = set(first_keys)

    only_first_mask = [
        key not in second_key_set
        for key in first_keys
    ]

    only_second_mask = [
        key not in first_key_set
        for key in second_keys
    ]

    common_mask = [
        key in second_key_set
        for key in first_keys
    ]

    return {
        "only_in_first": first.loc[
            only_first_mask
        ].copy(),

        "only_in_second": second.loc[
            only_second_mask
        ].copy(),

        "common_records": first.loc[
            common_mask
        ].copy(),

        "only_first_count": int(
            sum(only_first_mask)
        ),

        "only_second_count": int(
            sum(only_second_mask)
        ),

        "common_count": int(
            sum(common_mask)
        ),
    }


# ---------------------------------------------------------
# VALUE DIFFERENCE COMPARISON
# ---------------------------------------------------------

def compare_matching_records(
    first,
    second,
    key_columns,
    compare_columns=None,
):
    """
    Compare values for records sharing the same keys.

    Returns one row per matching record and compared column,
    showing whether the values changed.

    Values are compared directly. Different data types may
    therefore be treated as different values.
    """

    is_valid, error = validate_comparison_datasets(
        first,
        second,
    )

    if not is_valid:
        raise ValueError(error)

    if isinstance(key_columns, str):
        key_columns = [key_columns]

    if not key_columns:
        raise ValueError("At least one key column is required.")

    for column in key_columns:

        if column not in first.columns or column not in second.columns:
            raise ValueError(
                f"Key column '{column}' must exist in both datasets."
            )

    if first.duplicated(subset=key_columns).any():
        raise ValueError(
            "First dataset contains duplicate key combinations."
        )

    if second.duplicated(subset=key_columns).any():
        raise ValueError(
            "Second dataset contains duplicate key combinations."
        )

    common_columns = [
        column
        for column in first.columns
        if column in second.columns
        and column not in key_columns
    ]

    if compare_columns is not None:

        requested = set(compare_columns)

        common_columns = [
            column
            for column in common_columns
            if column in requested
        ]

    left = first[
        key_columns + common_columns
    ].copy()

    right = second[
        key_columns + common_columns
    ].copy()

    left = left.rename(
        columns={
            column: f"{column}_first"
            for column in common_columns
        }
    )

    right = right.rename(
        columns={
            column: f"{column}_second"
            for column in common_columns
        }
    )

    merged = left.merge(
        right,
        on=key_columns,
        how="inner",
    )

    records = []

    for _, row in merged.iterrows():

        key_values = {
            key: row[key]
            for key in key_columns
        }

        for column in common_columns:

            value_a = row[f"{column}_first"]
            value_b = row[f"{column}_second"]

            if pd.isna(value_a) and pd.isna(value_b):
                changed = False

            elif pd.isna(value_a) or pd.isna(value_b):
                changed = True

            else:
                changed = not (
                    type(value_a) == type(value_b)
                    and value_a == value_b
                )

            records.append({
                **key_values,
                "Column": column,
                "First Value": value_a,
                "Second Value": value_b,
                "Changed": changed,
            })

    return pd.DataFrame(records)


# ---------------------------------------------------------
# DATASET SIMILARITY
# ---------------------------------------------------------

def calculate_structure_similarity(first, second):
    """
    Calculate the percentage of matching column names.

    This measures structure similarity only, not data equality.
    """

    comparison = compare_columns(first, second)

    all_columns = set(first.columns).union(
        set(second.columns)
    )

    if not all_columns:
        return 100.0

    similarity = (
        len(comparison["common_columns"])
        / len(all_columns)
    ) * 100

    return round(similarity, 2)


# ---------------------------------------------------------
# COMPLETE COMPARISON REPORT
# ---------------------------------------------------------

def generate_comparison_report(
    first,
    second,
    first_name="Dataset A",
    second_name="Dataset B",
):
    """
    Generate a complete comparison report.
    """

    is_valid, error = validate_comparison_datasets(
        first,
        second,
    )

    if not is_valid:
        raise ValueError(error)

    column_comparison = compare_columns(
        first,
        second,
    )

    return {
        "overview": compare_dataset_overview(
            first,
            second,
            first_name,
            second_name,
        ),

        "columns": column_comparison,

        "data_types": compare_column_types(
            first,
            second,
        ),

        "numerical_statistics": compare_numerical_statistics(
            first,
            second,
        ),

        "structure_similarity": calculate_structure_similarity(
            first,
            second,
        ),

        "summary": {
            "first_dataset_rows": len(first),
            "second_dataset_rows": len(second),
            "common_columns": column_comparison["common_count"],
            "columns_only_in_first": column_comparison["only_first_count"],
            "columns_only_in_second": column_comparison["only_second_count"],
        },
    }
