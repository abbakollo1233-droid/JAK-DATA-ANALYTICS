"""
JAK Data Analytics
Data Quality Service

Provides reusable dataset quality assessment:
- Missing value detection
- Duplicate record detection
- Empty column detection
- Constant column detection
- Unique value analysis
- Invalid numerical value detection
- Column type analysis
- Quality scoring
- Data quality recommendations

This service is independent of Streamlit.
"""

import pandas as pd
import numpy as np


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_dataset(data):
    """
    Validate a DataFrame before quality assessment.
    """

    if not isinstance(data, pd.DataFrame):
        return False, "Input must be a Pandas DataFrame."

    if data.empty:
        return False, "Dataset is empty."

    if len(data.columns) == 0:
        return False, "Dataset contains no columns."

    if data.columns.duplicated().any():
        return False, "Dataset contains duplicate column names."

    return True, None


# ---------------------------------------------------------
# MISSING VALUE ANALYSIS
# ---------------------------------------------------------

def analyse_missing_values(data):
    """
    Calculate missing values for every column.
    """

    is_valid, error = validate_dataset(data)

    if not is_valid:
        raise ValueError(error)

    missing = data.isna().sum()

    result = pd.DataFrame({
        "Column": missing.index,
        "Missing Count": missing.values,
        "Missing Percentage": (
            missing.values / len(data)
        ) * 100,
    })

    result["Missing Percentage"] = (
        result["Missing Percentage"].round(2)
    )

    return result.sort_values(
        "Missing Percentage",
        ascending=False,
    ).reset_index(drop=True)


def get_total_missing_values(data):
    """
    Return the total number of missing cells.
    """

    return int(data.isna().sum().sum())


# ---------------------------------------------------------
# DUPLICATE ANALYSIS
# ---------------------------------------------------------

def analyse_duplicates(data):
    """
    Calculate duplicate record information.
    """

    duplicate_count = int(data.duplicated().sum())

    total_rows = len(data)

    percentage = (
        duplicate_count / total_rows * 100
        if total_rows
        else 0
    )

    return {
        "total_rows": total_rows,
        "duplicate_rows": duplicate_count,
        "unique_rows": total_rows - duplicate_count,
        "duplicate_percentage": round(percentage, 2),
    }


def get_duplicate_records(data):
    """
    Return duplicate records.
    """

    return data.loc[
        data.duplicated(keep=False)
    ].copy()


# ---------------------------------------------------------
# EMPTY COLUMN ANALYSIS
# ---------------------------------------------------------

def get_empty_columns(data):
    """
    Identify columns containing only missing values.
    """

    return [
        column
        for column in data.columns
        if data[column].isna().all()
    ]


# ---------------------------------------------------------
# CONSTANT COLUMN ANALYSIS
# ---------------------------------------------------------

def get_constant_columns(data):
    """
    Identify columns containing only one unique non-null value.
    """

    constant_columns = []

    for column in data.columns:

        unique_count = data[column].nunique(
            dropna=True
        )

        if unique_count <= 1:
            constant_columns.append(column)

    return constant_columns


# ---------------------------------------------------------
# UNIQUE VALUE ANALYSIS
# ---------------------------------------------------------

def analyse_unique_values(data):
    """
    Calculate unique values for every column.
    """

    records = []

    for column in data.columns:

        unique_count = int(
            data[column].nunique(dropna=True)
        )

        records.append({
            "Column": column,
            "Unique Values": unique_count,
            "Unique Percentage": round(
                unique_count / len(data) * 100,
                2,
            ) if len(data) else 0,
            "Total Rows": len(data),
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------
# INVALID NUMERICAL VALUES
# ---------------------------------------------------------

def analyse_invalid_numeric_values(data):
    """
    Identify infinite and invalid numerical values.

    Missing values are counted separately.
    """

    numeric_columns = data.select_dtypes(
        include="number"
    ).columns

    records = []

    for column in numeric_columns:

        values = pd.to_numeric(
            data[column],
            errors="coerce",
        )

        infinite_count = int(
            np.isinf(values.dropna()).sum()
        )

        records.append({
            "Column": column,
            "Infinite Values": infinite_count,
            "Missing Values": int(values.isna().sum()),
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------
# COLUMN TYPE ANALYSIS
# ---------------------------------------------------------

def analyse_column_types(data):
    """
    Inspect column data types.
    """

    records = []

    for column in data.columns:

        series = data[column]

        records.append({
            "Column": column,
            "Data Type": str(series.dtype),
            "Non-Null Values": int(series.notna().sum()),
            "Missing Values": int(series.isna().sum()),
            "Unique Values": int(series.nunique(dropna=True)),
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------
# TEXT QUALITY ANALYSIS
# ---------------------------------------------------------

def analyse_text_quality(data):
    """
    Identify empty strings and leading/trailing whitespace
    in text columns.
    """

    records = []

    text_columns = data.select_dtypes(
        include=["object", "string"]
    ).columns

    for column in text_columns:

        series = data[column].dropna().astype(str)

        empty_count = int(
            series.str.strip().eq("").sum()
        )

        whitespace_count = int(
            series.ne(series.str.strip()).sum()
        )

        records.append({
            "Column": column,
            "Empty Strings": empty_count,
            "Whitespace Issues": whitespace_count,
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------
# OUTLIER ANALYSIS
# ---------------------------------------------------------

def analyse_outliers(data):
    """
    Detect numerical outliers using the IQR method.

    Outliers are statistical flags, not necessarily errors.
    """

    numeric_columns = data.select_dtypes(
        include="number"
    ).columns

    records = []

    for column in numeric_columns:

        values = pd.to_numeric(
            data[column],
            errors="coerce",
        ).dropna()

        values = values[np.isfinite(values)]

        if values.empty:
            continue

        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)

        iqr = q3 - q1

        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

        outlier_count = int(
            (
                (values < lower_bound)
                | (values > upper_bound)
            ).sum()
        )

        records.append({
            "Column": column,
            "Outlier Count": outlier_count,
            "Lower Bound": float(lower_bound),
            "Upper Bound": float(upper_bound),
            "Outlier Percentage": round(
                outlier_count / len(values) * 100,
                2,
            ),
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------
# QUALITY DIMENSIONS
# ---------------------------------------------------------

def calculate_completeness(data):
    """
    Measure the percentage of non-missing cells.
    """

    if data.empty or data.size == 0:
        return 0.0

    complete_cells = int(data.notna().sum().sum())

    return round(
        complete_cells / data.size * 100,
        2,
    )


def calculate_uniqueness(data):
    """
    Measure the percentage of rows that are not duplicates.

    This is a row-level uniqueness indicator.
    """

    if data.empty:
        return 0.0

    duplicate_count = int(data.duplicated().sum())

    return round(
        (len(data) - duplicate_count) / len(data) * 100,
        2,
    )


def calculate_validity(data):
    """
    Measure basic value validity.

    Checks:
    - Infinite numerical values
    - Empty text strings

    This is a basic technical check, not a domain-specific
    validation of whether values are factually correct.
    """

    if data.empty or data.size == 0:
        return 0.0

    invalid_count = 0

    numeric_columns = data.select_dtypes(
        include="number"
    ).columns

    for column in numeric_columns:

        values = pd.to_numeric(
            data[column],
            errors="coerce",
        )

        invalid_count += int(
            np.isinf(values.dropna()).sum()
        )

    text_columns = data.select_dtypes(
        include=["object", "string"]
    ).columns

    for column in text_columns:

        series = data[column].dropna().astype(str)

        invalid_count += int(
            series.str.strip().eq("").sum()
        )

    return round(
        max(0, (data.size - invalid_count) / data.size * 100),
        2,
    )


# ---------------------------------------------------------
# OVERALL QUALITY SCORE
# ---------------------------------------------------------

def calculate_quality_score(data):
    """
    Calculate a basic overall data quality score.

    Weights:
        Completeness: 40%
        Uniqueness:   30%
        Validity:     30%

    This is a configurable heuristic, not a universal
    measure of dataset correctness.
    """

    is_valid, error = validate_dataset(data)

    if not is_valid:
        raise ValueError(error)

    completeness = calculate_completeness(data)
    uniqueness = calculate_uniqueness(data)
    validity = calculate_validity(data)

    score = (
        completeness * 0.40
        + uniqueness * 0.30
        + validity * 0.30
    )

    return {
        "overall_score": round(score, 2),
        "completeness": completeness,
        "uniqueness": uniqueness,
        "validity": validity,
        "rating": get_quality_rating(score),
    }


def get_quality_rating(score):
    """
    Convert a quality score into a readable rating.
    """

    if score >= 95:
        return "Excellent"

    if score >= 85:
        return "Very Good"

    if score >= 70:
        return "Good"

    if score >= 50:
        return "Needs Improvement"

    return "Poor"


# ---------------------------------------------------------
# QUALITY RECOMMENDATIONS
# ---------------------------------------------------------

def generate_quality_recommendations(data):
    """
    Generate recommendations based on detected problems.
    """

    is_valid, error = validate_dataset(data)

    if not is_valid:
        raise ValueError(error)

    recommendations = []

    missing_count = get_total_missing_values(data)

    duplicate_count = int(data.duplicated().sum())

    empty_columns = get_empty_columns(data)

    constant_columns = get_constant_columns(data)

    if missing_count > 0:
        recommendations.append({
            "category": "Completeness",
            "priority": "High",
            "issue": f"{missing_count} missing values detected.",
            "recommendation": (
                "Investigate missing values and choose an "
                "appropriate treatment strategy."
            ),
        })

    if duplicate_count > 0:
        recommendations.append({
            "category": "Uniqueness",
            "priority": "Medium",
            "issue": f"{duplicate_count} duplicate rows detected.",
            "recommendation": (
                "Review duplicate records before deciding "
                "whether to remove them."
            ),
        })

    if empty_columns:
        recommendations.append({
            "category": "Structure",
            "priority": "High",
            "issue": (
                "Completely empty columns detected: "
                + ", ".join(map(str, empty_columns))
            ),
            "recommendation": (
                "Check whether these columns should be "
                "recovered or removed."
            ),
        })

    if constant_columns:
        recommendations.append({
            "category": "Structure",
            "priority": "Low",
            "issue": (
                "Columns with only one non-missing value: "
                + ", ".join(map(str, constant_columns))
            ),
            "recommendation": (
                "Consider removing columns that provide "
                "no useful variation for the intended analysis."
            ),
        })

    text_quality = analyse_text_quality(data)

    if not text_quality.empty:

        empty_text_count = int(
            text_quality["Empty Strings"].sum()
        )

        whitespace_count = int(
            text_quality["Whitespace Issues"].sum()
        )

        if empty_text_count > 0:
            recommendations.append({
                "category": "Text Quality",
                "priority": "Medium",
                "issue": (
                    f"{empty_text_count} empty text values detected."
                ),
                "recommendation": (
                    "Convert blank strings to missing values "
                    "or apply an appropriate cleaning rule."
                ),
            })

        if whitespace_count > 0:
            recommendations.append({
                "category": "Text Quality",
                "priority": "Low",
                "issue": (
                    f"{whitespace_count} values contain "
                    "leading or trailing whitespace."
                ),
                "recommendation": (
                    "Trim unnecessary whitespace from text columns."
                ),
            })

    return recommendations


# ---------------------------------------------------------
# COMPLETE QUALITY REPORT
# ---------------------------------------------------------

def generate_quality_report(data):
    """
    Generate a complete dataset quality report.

    Returns a dictionary containing all quality results.
    """

    is_valid, error = validate_dataset(data)

    if not is_valid:
        raise ValueError(error)

    score = calculate_quality_score(data)

    return {
        "dataset_overview": {
            "rows": int(data.shape[0]),
            "columns": int(data.shape[1]),
            "cells": int(data.size),
        },

        "quality_score": score,

        "missing_values": analyse_missing_values(data),

        "duplicates": analyse_duplicates(data),

        "empty_columns": get_empty_columns(data),

        "constant_columns": get_constant_columns(data),

        "unique_values": analyse_unique_values(data),

        "invalid_numeric_values": analyse_invalid_numeric_values(data),

        "column_types": analyse_column_types(data),

        "text_quality": analyse_text_quality(data),

        "outliers": analyse_outliers(data),

        "recommendations": generate_quality_recommendations(data),
    }
