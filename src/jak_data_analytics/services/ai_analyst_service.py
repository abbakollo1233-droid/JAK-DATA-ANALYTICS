"""
JAK Data Analytics
AI Data Analyst Service

Provides natural-language dataset analysis.

Current capabilities:
- Dataset summaries
- Missing-value analysis
- Duplicate detection
- Numerical statistics
- Highest and lowest values
- Category analysis
- Group comparisons
- Correlation analysis
- Automatic question interpretation

This is a rule-based foundation.
A generative AI provider can be integrated later.
"""

import re
import pandas as pd
import numpy as np


# ---------------------------------------------------------
# DATA VALIDATION
# ---------------------------------------------------------

def validate_analyst_dataset(data):
    """
    Validate a dataset before analysis.
    """

    if not isinstance(data, pd.DataFrame):
        return False, "Please provide a valid Pandas DataFrame."

    if data.empty:
        return False, "The selected dataset is empty."

    if len(data.columns) == 0:
        return False, "The dataset has no columns."

    return True, None


# ---------------------------------------------------------
# COLUMN DETECTION
# ---------------------------------------------------------

def find_column(data, question):
    """
    Identify a dataset column mentioned in a question.
    """

    question = str(question).lower()

    for column in data.columns:

        column_name = str(column).strip().lower()

        if not column_name:
            continue

        pattern = (
            r"(?<![a-zA-Z0-9_])"
            + re.escape(column_name)
            + r"(?![a-zA-Z0-9_])"
        )

        if re.search(pattern, question):
            return column

    return None


def get_numeric_columns(data):
    """
    Return numerical columns.
    """

    return data.select_dtypes(
        include="number"
    ).columns.tolist()


def get_categorical_columns(data):
    """
    Return categorical columns.
    """

    return data.select_dtypes(
        include=["object", "category", "string", "bool"]
    ).columns.tolist()


# ---------------------------------------------------------
# DATASET OVERVIEW
# ---------------------------------------------------------

def analyse_dataset_overview(data):
    """
    Generate a general dataset summary.
    """

    is_valid, error = validate_analyst_dataset(data)

    if not is_valid:
        raise ValueError(error)

    return {
        "total_rows": int(data.shape[0]),
        "total_columns": int(data.shape[1]),
        "total_cells": int(data.size),
        "numeric_columns": get_numeric_columns(data),
        "categorical_columns": get_categorical_columns(data),
        "missing_values": int(data.isna().sum().sum()),
        "duplicate_rows": int(data.duplicated().sum()),
        "memory_usage_mb": round(
            data.memory_usage(deep=True).sum() / (1024 ** 2),
            3,
        ),
    }


# ---------------------------------------------------------
# AUTOMATIC DATASET SUMMARY
# ---------------------------------------------------------

def generate_dataset_summary(data):
    """
    Generate a readable summary of a dataset.
    """

    overview = analyse_dataset_overview(data)

    numeric_columns = overview["numeric_columns"]
    categorical_columns = overview["categorical_columns"]

    summary = [
        f"The dataset contains {overview['total_rows']:,} rows "
        f"and {overview['total_columns']:,} columns.",
        f"It contains {overview['missing_values']:,} missing values.",
        f"It contains {overview['duplicate_rows']:,} duplicate rows.",
        f"There are {len(numeric_columns)} numerical columns "
        f"and {len(categorical_columns)} categorical columns.",
    ]

    if numeric_columns:
        summary.append(
            "Numerical columns: "
            + ", ".join(map(str, numeric_columns))
            + "."
        )

    if categorical_columns:
        summary.append(
            "Categorical columns: "
            + ", ".join(map(str, categorical_columns))
            + "."
        )

    return " ".join(summary)


# ---------------------------------------------------------
# MISSING VALUE ANALYSIS
# ---------------------------------------------------------

def analyse_missing_values(data):
    """
    Analyse missing values by column.
    """

    missing_count = data.isna().sum()

    result = pd.DataFrame({
        "Column": missing_count.index,
        "Missing Values": missing_count.values,
        "Missing Percentage": (
            missing_count.values / len(data)
        ) * 100,
    })

    result = result.sort_values(
        "Missing Values",
        ascending=False,
    )

    return result.reset_index(drop=True)


# ---------------------------------------------------------
# DUPLICATE ANALYSIS
# ---------------------------------------------------------

def analyse_duplicates(data):
    """
    Analyse duplicate records.
    """

    duplicate_count = int(data.duplicated().sum())

    duplicate_percentage = (
        duplicate_count / len(data)
    ) * 100 if len(data) else 0

    return {
        "duplicate_count": duplicate_count,
        "duplicate_percentage": round(
            duplicate_percentage,
            2,
        ),
        "unique_rows": int(
            len(data) - duplicate_count
        ),
    }


# ---------------------------------------------------------
# NUMERICAL ANALYSIS
# ---------------------------------------------------------

def analyse_numeric_column(data, column):
    """
    Calculate statistics for a numerical column.
    """

    if column not in data.columns:
        raise ValueError("Column not found.")

    if not pd.api.types.is_numeric_dtype(data[column]):
        raise ValueError("Selected column is not numerical.")

    values = pd.to_numeric(
        data[column],
        errors="coerce",
    ).dropna()

    if values.empty:
        raise ValueError(
            "The selected column contains no valid numerical values."
        )

    return {
        "column": str(column),
        "count": int(values.count()),
        "mean": float(values.mean()),
        "median": float(values.median()),
        "minimum": float(values.min()),
        "maximum": float(values.max()),
        "standard_deviation": float(values.std()),
        "sum": float(values.sum()),
        "variance": float(values.var()),
    }


# ---------------------------------------------------------
# HIGHEST AND LOWEST RECORDS
# ---------------------------------------------------------

def get_ranked_records(
    data,
    column,
    ascending=False,
    limit=10,
):
    """
    Return records ranked by a numerical column.
    """

    if column not in data.columns:
        raise ValueError("Column not found.")

    if not pd.api.types.is_numeric_dtype(data[column]):
        raise ValueError("Ranking requires a numerical column.")

    limit = max(1, min(int(limit), 100))

    result = data.copy()

    result[column] = pd.to_numeric(
        result[column],
        errors="coerce",
    )

    result = result.dropna(subset=[column])

    return result.sort_values(
        column,
        ascending=ascending,
    ).head(limit)


# ---------------------------------------------------------
# CATEGORY ANALYSIS
# ---------------------------------------------------------

def analyse_category(data, column, limit=10):
    """
    Analyse the most frequent values in a categorical column.
    """

    if column not in data.columns:
        raise ValueError("Column not found.")

    limit = max(1, min(int(limit), 100))

    frequencies = (
        data[column]
        .value_counts(dropna=False)
        .head(limit)
    )

    result = pd.DataFrame({
        "Category": frequencies.index.astype(str),
        "Count": frequencies.values,
    })

    return result


# ---------------------------------------------------------
# GROUP ANALYSIS
# ---------------------------------------------------------

def analyse_groups(data, group_column, numeric_column):
    """
    Compare a numerical metric across groups.
    """

    if group_column not in data.columns:
        raise ValueError("Group column not found.")

    if numeric_column not in data.columns:
        raise ValueError("Numerical column not found.")

    if not pd.api.types.is_numeric_dtype(
        data[numeric_column]
    ):
        raise ValueError(
            "The metric column must be numerical."
        )

    result = (
        data.groupby(
            group_column,
            dropna=False,
        )[numeric_column]
        .agg(["count", "mean", "median", "min", "max", "sum"])
        .reset_index()
    )

    result = result.sort_values(
        "mean",
        ascending=False,
    )

    return result


# ---------------------------------------------------------
# CORRELATION ANALYSIS
# ---------------------------------------------------------

def analyse_correlations(data, method="pearson"):
    """
    Calculate numerical correlations.
    """

    numeric_data = data.select_dtypes(
        include="number"
    )

    if numeric_data.shape[1] < 2:
        raise ValueError(
            "At least two numerical columns are required."
        )

    if method not in {"pearson", "spearman", "kendall"}:
        raise ValueError(
            "Choose Pearson, Spearman, or Kendall correlation."
        )

    return numeric_data.corr(
        method=method
    )


# ---------------------------------------------------------
# QUESTION INTENT DETECTION
# ---------------------------------------------------------

def detect_question_intent(question):
    """
    Identify the likely purpose of a natural-language question.
    """

    question = str(question).lower().strip()

    if any(word in question for word in [
        "missing",
        "null",
        "empty values",
        "blank values",
    ]):
        return "missing"

    if any(word in question for word in [
        "duplicate",
        "duplicated",
        "repeated records",
        "repeated rows",
    ]):
        return "duplicates"

    if any(word in question for word in [
        "correlation",
        "relationship between",
        "related to",
        "relationship of",
    ]):
        return "correlation"

    if any(word in question for word in [
        "highest",
        "largest",
        "maximum",
        "top",
        "best performing",
        "most profitable",
        "greatest",
    ]):
        return "highest"

    if any(word in question for word in [
        "lowest",
        "smallest",
        "minimum",
        "bottom",
        "least",
        "worst performing",
    ]):
        return "lowest"

    if any(word in question for word in [
        "average",
        "mean",
        "median",
        "maximum",
        "minimum",
        "standard deviation",
        "variance",
        "sum",
        "total",
        "statistics",
        "describe",
    ]):
        return "statistics"

    if any(word in question for word in [
        "department",
        "category",
        "group",
        "compare",
        "comparison",
        "per ",
        "by ",
    ]):
        return "group"

    if any(word in question for word in [
        "most common",
        "most frequent",
        "popular",
        "frequency",
        "distribution",
    ]):
        return "category"

    if any(word in question for word in [
        "summary",
        "overview",
        "describe dataset",
        "tell me about",
        "dataset information",
    ]):
        return "summary"

    return "unknown"


# ---------------------------------------------------------
# QUESTION INTERPRETATION
# ---------------------------------------------------------

def interpret_question(data, question):
    """
    Interpret a user's question and return an analysis result.

    Returns:
        dict containing:
            success
            intent
            answer
            data
            chart_type
    """

    is_valid, error = validate_analyst_dataset(data)

    if not is_valid:
        return {
            "success": False,
            "intent": "error",
            "answer": error,
            "data": None,
            "chart_type": None,
        }

    question = str(question or "").strip()

    if not question:
        return {
            "success": False,
            "intent": "error",
            "answer": "Please enter a question.",
            "data": None,
            "chart_type": None,
        }

    intent = detect_question_intent(question)

    column = find_column(data, question)

    try:

        # ---------------------------------------------
        # DATASET SUMMARY
        # ---------------------------------------------

        if intent == "summary":

            answer = generate_dataset_summary(data)

            return {
                "success": True,
                "intent": intent,
                "answer": answer,
                "data": analyse_dataset_overview(data),
                "chart_type": None,
            }

        # ---------------------------------------------
        # MISSING VALUES
        # ---------------------------------------------

        if intent == "missing":

            result = analyse_missing_values(data)

            total_missing = int(
                result["Missing Values"].sum()
            )

            answer = (
                f"Your dataset contains {total_missing:,} "
                "missing values across its columns."
            )

            return {
                "success": True,
                "intent": intent,
                "answer": answer,
                "data": result,
                "chart_type": "bar",
            }

        # ---------------------------------------------
        # DUPLICATES
        # ---------------------------------------------

        if intent == "duplicates":

            result = analyse_duplicates(data)

            answer = (
                f"Your dataset contains "
                f"{result['duplicate_count']:,} duplicate rows "
                f"({result['duplicate_percentage']}% of all rows)."
            )

            return {
                "success": True,
                "intent": intent,
                "answer": answer,
                "data": result,
                "chart_type": None,
            }

        # ---------------------------------------------
        # HIGHEST VALUES
        # ---------------------------------------------

        if intent == "highest":

            if column is None:
                numeric_columns = get_numeric_columns(data)

                if len(numeric_columns) == 1:
                    column = numeric_columns[0]

                else:
                    raise ValueError(
                        "Please mention the numerical column "
                        "you want to rank."
                    )

            result = get_ranked_records(
                data,
                column,
                ascending=False,
                limit=10,
            )

            answer = (
                f"Here are the 10 highest records "
                f"according to {column}."
            )

            return {
                "success": True,
                "intent": intent,
                "answer": answer,
                "data": result,
                "chart_type": "bar",
            }

        # ---------------------------------------------
        # LOWEST VALUES
        # ---------------------------------------------

        if intent == "lowest":

            if column is None:
                numeric_columns = get_numeric_columns(data)

                if len(numeric_columns) == 1:
                    column = numeric_columns[0]

                else:
                    raise ValueError(
                        "Please mention the numerical column "
                        "you want to rank."
                    )

            result = get_ranked_records(
                data,
                column,
                ascending=True,
                limit=10,
            )

            answer = (
                f"Here are the 10 lowest records "
                f"according to {column}."
            )

            return {
                "success": True,
                "intent": intent,
                "answer": answer,
                "data": result,
                "chart_type": "bar",
            }

        # ---------------------------------------------
        # NUMERICAL STATISTICS
        # ---------------------------------------------

        if intent == "statistics":

            if column is None:
                numeric_columns = get_numeric_columns(data)

                if len(numeric_columns) == 1:
                    column = numeric_columns[0]

                else:
                    raise ValueError(
                        "Please mention the numerical column "
                        "you want to analyse."
                    )

            result = analyse_numeric_column(
                data,
                column,
            )

            answer = (
                f"Statistical analysis for {column}: "
                f"Mean = {result['mean']:.2f}, "
                f"Median = {result['median']:.2f}, "
                f"Minimum = {result['minimum']:.2f}, "
                f"Maximum = {result['maximum']:.2f}, "
                f"Sum = {result['sum']:.2f}."
            )

            return {
                "success": True,
                "intent": intent,
                "answer": answer,
                "data": result,
                "chart_type": None,
            }

        # ---------------------------------------------
        # CATEGORY FREQUENCY
        # ---------------------------------------------

        if intent == "category":

            if column is None:
                categorical_columns = get_categorical_columns(data)

                if len(categorical_columns) == 1:
                    column = categorical_columns[0]

                else:
                    raise ValueError(
                        "Please mention the categorical column "
                        "you want to analyse."
                    )

            result = analyse_category(
                data,
                column,
                limit=10,
            )

            answer = (
                f"Here are the most frequent values "
                f"in {column}."
            )

            return {
                "success": True,
                "intent": intent,
                "answer": answer,
                "data": result,
                "chart_type": "bar",
            }

        # ---------------------------------------------
        # GROUP COMPARISON
        # ---------------------------------------------

        if intent == "group":

            numeric_columns = get_numeric_columns(data)
            categorical_columns = get_categorical_columns(data)

            if column in numeric_columns:
                numeric_column = column

                group_columns = [
                    item
                    for item in categorical_columns
                    if item in question.lower()
                ]

                if len(group_columns) == 1:
                    group_column = group_columns[0]

                elif len(categorical_columns) == 1:
                    group_column = categorical_columns[0]

                else:
                    raise ValueError(
                        "Please specify the group column "
                        "and numerical metric."
                    )

            elif column in categorical_columns:
                group_column = column

                mentioned_numeric = [
                    item
                    for item in numeric_columns
                    if str(item).lower() in question.lower()
                ]

                if len(mentioned_numeric) == 1:
                    numeric_column = mentioned_numeric[0]

                elif len(numeric_columns) == 1:
                    numeric_column = numeric_columns[0]

                else:
                    raise ValueError(
                        "Please specify the numerical metric "
                        "you want to compare."
                    )

            else:
                raise ValueError(
                    "Please specify a group column."
                )

            result = analyse_groups(
                data,
                group_column,
                numeric_column,
            )

            answer = (
                f"Here is the comparison of {numeric_column} "
                f"across {group_column}."
            )

            return {
                "success": True,
                "intent": intent,
                "answer": answer,
                "data": result,
                "chart_type": "bar",
            }

        # ---------------------------------------------
        # CORRELATION
        # ---------------------------------------------

        if intent == "correlation":

            result = analyse_correlations(data)

            answer = (
                "Here is the Pearson correlation matrix "
                "for the numerical columns in your dataset. "
                "Correlation indicates association, not causation."
            )

            return {
                "success": True,
                "intent": intent,
                "answer": answer,
                "data": result,
                "chart_type": "heatmap",
            }

        # ---------------------------------------------
        # UNKNOWN QUESTION
        # ---------------------------------------------

        return {
            "success": False,
            "intent": "unknown",
            "answer": (
                "I could not identify what you want to analyse. "
                "Try asking about missing values, duplicates, "
                "statistics, highest values, lowest values, "
                "categories, group comparisons, correlations, "
                "or a dataset summary."
            ),
            "data": None,
            "chart_type": None,
        }

    except (ValueError, TypeError, KeyError, ZeroDivisionError) as error:

        return {
            "success": False,
            "intent": intent,
            "answer": str(error),
            "data": None,
            "chart_type": None,
        }


# ---------------------------------------------------------
# SUGGESTED QUESTIONS
# ---------------------------------------------------------

def generate_suggested_questions(data):
    """
    Generate example questions based on available columns.
    """

    is_valid, error = validate_analyst_dataset(data)

    if not is_valid:
        return []

    suggestions = [
        "Give me a summary of this dataset.",
        "How many missing values are there?",
        "Are there duplicate records?",
    ]

    numeric_columns = get_numeric_columns(data)
    categorical_columns = get_categorical_columns(data)

    if numeric_columns:

        column = numeric_columns[0]

        suggestions.extend([
            f"What is the average {column}?",
            f"Show the highest {column} values.",
            f"Show the lowest {column} values.",
        ])

    if categorical_columns:

        column = categorical_columns[0]

        suggestions.append(
            f"Which {column} is most frequent?"
        )

    if len(numeric_columns) >= 2:

        suggestions.append(
            "Show the correlation between numerical columns."
        )

    if numeric_columns and categorical_columns:

        suggestions.append(
            f"Compare {numeric_columns[0]} by {categorical_columns[0]}."
        )

    return suggestions
