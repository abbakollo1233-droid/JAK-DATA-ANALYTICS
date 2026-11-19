"""
JAK Data Analytics
Data Profiling Service

Provides independent dataset profiling functionality.

Features:
- Dataset overview
- Column information
- Missing-value analysis
- Duplicate analysis
- Statistical summaries
- Categorical analysis
- Correlation analysis
- Data quality assessment

This module does not depend on Streamlit.
"""

import pandas as pd
import numpy as np


# ==================================================
# DATASET VALIDATION
# ==================================================

def validate_dataframe(data):
    """Validate that the input is a usable DataFrame."""

    if not isinstance(data, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    if data.empty:
        raise ValueError("The dataset is empty.")

    return True


# ==================================================
# DATASET OVERVIEW
# ==================================================

def get_dataset_overview(data):
    """Return general information about a dataset."""

    validate_dataframe(data)

    rows, columns = data.shape

    return {
        "total_rows": int(rows),
        "total_columns": int(columns),
        "total_cells": int(rows * columns),
        "memory_usage_bytes": int(
            data.memory_usage(deep=True).sum()
        ),
        "memory_usage_mb": round(
            data.memory_usage(deep=True).sum()
            / (1024 * 1024),
            2
        ),
        "duplicate_rows": int(
            data.duplicated().sum()
        ),
        "missing_cells": int(
            data.isna().sum().sum()
        ),
    }


# ==================================================
# COLUMN INFORMATION
# ==================================================

def get_column_information(data):
    """Return detailed information about each column."""

    validate_dataframe(data)

    information = []

    for column in data.columns:

        series = data[column]

        missing = int(series.isna().sum())

        information.append({
            "column": str(column),
            "data_type": str(series.dtype),
            "non_null": int(series.notna().sum()),
            "missing": missing,
            "missing_percentage": round(
                (missing / len(data)) * 100,
                2
            ),
            "unique_values": int(series.nunique()),
            "is_constant": bool(
                series.nunique(dropna=True) <= 1
            ),
        })

    return pd.DataFrame(information)


# ==================================================
# MISSING VALUE ANALYSIS
# ==================================================

def get_missing_value_analysis(data):
    """Analyse missing values in the dataset."""

    validate_dataframe(data)

    missing_counts = data.isna().sum()

    result = pd.DataFrame({
        "column": missing_counts.index.astype(str),
        "missing_values": missing_counts.values,
    })

    result["missing_percentage"] = (
        result["missing_values"] / len(data)
    ) * 100

    result = result.sort_values(
        by="missing_percentage",
        ascending=False
    ).reset_index(drop=True)

    return result


# ==================================================
# DUPLICATE ANALYSIS
# ==================================================

def get_duplicate_analysis(data):
    """Analyse duplicate rows."""

    validate_dataframe(data)

    duplicate_mask = data.duplicated()

    duplicate_count = int(
        duplicate_mask.sum()
    )

    total_rows = len(data)

    return {
        "total_rows": total_rows,
        "duplicate_rows": duplicate_count,
        "unique_rows": int(
            total_rows - duplicate_count
        ),
        "duplicate_percentage": round(
            (duplicate_count / total_rows) * 100,
            2
        ),
        "duplicate_preview": data.loc[
            duplicate_mask
        ].head(20).copy(),
    }


# ==================================================
# NUMERICAL STATISTICS
# ==================================================

def get_numerical_statistics(data):
    """Generate descriptive statistics for numerical columns."""

    validate_dataframe(data)

    numerical_data = data.select_dtypes(
        include=np.number
    )

    if numerical_data.empty:
        return pd.DataFrame()

    statistics = numerical_data.describe().T

    statistics["missing_values"] = (
        numerical_data.isna().sum()
    )

    statistics["unique_values"] = (
        numerical_data.nunique()
    )

    statistics["skewness"] = (
        numerical_data.skew()
    )

    statistics["kurtosis"] = (
        numerical_data.kurtosis()
    )

    return statistics.reset_index(
        names="column"
    )


# ==================================================
# CATEGORICAL ANALYSIS
# ==================================================

def get_categorical_analysis(
    data,
    top_n=10
):
    """Analyse categorical columns."""

    validate_dataframe(data)

    categorical_data = data.select_dtypes(
        include=["object", "category", "bool", "string"]
    )

    results = {}

    for column in categorical_data.columns:

        series = categorical_data[column]

        value_counts = (
            series
            .value_counts(dropna=False)
            .head(max(1, min(top_n, 100)))
        )

        results[str(column)] = {
            "unique_values": int(
                series.nunique(dropna=True)
            ),
            "most_common_values": value_counts.to_dict(),
            "missing_values": int(
                series.isna().sum()
            ),
        }

    return results


# ==================================================
# CORRELATION ANALYSIS
# ==================================================

def get_correlation_analysis(
    data,
    method="pearson"
):
    """Calculate correlations between numerical columns."""

    validate_dataframe(data)

    allowed_methods = [
        "pearson",
        "spearman",
        "kendall",
    ]

    if method not in allowed_methods:
        raise ValueError("Unsupported correlation method.")

    numerical_data = data.select_dtypes(
        include=np.number
    )

    if numerical_data.shape[1] < 2:
        return pd.DataFrame()

    return numerical_data.corr(
        method=method
    )


# ==================================================
# OUTLIER ANALYSIS
# ==================================================

def get_outlier_analysis(data):
    """Identify numerical outliers using the IQR method."""

    validate_dataframe(data)

    numerical_data = data.select_dtypes(
        include=np.number
    )

    results = []

    for column in numerical_data.columns:

        series = numerical_data[column].dropna()

        if series.empty:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)

        iqr = q3 - q1

        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

        outlier_mask = (
            (series < lower_bound)
            | (series > upper_bound)
        )

        outlier_count = int(
            outlier_mask.sum()
        )

        results.append({
            "column": str(column),
            "lower_bound": float(lower_bound),
            "upper_bound": float(upper_bound),
            "outlier_count": outlier_count,
            "outlier_percentage": round(
                (outlier_count / len(series)) * 100,
                2
            ),
        })

    return pd.DataFrame(results)


# ==================================================
# DATA QUALITY SCORE
# ==================================================

def calculate_quality_score(data):
    """
    Calculate a basic data quality score.

    The score considers:
    - Missing values: 70% weight
    - Duplicate rows: 30% weight

    This is a preliminary heuristic, not a complete
    assessment of data correctness or fitness for use.
    """

    validate_dataframe(data)

    total_cells = data.shape[0] * data.shape[1]

    missing_cells = int(
        data.isna().sum().sum()
    )

    duplicate_rows = int(
        data.duplicated().sum()
    )

    missing_rate = (
        missing_cells / total_cells
        if total_cells
        else 0
    )

    duplicate_rate = (
        duplicate_rows / len(data)
        if len(data)
        else 0
    )

    missing_score = max(
        0,
        100 - missing_rate * 100
    )

    duplicate_score = max(
        0,
        100 - duplicate_rate * 100
    )

    quality_score = (
        missing_score * 0.70
        + duplicate_score * 0.30
    )

    return {
        "quality_score": round(
            float(quality_score),
            2
        ),
        "missing_score": round(
            float(missing_score),
            2
        ),
        "duplicate_score": round(
            float(duplicate_score),
            2
        ),
        "missing_rate": round(
            float(missing_rate * 100),
            2
        ),
        "duplicate_rate": round(
            float(duplicate_rate * 100),
            2
        ),
        "method": "Missing values 70%; duplicate rows 30%.",
    }


# ==================================================
# COMPLETE PROFILE
# ==================================================

def generate_complete_profile(data):
    """Generate a complete dataset profiling report."""

    validate_dataframe(data)

    return {
        "overview": get_dataset_overview(data),
        "columns": get_column_information(data),
        "missing_values": get_missing_value_analysis(data),
        "duplicates": get_duplicate_analysis(data),
        "numerical_statistics": get_numerical_statistics(data),
        "categorical_analysis": get_categorical_analysis(data),
        "correlations": get_correlation_analysis(data),
        "outliers": get_outlier_analysis(data),
        "quality": calculate_quality_score(data),
    }