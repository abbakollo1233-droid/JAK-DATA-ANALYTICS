"""
JAK Data Analytics
Recommendation Service

An independent recommendation engine that examines
datasets and generates useful analytical suggestions.

Features:
- Data quality recommendations
- Missing value recommendations
- Duplicate recommendations
- Numerical analysis recommendations
- Categorical analysis recommendations
- Correlation recommendations
- Outlier recommendations
- Dataset size recommendations
- Date and time recommendations
- Machine learning recommendations
- Prioritised recommendation reports

This module does not depend on Streamlit.

Recommendations are suggestions, not guaranteed
business outcomes or causal conclusions.
"""

import numpy as np
import pandas as pd

from typing import Any


# ==================================================
# CONSTANTS
# ==================================================

PRIORITY_ORDER = {
    "High": 1,
    "Medium": 2,
    "Low": 3,
}

RECOMMENDATION_CATEGORIES = [
    "Data Quality",
    "Missing Values",
    "Duplicates",
    "Numerical Analysis",
    "Categorical Analysis",
    "Correlation",
    "Outliers",
    "Dataset Structure",
    "Date and Time",
    "Machine Learning",
]


# ==================================================
# VALIDATION
# ==================================================

def validate_dataframe(data):
    """Validate a dataset before analysis."""

    if not isinstance(data, pd.DataFrame):
        raise TypeError(
            "Input must be a pandas DataFrame."
        )

    if data.empty:
        raise ValueError(
            "The dataset is empty."
        )

    if len(data.columns) == 0:
        raise ValueError(
            "The dataset contains no columns."
        )

    return True


# ==================================================
# RECOMMENDATION BUILDER
# ==================================================

def create_recommendation(
    title,
    description,
    category,
    priority="Medium",
    action=None,
    affected_columns=None,
    evidence=None,
):
    """Create a standardized recommendation."""

    if priority not in PRIORITY_ORDER:
        raise ValueError(
            "Priority must be High, Medium, or Low."
        )

    return {
        "title": str(title),
        "description": str(description),
        "category": str(category),
        "priority": priority,
        "action": str(action or ""),
        "affected_columns": affected_columns or [],
        "evidence": evidence or {},
    }


# ==================================================
# DATA QUALITY RECOMMENDATIONS
# ==================================================

def recommend_data_quality(data):
    """Generate general data quality recommendations."""

    validate_dataframe(data)

    recommendations = []

    total_cells = data.shape[0] * data.shape[1]

    missing_cells = int(
        data.isna().sum().sum()
    )

    missing_percentage = (
        missing_cells / total_cells * 100
        if total_cells else 0
    )

    duplicate_count = int(
        data.duplicated().sum()
    )

    duplicate_percentage = (
        duplicate_count / len(data) * 100
        if len(data) else 0
    )

    if missing_percentage >= 30:
        recommendations.append(
            create_recommendation(
                title="High Missing Data",
                description=(
                    f"{missing_percentage:.2f}% of dataset cells "
                    "contain missing values. This may affect "
                    "statistical analysis and predictive models."
                ),
                category="Data Quality",
                priority="High",
                action=(
                    "Investigate why values are missing. "
                    "Consider appropriate imputation or removal "
                    "after examining the missingness pattern."
                ),
                evidence={
                    "missing_cells": missing_cells,
                    "missing_percentage": round(
                        missing_percentage, 2
                    ),
                },
            )
        )

    elif missing_percentage > 5:
        recommendations.append(
            create_recommendation(
                title="Review Missing Values",
                description=(
                    f"{missing_percentage:.2f}% of dataset cells "
                    "are missing."
                ),
                category="Data Quality",
                priority="Medium",
                action=(
                    "Review missing values and determine "
                    "an appropriate treatment strategy."
                ),
                evidence={
                    "missing_cells": missing_cells,
                    "missing_percentage": round(
                        missing_percentage, 2
                    ),
                },
            )
        )

    if duplicate_percentage >= 10:
        recommendations.append(
            create_recommendation(
                title="Large Number of Duplicate Records",
                description=(
                    f"{duplicate_count} duplicate rows were found, "
                    f"representing {duplicate_percentage:.2f}% "
                    "of the dataset."
                ),
                category="Data Quality",
                priority="High",
                action=(
                    "Investigate duplicate records and remove "
                    "only those confirmed to be unintended."
                ),
                evidence={
                    "duplicate_count": duplicate_count,
                    "duplicate_percentage": round(
                        duplicate_percentage, 2
                    ),
                },
            )
        )

    elif duplicate_count > 0:
        recommendations.append(
            create_recommendation(
                title="Review Duplicate Records",
                description=(
                    f"{duplicate_count} duplicate rows were detected."
                ),
                category="Data Quality",
                priority="Medium",
                action=(
                    "Review the duplicate rows before deciding "
                    "whether they should be removed."
                ),
                evidence={
                    "duplicate_count": duplicate_count,
                },
            )
        )

    constant_columns = [
        column
        for column in data.columns
        if data[column].nunique(dropna=True) <= 1
    ]

    if constant_columns:
        recommendations.append(
            create_recommendation(
                title="Constant Columns Detected",
                description=(
                    f"{len(constant_columns)} columns contain "
                    "only one distinct non-missing value."
                ),
                category="Data Quality",
                priority="Medium",
                action=(
                    "Check whether these columns provide useful "
                    "information. Consider removing irrelevant "
                    "constant columns."
                ),
                affected_columns=constant_columns,
            )
        )

    return recommendations


# ==================================================
# NUMERICAL RECOMMENDATIONS
# ==================================================

def recommend_numerical_analysis(data):
    """Generate recommendations for numerical columns."""

    validate_dataframe(data)

    recommendations = []

    numeric_columns = data.select_dtypes(
        include=np.number
    ).columns.tolist()

    if not numeric_columns:
        recommendations.append(
            create_recommendation(
                title="No Numerical Features Found",
                description=(
                    "The dataset has no recognised numerical columns."
                ),
                category="Numerical Analysis",
                priority="Low",
                action=(
                    "Check whether numeric information is stored "
                    "as text and convert it where appropriate."
                ),
            )
        )

        return recommendations

    for column in numeric_columns:

        values = pd.to_numeric(
            data[column],
            errors="coerce"
        )

        values = values.replace(
            [np.inf, -np.inf],
            np.nan
        ).dropna()

        if values.empty:
            continue

        if values.nunique() <= 1:
            continue

        skewness = values.skew()

        if pd.notna(skewness) and abs(skewness) > 1:
            recommendations.append(
                create_recommendation(
                    title=f"Highly Skewed Distribution: {column}",
                    description=(
                        f"The column '{column}' has a skewness "
                        f"of {skewness:.2f}. Its distribution may "
                        "be strongly asymmetric."
                    ),
                    category="Numerical Analysis",
                    priority="Medium",
                    action=(
                        "Inspect the distribution and consider "
                        "a suitable transformation if required "
                        "by your analysis."
                    ),
                    affected_columns=[column],
                    evidence={
                        "skewness": round(
                            float(skewness), 3
                        ),
                    },
                )
            )

        if len(values) >= 5:

            q1 = values.quantile(0.25)
            q3 = values.quantile(0.75)

            iqr = q3 - q1

            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

            outlier_count = int(
                (
                    (values < lower)
                    | (values > upper)
                ).sum()
            )

            if outlier_count > 0:

                outlier_percentage = (
                    outlier_count / len(values) * 100
                )

                recommendations.append(
                    create_recommendation(
                        title=f"Potential Outliers: {column}",
                        description=(
                            f"{outlier_count} observations in "
                            f"'{column}' fall outside the IQR "
                            f"fences ({outlier_percentage:.2f}%)."
                        ),
                        category="Outliers",
                        priority=(
                            "High"
                            if outlier_percentage >= 10
                            else "Medium"
                        ),
                        action=(
                            "Investigate unusual observations. "
                            "Determine whether they are valid "
                            "extreme values or data errors."
                        ),
                        affected_columns=[column],
                        evidence={
                            "outlier_count": outlier_count,
                            "outlier_percentage": round(
                                outlier_percentage, 2
                            ),
                            "lower_bound": float(lower),
                            "upper_bound": float(upper),
                        },
                    )
                )

    return recommendations


# ==================================================
# CORRELATION RECOMMENDATIONS
# ==================================================

def recommend_correlations(data):
    """Identify potentially useful numerical relationships."""

    validate_dataframe(data)

    recommendations = []

    numeric_data = data.select_dtypes(
        include=np.number
    )

    numeric_data = numeric_data.replace(
        [np.inf, -np.inf],
        np.nan
    )

    if numeric_data.shape[1] < 2:
        return recommendations

    correlation = numeric_data.corr(
        method="pearson",
        min_periods=3,
    )

    columns = correlation.columns.tolist()

    for i in range(len(columns)):

        for j in range(i + 1, len(columns)):

            first = columns[i]
            second = columns[j]

            value = correlation.loc[
                first,
                second
            ]

            if pd.isna(value):
                continue

            strength = abs(value)

            if strength >= 0.9:
                priority = "High"
                description_strength = "very strong"

            elif strength >= 0.7:
                priority = "Medium"
                description_strength = "strong"

            elif strength >= 0.5:
                priority = "Low"
                description_strength = "moderate"

            else:
                continue

            direction = (
                "positive"
                if value > 0
                else "negative"
            )

            recommendations.append(
                create_recommendation(
                    title=(
                        f"Relationship Between {first} and {second}"
                    ),
                    description=(
                        f"A {description_strength} {direction} "
                        f"Pearson correlation ({value:.3f}) "
                        "was observed."
                    ),
                    category="Correlation",
                    priority=priority,
                    action=(
                        "Create a scatter plot and investigate "
                        "the relationship. Correlation alone "
                        "does not establish causation."
                    ),
                    affected_columns=[
                        first,
                        second,
                    ],
                    evidence={
                        "correlation": round(
                            float(value), 4
                        ),
                        "method": "Pearson",
                    },
                )
            )

    return recommendations


# ==================================================
# CATEGORICAL RECOMMENDATIONS
# ==================================================

def recommend_categorical_analysis(data):
    """Generate recommendations for categorical columns."""

    validate_dataframe(data)

    recommendations = []

    categorical_columns = data.select_dtypes(
        include=["object", "category", "string", "bool"]
    ).columns.tolist()

    for column in categorical_columns:

        values = data[column].dropna()

        if values.empty:
            continue

        unique_count = values.nunique()

        if unique_count == 0:
            continue

        if unique_count == 1:
            continue

        unique_percentage = (
            unique_count / len(values) * 100
        )

        if unique_percentage >= 80 and unique_count > 20:
            recommendations.append(
                create_recommendation(
                    title=f"High Cardinality: {column}",
                    description=(
                        f"'{column}' contains {unique_count} "
                        "distinct values. This may create "
                        "complications for some categorical analyses."
                    ),
                    category="Categorical Analysis",
                    priority="Medium",
                    action=(
                        "Inspect the values. Consider grouping "
                        "rare categories where meaningful, "
                        "or using an appropriate encoding method."
                    ),
                    affected_columns=[column],
                    evidence={
                        "unique_values": int(unique_count),
                        "unique_percentage": round(
                            unique_percentage, 2
                        ),
                    },
                )
            )

        frequencies = values.value_counts(
            normalize=True
        )

        if not frequencies.empty:

            dominant_percentage = (
                frequencies.iloc[0] * 100
            )

            if dominant_percentage >= 90:
                recommendations.append(
                    create_recommendation(
                        title=f"Dominant Category: {column}",
                        description=(
                            f"One category accounts for "
                            f"{dominant_percentage:.2f}% "
                            "of non-missing observations."
                        ),
                        category="Categorical Analysis",
                        priority="Medium",
                        action=(
                            "Review category balance. If this is "
                            "a prediction target, consider whether "
                            "class imbalance requires attention."
                        ),
                        affected_columns=[column],
                        evidence={
                            "dominant_percentage": round(
                                dominant_percentage, 2
                            ),
                            "dominant_category": str(
                                frequencies.index[0]
                            ),
                        },
                    )
                )

    return recommendations


# ==================================================
# DATE AND TIME RECOMMENDATIONS
# ==================================================

def recommend_date_analysis(data):
    """Recommend time-based analysis when suitable."""

    validate_dataframe(data)

    recommendations = []

    date_columns = data.select_dtypes(
        include=["datetime", "datetimetz"]
    ).columns.tolist()

    for column in data.columns:

        if column in date_columns:
            continue

        if (
            data[column].dtype == "object"
            or pd.api.types.is_string_dtype(data[column])
        ):
            name = str(column).lower()

            if any(
                keyword in name
                for keyword in [
                    "date",
                    "time",
                    "timestamp",
                    "year",
                    "month",
                ]
            ):
                parsed = pd.to_datetime(
                    data[column],
                    errors="coerce"
                )

                valid_count = int(
                    parsed.notna().sum()
                )

                if valid_count >= max(
                    3,
                    int(len(data) * 0.5)
                ):
                    date_columns.append(column)

    for column in date_columns:

        recommendations.append(
            create_recommendation(
                title=f"Time-Based Analysis: {column}",
                description=(
                    f"'{column}' appears to contain date or "
                    "time information."
                ),
                category="Date and Time",
                priority="Low",
                action=(
                    "Consider time-based grouping, trend analysis, "
                    "seasonality analysis, or forecasting if "
                    "the data and business question support it."
                ),
                affected_columns=[column],
            )
        )

    return recommendations


# ==================================================
# DATASET STRUCTURE RECOMMENDATIONS
# ==================================================

def recommend_dataset_structure(data):
    """Evaluate the general shape of the dataset."""

    validate_dataframe(data)

    recommendations = []

    rows, columns = data.shape

    if rows < 30:
        recommendations.append(
            create_recommendation(
                title="Small Dataset",
                description=(
                    f"The dataset contains only {rows} rows."
                ),
                category="Dataset Structure",
                priority="Medium",
                action=(
                    "Interpret statistical results cautiously. "
                    "Collect more representative observations "
                    "if possible."
                ),
                evidence={
                    "rows": rows,
                    "columns": columns,
                },
            )
        )

    if columns > 100:
        recommendations.append(
            create_recommendation(
                title="High Number of Features",
                description=(
                    f"The dataset contains {columns} columns."
                ),
                category="Dataset Structure",
                priority="Medium",
                action=(
                    "Review feature relevance, redundancy, "
                    "and potential dimensionality reduction."
                ),
                evidence={
                    "columns": columns,
                },
            )
        )

    if columns == 1:
        recommendations.append(
            create_recommendation(
                title="Single-Column Dataset",
                description=(
                    "The dataset contains only one column."
                ),
                category="Dataset Structure",
                priority="Low",
                action=(
                    "Consider adding relevant variables "
                    "if the intended analysis requires them."
                ),
            )
        )

    if rows > 100000 and columns > 50:
        recommendations.append(
            create_recommendation(
                title="Large Dataset",
                description=(
                    f"The dataset contains {rows:,} rows "
                    f"and {columns} columns."
                ),
                category="Dataset Structure",
                priority="Low",
                action=(
                    "Consider efficient processing tools, "
                    "column selection, and memory-aware "
                    "analysis methods."
                ),
                evidence={
                    "rows": rows,
                    "columns": columns,
                },
            )
        )

    return recommendations


# ==================================================
# MACHINE LEARNING RECOMMENDATIONS
# ==================================================

def recommend_machine_learning(data):
    """Identify whether the dataset may support ML exploration."""

    validate_dataframe(data)

    recommendations = []

    numeric_columns = data.select_dtypes(
        include=np.number
    ).columns.tolist()

    categorical_columns = data.select_dtypes(
        include=["object", "category", "string", "bool"]
    ).columns.tolist()

    if len(data) < 100:
        recommendations.append(
            create_recommendation(
                title="Review Dataset Size Before Machine Learning",
                description=(
                    "The dataset has fewer than 100 observations. "
                    "Some machine learning models may be unstable "
                    "or difficult to evaluate reliably."
                ),
                category="Machine Learning",
                priority="Medium",
                action=(
                    "Check whether the dataset is representative "
                    "and whether sufficient training and test "
                    "observations are available."
                ),
            )
        )

    if len(numeric_columns) + len(categorical_columns) >= 2:
        recommendations.append(
            create_recommendation(
                title="Explore Machine Learning",
                description=(
                    "The dataset contains multiple usable "
                    "numerical or categorical features."
                ),
                category="Machine Learning",
                priority="Low",
                action=(
                    "Define a clear analytical objective. "
                    "For supervised learning, identify a suitable "
                    "target variable. For clustering, investigate "
                    "whether meaningful groups may exist."
                ),
                affected_columns=(
                    numeric_columns + categorical_columns
                ),
            )
        )

    if not numeric_columns:
        recommendations.append(
            create_recommendation(
                title="Review Numerical Feature Availability",
                description=(
                    "No numerical columns were identified."
                ),
                category="Machine Learning",
                priority="Low",
                action=(
                    "Check whether numeric variables are stored "
                    "as text and convert them where appropriate."
                ),
            )
        )

    return recommendations


# ==================================================
# GENERATE ALL RECOMMENDATIONS
# ==================================================

def generate_all_recommendations(data):
    """
    Generate recommendations across all supported categories.

    Returns a list sorted by priority.
    """

    validate_dataframe(data)

    recommendations = []

    recommendation_functions = [
        recommend_data_quality,
        recommend_numerical_analysis,
        recommend_correlations,
        recommend_categorical_analysis,
        recommend_date_analysis,
        recommend_dataset_structure,
        recommend_machine_learning,
    ]

    for function in recommendation_functions:

        try:
            recommendations.extend(
                function(data)
            )

        except (
            ValueError,
            TypeError,
            KeyError,
            ZeroDivisionError,
        ):
            # A failure in one recommendation category
            # should not prevent other categories from running.
            continue

    recommendations.sort(
        key=lambda item: (
            PRIORITY_ORDER.get(
                item["priority"],
                99
            ),
            item["category"],
            item["title"],
        )
    )

    return recommendations


# ==================================================
# RECOMMENDATION SUMMARY
# ==================================================

def summarize_recommendations(recommendations):
    """Calculate recommendation totals and priority counts."""

    if not isinstance(recommendations, list):
        raise TypeError(
            "Recommendations must be a list."
        )

    total = len(recommendations)

    high = sum(
        item.get("priority") == "High"
        for item in recommendations
    )

    medium = sum(
        item.get("priority") == "Medium"
        for item in recommendations
    )

    low = sum(
        item.get("priority") == "Low"
        for item in recommendations
    )

    categories = {}

    for item in recommendations:

        category = item.get(
            "category",
            "Other"
        )

        categories[category] = (
            categories.get(category, 0) + 1
        )

    return {
        "total": total,
        "high_priority": high,
        "medium_priority": medium,
        "low_priority": low,
        "categories": categories,
    }


# ==================================================
# FILTER RECOMMENDATIONS
# ==================================================

def filter_recommendations(
    recommendations,
    priority=None,
    category=None,
):
    """Filter recommendations by priority and category."""

    filtered = recommendations.copy()

    if priority:

        filtered = [
            item
            for item in filtered
            if item.get("priority") == priority
        ]

    if category:

        filtered = [
            item
            for item in filtered
            if item.get("category") == category
        ]

    return filtered


# ==================================================
# CONVERT TO DATAFRAME
# ==================================================

def recommendations_to_dataframe(recommendations):
    """Convert recommendations into a tabular report."""

    if not isinstance(recommendations, list):
        raise TypeError(
            "Recommendations must be a list."
        )

    rows = []

    for item in recommendations:

        rows.append({
            "Title": item.get("title"),
            "Description": item.get("description"),
            "Category": item.get("category"),
            "Priority": item.get("priority"),
            "Recommended Action": item.get("action"),
            "Affected Columns": ", ".join(
                item.get("affected_columns", [])
            ),
        })

    return pd.DataFrame(
        rows,
        columns=[
            "Title",
            "Description",
            "Category",
            "Priority",
            "Recommended Action",
            "Affected Columns",
        ],
    )


# ==================================================
# EXPORT RECOMMENDATIONS
# ==================================================

def export_recommendations(
    recommendations,
    file_path,
):
    """Export recommendations to CSV."""

    report = recommendations_to_dataframe(
        recommendations
    )

    if report.empty:
        raise ValueError(
            "There are no recommendations to export."
        )

    report.to_csv(
        file_path,
        index=False
    )

    return str(file_path)