"""
JAK Data Analytics
Data Validation Service

Provides configurable dataset validation.

Supported validation rules:
- Required columns
- Missing values
- Unique values
- Numeric ranges
- Allowed values
- Text length
- Regular expression patterns
- Email validation
- Date validation
- Duplicate records
- Custom column types

This service is independent of Streamlit.
"""

import re
import pandas as pd
import numpy as np


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

SUPPORTED_RULES = {
    "required",
    "not_null",
    "unique",
    "numeric_range",
    "allowed_values",
    "text_length",
    "regex",
    "email",
    "valid_date",
    "data_type",
}

SUPPORTED_DATA_TYPES = {
    "integer",
    "float",
    "numeric",
    "string",
    "boolean",
    "datetime",
}


# ---------------------------------------------------------
# GENERAL VALIDATION
# ---------------------------------------------------------

def validate_dataframe(data):
    """Validate the input dataset."""

    if not isinstance(data, pd.DataFrame):
        raise ValueError(
            "Input must be a Pandas DataFrame."
        )

    if data.empty:
        raise ValueError(
            "The dataset is empty."
        )

    if data.columns.duplicated().any():
        raise ValueError(
            "The dataset contains duplicate column names."
        )

    return True


def validate_rule_definition(rule):
    """Validate a single rule definition."""

    if not isinstance(rule, dict):
        raise ValueError(
            "Each validation rule must be a dictionary."
        )

    rule_type = rule.get("rule")

    if rule_type not in SUPPORTED_RULES:
        raise ValueError(
            f"Unsupported validation rule: {rule_type}"
        )

    if rule_type != "required" and not rule.get("column"):
        raise ValueError(
            f"The {rule_type} rule requires a column."
        )

    if rule_type == "numeric_range":

        if "min" not in rule and "max" not in rule:
            raise ValueError(
                "Numeric range requires a minimum or maximum."
            )

        if (
            rule.get("min") is not None
            and rule.get("max") is not None
            and rule["min"] > rule["max"]
        ):
            raise ValueError(
                "Minimum value cannot exceed maximum value."
            )

    if rule_type == "allowed_values":

        if not isinstance(rule.get("values"), list):
            raise ValueError(
                "Allowed values must be provided as a list."
            )

    if rule_type == "text_length":

        if (
            rule.get("min") is None
            and rule.get("max") is None
        ):
            raise ValueError(
                "Text length requires a minimum or maximum."
            )

    if rule_type == "regex":

        pattern = rule.get("pattern")

        if not pattern:
            raise ValueError(
                "A regular expression pattern is required."
            )

        try:
            re.compile(pattern)
        except re.error as error:
            raise ValueError(
                f"Invalid regular expression: {error}"
            )

    if rule_type == "data_type":

        expected_type = rule.get("expected_type")

        if expected_type not in SUPPORTED_DATA_TYPES:
            raise ValueError(
                "Unsupported expected data type."
            )

    return True


def validate_rules(rules):
    """Validate a complete collection of rules."""

    if not isinstance(rules, list):
        raise ValueError(
            "Rules must be provided as a list."
        )

    for rule in rules:
        validate_rule_definition(rule)

    return True


# ---------------------------------------------------------
# COLUMN CHECKS
# ---------------------------------------------------------

def validate_required_columns(data, columns):
    """Check whether required columns exist."""

    if isinstance(columns, str):
        columns = [columns]

    missing = [
        column
        for column in columns
        if column not in data.columns
    ]

    return {
        "rule": "required",
        "passed": len(missing) == 0,
        "checked": len(columns),
        "failed": len(missing),
        "message": (
            "All required columns exist."
            if not missing
            else f"Missing columns: {missing}"
        ),
        "details": missing,
    }


def validate_not_null(data, column):
    """Check for missing values in a column."""

    if column not in data.columns:
        raise ValueError(
            f"Column not found: {column}"
        )

    missing_mask = data[column].isna()

    failed_rows = data.index[missing_mask].tolist()

    return {
        "rule": "not_null",
        "column": column,
        "passed": len(failed_rows) == 0,
        "checked": len(data),
        "failed": len(failed_rows),
        "message": (
            "No missing values found."
            if not failed_rows
            else f"{len(failed_rows)} missing values found."
        ),
        "details": failed_rows[:100],
    }


def validate_unique(data, column):
    """Check whether all non-missing values are unique."""

    if column not in data.columns:
        raise ValueError(
            f"Column not found: {column}"
        )

    duplicate_mask = (
        data[column].notna()
        & data[column].duplicated(keep=False)
    )

    failed_rows = data.index[
        duplicate_mask
    ].tolist()

    return {
        "rule": "unique",
        "column": column,
        "passed": len(failed_rows) == 0,
        "checked": int(data[column].notna().sum()),
        "failed": len(failed_rows),
        "message": (
            "All non-missing values are unique."
            if not failed_rows
            else f"{len(failed_rows)} duplicate-value rows found."
        ),
        "details": failed_rows[:100],
    }


# ---------------------------------------------------------
# NUMERIC VALIDATION
# ---------------------------------------------------------

def validate_numeric_range(
    data,
    column,
    minimum=None,
    maximum=None,
):
    """Check whether numeric values are within a range."""

    if column not in data.columns:
        raise ValueError(
            f"Column not found: {column}"
        )

    numeric = pd.to_numeric(
        data[column],
        errors="coerce",
    )

    invalid_mask = (
        data[column].notna()
        & numeric.isna()
    )

    invalid_mask |= (
        numeric.notna()
        & ~np.isfinite(numeric)
    )

    if minimum is not None:
        invalid_mask |= (
            numeric.notna()
            & (numeric < minimum)
        )

    if maximum is not None:
        invalid_mask |= (
            numeric.notna()
            & (numeric > maximum)
        )

    failed_rows = data.index[
        invalid_mask
    ].tolist()

    return {
        "rule": "numeric_range",
        "column": column,
        "passed": len(failed_rows) == 0,
        "checked": len(data),
        "failed": len(failed_rows),
        "message": (
            "All values satisfy the numeric range."
            if not failed_rows
            else f"{len(failed_rows)} invalid numeric values found."
        ),
        "details": failed_rows[:100],
    }


# ---------------------------------------------------------
# ALLOWED VALUES
# ---------------------------------------------------------

def validate_allowed_values(
    data,
    column,
    allowed_values,
    case_sensitive=True,
):
    """Check whether values belong to an approved list."""

    if column not in data.columns:
        raise ValueError(
            f"Column not found: {column}"
        )

    if case_sensitive:
        valid_mask = data[column].isin(
            allowed_values
        )

    else:
        allowed_normalized = {
            str(value).casefold()
            for value in allowed_values
        }

        valid_mask = data[column].map(
            lambda value: (
                False
                if pd.isna(value)
                else str(value).casefold()
                in allowed_normalized
            )
        )

    invalid_mask = (
        data[column].notna()
        & ~valid_mask
    )

    failed_rows = data.index[
        invalid_mask
    ].tolist()

    return {
        "rule": "allowed_values",
        "column": column,
        "passed": len(failed_rows) == 0,
        "checked": int(data[column].notna().sum()),
        "failed": len(failed_rows),
        "message": (
            "All values belong to the approved list."
            if not failed_rows
            else f"{len(failed_rows)} unapproved values found."
        ),
        "details": failed_rows[:100],
    }


# ---------------------------------------------------------
# TEXT VALIDATION
# ---------------------------------------------------------

def validate_text_length(
    data,
    column,
    minimum=None,
    maximum=None,
):
    """Validate the length of text values."""

    if column not in data.columns:
        raise ValueError(
            f"Column not found: {column}"
        )

    text = data[column].astype("string")

    lengths = text.str.len()

    invalid_mask = pd.Series(
        False,
        index=data.index,
    )

    if minimum is not None:
        invalid_mask |= (
            lengths.notna()
            & (lengths < minimum)
        )

    if maximum is not None:
        invalid_mask |= (
            lengths.notna()
            & (lengths > maximum)
        )

    failed_rows = data.index[
        invalid_mask
    ].tolist()

    return {
        "rule": "text_length",
        "column": column,
        "passed": len(failed_rows) == 0,
        "checked": int(text.notna().sum()),
        "failed": len(failed_rows),
        "message": (
            "All text lengths are valid."
            if not failed_rows
            else f"{len(failed_rows)} invalid text lengths found."
        ),
        "details": failed_rows[:100],
    }


def validate_regex(
    data,
    column,
    pattern,
):
    """Validate text values against a regex pattern."""

    if column not in data.columns:
        raise ValueError(
            f"Column not found: {column}"
        )

    compiled = re.compile(pattern)

    def matches(value):

        if pd.isna(value):
            return True

        return bool(
            compiled.fullmatch(str(value))
        )

    valid_mask = data[column].map(matches)

    invalid_mask = (
        data[column].notna()
        & ~valid_mask
    )

    failed_rows = data.index[
        invalid_mask
    ].tolist()

    return {
        "rule": "regex",
        "column": column,
        "passed": len(failed_rows) == 0,
        "checked": int(data[column].notna().sum()),
        "failed": len(failed_rows),
        "message": (
            "All values match the required pattern."
            if not failed_rows
            else f"{len(failed_rows)} pattern mismatches found."
        ),
        "details": failed_rows[:100],
    }


# ---------------------------------------------------------
# EMAIL VALIDATION
# ---------------------------------------------------------

def validate_email_addresses(data, column):
    """Check basic email address formatting."""

    pattern = (
        r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"
    )

    return validate_regex(
        data,
        column,
        pattern,
    )


# ---------------------------------------------------------
# DATE VALIDATION
# ---------------------------------------------------------

def validate_dates(data, column):
    """Check whether non-missing values can be parsed as dates."""

    if column not in data.columns:
        raise ValueError(
            f"Column not found: {column}"
        )

    parsed = pd.to_datetime(
        data[column],
        errors="coerce",
    )

    invalid_mask = (
        data[column].notna()
        & parsed.isna()
    )

    failed_rows = data.index[
        invalid_mask
    ].tolist()

    return {
        "rule": "valid_date",
        "column": column,
        "passed": len(failed_rows) == 0,
        "checked": int(data[column].notna().sum()),
        "failed": len(failed_rows),
        "message": (
            "All non-missing dates are valid."
            if not failed_rows
            else f"{len(failed_rows)} invalid dates found."
        ),
        "details": failed_rows[:100],
    }


# ---------------------------------------------------------
# DATA TYPE VALIDATION
# ---------------------------------------------------------

def validate_data_type(
    data,
    column,
    expected_type,
):
    """Check whether values can be interpreted as a data type."""

    if column not in data.columns:
        raise ValueError(
            f"Column not found: {column}"
        )

    series = data[column]
    non_missing = series.notna()

    if expected_type == "integer":

        converted = pd.to_numeric(
            series,
            errors="coerce",
        )

        valid = (
            converted.notna()
            & np.isfinite(converted)
            & (converted % 1 == 0)
        )

    elif expected_type in {"float", "numeric"}:

        converted = pd.to_numeric(
            series,
            errors="coerce",
        )

        valid = (
            converted.notna()
            & np.isfinite(converted)
        )

    elif expected_type == "string":

        valid = series.map(
            lambda value: isinstance(value, str)
            if not pd.isna(value)
            else True
        )

    elif expected_type == "boolean":

        valid_values = {
            "true",
            "false",
            "yes",
            "no",
            "1",
            "0",
        }

        valid = series.map(
            lambda value: (
                True
                if pd.isna(value)
                else (
                    isinstance(value, (bool, np.bool_))
                    or str(value).strip().lower()
                    in valid_values
                )
            )
        )

    elif expected_type == "datetime":

        converted = pd.to_datetime(
            series,
            errors="coerce",
        )

        valid = converted.notna()

    else:
        raise ValueError(
            "Unsupported expected data type."
        )

    invalid_mask = non_missing & ~valid

    failed_rows = data.index[
        invalid_mask
    ].tolist()

    return {
        "rule": "data_type",
        "column": column,
        "expected_type": expected_type,
        "passed": len(failed_rows) == 0,
        "checked": int(non_missing.sum()),
        "failed": len(failed_rows),
        "message": (
            f"All values match the {expected_type} type."
            if not failed_rows
            else f"{len(failed_rows)} incompatible values found."
        ),
        "details": failed_rows[:100],
    }


# ---------------------------------------------------------
# DUPLICATE RECORD VALIDATION
# ---------------------------------------------------------

def validate_duplicate_records(
    data,
    columns=None,
):
    """Check for duplicate records."""

    if columns is not None:

        if isinstance(columns, str):
            columns = [columns]

        missing = [
            column
            for column in columns
            if column not in data.columns
        ]

        if missing:
            raise ValueError(
                f"Columns not found: {missing}"
            )

    duplicate_mask = data.duplicated(
        subset=columns,
        keep=False,
    )

    failed_rows = data.index[
        duplicate_mask
    ].tolist()

    return {
        "rule": "duplicate_records",
        "passed": len(failed_rows) == 0,
        "checked": len(data),
        "failed": len(failed_rows),
        "message": (
            "No duplicate records found."
            if not failed_rows
            else f"{len(failed_rows)} duplicate-record rows found."
        ),
        "details": failed_rows[:100],
    }


# ---------------------------------------------------------
# RULE EXECUTION
# ---------------------------------------------------------

def execute_validation_rule(data, rule):
    """Execute one configured validation rule."""

    validate_rule_definition(rule)

    rule_type = rule["rule"]

    if rule_type == "required":

        return validate_required_columns(
            data,
            rule["columns"],
        )

    if rule_type == "not_null":

        return validate_not_null(
            data,
            rule["column"],
        )

    if rule_type == "unique":

        return validate_unique(
            data,
            rule["column"],
        )

    if rule_type == "numeric_range":

        return validate_numeric_range(
            data,
            rule["column"],
            minimum=rule.get("min"),
            maximum=rule.get("max"),
        )

    if rule_type == "allowed_values":

        return validate_allowed_values(
            data,
            rule["column"],
            rule["values"],
            case_sensitive=rule.get(
                "case_sensitive",
                True,
            ),
        )

    if rule_type == "text_length":

        return validate_text_length(
            data,
            rule["column"],
            minimum=rule.get("min"),
            maximum=rule.get("max"),
        )

    if rule_type == "regex":

        return validate_regex(
            data,
            rule["column"],
            rule["pattern"],
        )

    if rule_type == "email":

        return validate_email_addresses(
            data,
            rule["column"],
        )

    if rule_type == "valid_date":

        return validate_dates(
            data,
            rule["column"],
        )

    if rule_type == "data_type":

        return validate_data_type(
            data,
            rule["column"],
            rule["expected_type"],
        )

    raise ValueError(
        f"Unsupported rule: {rule_type}"
    )


# ---------------------------------------------------------
# COMPLETE VALIDATION
# ---------------------------------------------------------

def validate_dataset(data, rules):
    """
    Execute multiple validation rules.

    Returns:
        success
        total_rules
        passed_rules
        failed_rules
        validation_score
        results
    """

    validate_dataframe(data)
    validate_rules(rules)

    results = []

    for position, rule in enumerate(rules, start=1):

        try:

            result = execute_validation_rule(
                data,
                rule,
            )

            result["rule_number"] = position

        except Exception as error:

            result = {
                "rule": rule.get("rule", "unknown"),
                "column": rule.get("column"),
                "passed": False,
                "checked": 0,
                "failed": 0,
                "message": str(error),
                "details": [],
                "rule_number": position,
                "execution_error": True,
            }

        results.append(result)

    total_rules = len(results)

    passed_rules = sum(
        1
        for result in results
        if result["passed"]
    )

    failed_rules = total_rules - passed_rules

    validation_score = (
        round(
            passed_rules / total_rules * 100,
            2,
        )
        if total_rules
        else 100.0
    )

    return {
        "success": failed_rules == 0,
        "total_rules": total_rules,
        "passed_rules": passed_rules,
        "failed_rules": failed_rules,
        "validation_score": validation_score,
        "results": results,
    }


# ---------------------------------------------------------
# VALIDATION REPORT
# ---------------------------------------------------------

def generate_validation_report(validation_result):
    """Generate a tabular validation report."""

    if not isinstance(validation_result, dict):
        raise ValueError(
            "A valid validation result is required."
        )

    results = validation_result.get(
        "results",
        [],
    )

    records = []

    for result in results:

        records.append({
            "Rule Number": result.get("rule_number"),
            "Rule": result.get("rule"),
            "Column": result.get("column", ""),
            "Status": (
                "Passed"
                if result.get("passed")
                else "Failed"
            ),
            "Checked": result.get("checked", 0),
            "Failed": result.get("failed", 0),
            "Message": result.get("message", ""),
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------
# VALIDATION SUMMARY
# ---------------------------------------------------------

def get_validation_summary(validation_result):
    """Return a concise validation summary."""

    return {
        "success": validation_result.get("success", False),
        "total_rules": validation_result.get("total_rules", 0),
        "passed_rules": validation_result.get("passed_rules", 0),
        "failed_rules": validation_result.get("failed_rules", 0),
        "validation_score": validation_result.get(
            "validation_score",
            0,
        ),
        "status": (
            "Passed"
            if validation_result.get("success")
            else "Failed"
        ),
    }
