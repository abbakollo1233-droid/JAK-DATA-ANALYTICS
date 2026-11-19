"""
JAK Health Intelligence
Medical Data Validation Engine

Validates medical information before analysis or prediction.

This module does not diagnose diseases.
It checks data quality and basic input validity.
"""

import math
import pandas as pd


# ==========================================
# FIELD VALIDATION RULES
# ==========================================

FIELD_RULES = {

    "age": {
        "minimum": 0,
        "maximum": 120,
    },

    "weight": {
        "minimum": 1,
        "maximum": 500,
    },

    "height": {
        "minimum": 0.3,
        "maximum": 2.8,
    },

    "bmi": {
        "minimum": 5,
        "maximum": 100,
    },

    "glucose": {
        "minimum": 0,
        "maximum": 2000,
    },

    "systolic_pressure": {
        "minimum": 40,
        "maximum": 300,
    },

    "diastolic_pressure": {
        "minimum": 20,
        "maximum": 200,
    },

    "blood_pressure": {
        "minimum": 20,
        "maximum": 300,
    },

    "heart_rate": {
        "minimum": 20,
        "maximum": 300,
    },

    "temperature": {
        "minimum": 25,
        "maximum": 45,
    },

    "oxygen_saturation": {
        "minimum": 0,
        "maximum": 100,
    },

    "cholesterol": {
        "minimum": 0,
        "maximum": 2000,
    },

    "creatinine": {
        "minimum": 0,
        "maximum": 100,
    },

    "blood_urea": {
        "minimum": 0,
        "maximum": 1000,
    },

    "haemoglobin": {
        "minimum": 0,
        "maximum": 30,
    },

    "haematocrit": {
        "minimum": 0,
        "maximum": 100,
    },

    "mcv": {
        "minimum": 0,
        "maximum": 200,
    },

    "ferritin": {
        "minimum": 0,
        "maximum": 100000,
    },

    "alt": {
        "minimum": 0,
        "maximum": 100000,
    },

    "ast": {
        "minimum": 0,
        "maximum": 100000,
    },

    "bilirubin": {
        "minimum": 0,
        "maximum": 1000,
    },

    "albumin": {
        "minimum": 0,
        "maximum": 100,
    },

    "hdl": {
        "minimum": 0,
        "maximum": 1000,
    },

    "triglycerides": {
        "minimum": 0,
        "maximum": 10000,
    },

    "psa": {
        "minimum": 0,
        "maximum": 100000,
    },

    "intraocular_pressure": {
        "minimum": 0,
        "maximum": 100,
    },

    "gestational_age": {
        "minimum": 0,
        "maximum": 45,
    },

    "egfr": {
        "minimum": 0,
        "maximum": 250,
    },

    "waist_circumference": {
        "minimum": 10,
        "maximum": 300,
    },
}


# ==========================================
# BASIC VALIDATION
# ==========================================

def is_missing(value):
    """Check whether a value is missing."""

    if value is None:
        return True

    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def validate_numeric_value(field, value):
    """
    Validate a numeric medical measurement.

    Returns:
        (is_valid, error_message)
    """

    if is_missing(value):
        return False, f"{field} is required."

    try:
        number = float(value)
    except (TypeError, ValueError):
        return False, f"{field} must be a valid number."

    if not math.isfinite(number):
        return False, f"{field} must be a finite number."

    rule = FIELD_RULES.get(field)

    if rule is None:
        return True, None

    minimum = rule["minimum"]
    maximum = rule["maximum"]

    if number < minimum:
        return (
            False,
            f"{field} must not be below {minimum}."
        )

    if number > maximum:
        return (
            False,
            f"{field} must not exceed {maximum}."
        )

    return True, None


# ==========================================
# BLOOD PRESSURE VALIDATION
# ==========================================

def validate_blood_pressure(systolic, diastolic):
    """Validate systolic and diastolic blood pressure."""

    errors = []

    systolic_valid, systolic_error = validate_numeric_value(
        "systolic_pressure",
        systolic,
    )

    diastolic_valid, diastolic_error = validate_numeric_value(
        "diastolic_pressure",
        diastolic,
    )

    if not systolic_valid:
        errors.append(systolic_error)

    if not diastolic_valid:
        errors.append(diastolic_error)

    if not systolic_valid or not diastolic_valid:
        return errors

    systolic = float(systolic)
    diastolic = float(diastolic)

    if systolic <= diastolic:
        errors.append(
            "Systolic pressure must be greater than diastolic pressure."
        )

    return errors


# ==========================================
# BMI CALCULATION
# ==========================================

def calculate_bmi(weight_kg, height_metres):
    """
    Calculate Body Mass Index.

    Weight must be in kilograms.
    Height must be in metres.
    """

    weight_valid, weight_error = validate_numeric_value(
        "weight",
        weight_kg,
    )

    height_valid, height_error = validate_numeric_value(
        "height",
        height_metres,
    )

    if not weight_valid:
        raise ValueError(weight_error)

    if not height_valid:
        raise ValueError(height_error)

    weight = float(weight_kg)
    height = float(height_metres)

    return round(weight / (height ** 2), 2)


# ==========================================
# REQUIRED FIELD VALIDATION
# ==========================================

def validate_required_fields(data, required_fields):
    """
    Check whether all required medical fields are present.

    data may be a dictionary or pandas Series.
    """

    if isinstance(data, pd.Series):
        data = data.to_dict()

    if not isinstance(data, dict):
        raise TypeError(
            "Medical information must be a dictionary or pandas Series."
        )

    errors = []

    for field in required_fields:

        if field not in data:
            errors.append(f"Missing required field: {field}.")
            continue

        if is_missing(data[field]):
            errors.append(f"{field} cannot be empty.")

    return errors


# ==========================================
# COMPLETE RECORD VALIDATION
# ==========================================

def validate_medical_record(data, required_fields=None):
    """
    Validate one medical record.

    Returns a dictionary containing:
    - valid
    - errors
    - warnings
    """

    if isinstance(data, pd.Series):
        data = data.to_dict()

    if not isinstance(data, dict):
        raise TypeError(
            "Medical record must be a dictionary or pandas Series."
        )

    errors = []
    warnings = []

    if required_fields is None:
        required_fields = []

    errors.extend(
        validate_required_fields(data, required_fields)
    )

    # Validate recognised numeric fields.

    for field, value in data.items():

        if field not in FIELD_RULES:
            continue

        if is_missing(value):
            continue

        valid, error = validate_numeric_value(
            field,
            value,
        )

        if not valid:
            errors.append(error)

    # Validate blood pressure relationship.

    if (
        "systolic_pressure" in data
        and "diastolic_pressure" in data
    ):
        if (
            not is_missing(data["systolic_pressure"])
            and not is_missing(data["diastolic_pressure"])
        ):
            errors.extend(
                validate_blood_pressure(
                    data["systolic_pressure"],
                    data["diastolic_pressure"],
                )
            )

    # Clinical caution messages.

    if "age" in data and not is_missing(data["age"]):
        try:
            age = float(data["age"])

            if age < 18:
                warnings.append(
                    "This record concerns a person under 18. "
                    "Adult prediction models may not be appropriate."
                )

        except (TypeError, ValueError):
            pass

    if "temperature" in data and not is_missing(data["temperature"]):
        try:
            temperature = float(data["temperature"])

            if temperature >= 40:
                warnings.append(
                    "Very high temperature recorded. "
                    "Prompt medical assessment may be necessary."
                )

        except (TypeError, ValueError):
            pass

    return {
        "valid": len(errors) == 0,
        "errors": list(dict.fromkeys(errors)),
        "warnings": list(dict.fromkeys(warnings)),
    }


# ==========================================
# DATASET VALIDATION
# ==========================================

def validate_medical_dataset(
    dataframe,
    required_fields=None,
):
    """
    Validate a medical dataset.

    Returns:
        summary
        row_errors
        missing_values
        invalid_rows
    """

    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError(
            "Expected a pandas DataFrame."
        )

    if dataframe.empty:
        raise ValueError(
            "The medical dataset is empty."
        )

    required_fields = required_fields or []

    errors = []

    # Check required columns.

    missing_columns = [
        field
        for field in required_fields
        if field not in dataframe.columns
    ]

    if missing_columns:
        errors.extend([
            f"Required column is missing: {column}"
            for column in missing_columns
        ])

    if errors:
        return {
            "valid": False,
            "summary": {
                "total_rows": len(dataframe),
                "total_columns": len(dataframe.columns),
                "invalid_rows": len(dataframe),
                "missing_values": int(
                    dataframe.isna().sum().sum()
                ),
            },
            "row_errors": [],
            "column_errors": errors,
        }

    row_errors = []

    # Validate each record.

    for index, row in dataframe.iterrows():

        result = validate_medical_record(
            row,
            required_fields,
        )

        if not result["valid"]:

            row_errors.append({
                "row": index,
                "errors": result["errors"],
            })

    missing_values = (
        dataframe.isna()
        .sum()
        .to_dict()
    )

    invalid_rows = len(row_errors)

    total_missing = int(
        dataframe.isna().sum().sum()
    )

    return {
        "valid": invalid_rows == 0 and total_missing == 0,
        "summary": {
            "total_rows": len(dataframe),
            "total_columns": len(dataframe.columns),
            "invalid_rows": invalid_rows,
            "missing_values": total_missing,
        },
        "row_errors": row_errors,
        "missing_values": missing_values,
        "column_errors": [],
    }


# ==========================================
# VALIDATION REPORT
# ==========================================

def generate_validation_report(result):
    """Generate a readable medical data validation report."""

    if not isinstance(result, dict):
        raise TypeError(
            "Validation result must be a dictionary."
        )

    lines = []

    lines.append(
        "JAK HEALTH INTELLIGENCE"
    )

    lines.append(
        "MEDICAL DATA VALIDATION REPORT"
    )

    lines.append("=" * 45)

    lines.append(
        f"Validation status: "
        f"{'VALID' if result.get('valid') else 'INVALID'}"
    )

    summary = result.get("summary", {})

    for key, value in summary.items():
        lines.append(
            f"{key.replace('_', ' ').title()}: {value}"
        )

    lines.append("")
    lines.append("VALIDATION ERRORS")

    column_errors = result.get(
        "column_errors",
        [],
    )

    for error in column_errors:
        lines.append(f"- {error}")

    for row in result.get("row_errors", []):
        lines.append(
            f"Row {row['row']}: "
            + "; ".join(row["errors"])
        )

    if not column_errors and not result.get("row_errors"):
        lines.append("No validation errors found.")

    lines.append("")
    lines.append(
        "This report checks data quality only. "
        "It does not provide a medical diagnosis."
    )

    return "\n".join(lines)