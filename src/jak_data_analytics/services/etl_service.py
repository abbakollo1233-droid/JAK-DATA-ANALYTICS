"""
JAK Data Analytics
ETL Workflow Service

Provides reusable Extract, Transform, Load functionality.

Supported operations:
- Rename columns
- Remove columns
- Remove duplicate records
- Handle missing values
- Convert data types
- Create calculated columns
- Filter records
- Sort records
- Clean text columns
- Extract date components
- Group and aggregate records

This service is independent of Streamlit.
"""

from copy import deepcopy
import operator

import numpy as np
import pandas as pd


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

SUPPORTED_OPERATIONS = {
    "rename_columns",
    "remove_columns",
    "remove_duplicates",
    "handle_missing",
    "convert_type",
    "calculate_column",
    "filter_rows",
    "sort_rows",
    "clean_text",
    "extract_date",
    "group_aggregate",
}

CALCULATION_OPERATORS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "**": operator.pow,
}

FILTER_OPERATORS = {
    "equals": operator.eq,
    "not_equals": operator.ne,
    "greater_than": operator.gt,
    "greater_than_or_equal": operator.ge,
    "less_than": operator.lt,
    "less_than_or_equal": operator.le,
}


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_dataframe(data):
    """
    Validate an input DataFrame.
    """

    if not isinstance(data, pd.DataFrame):
        raise ValueError("Input must be a Pandas DataFrame.")

    if data.empty:
        raise ValueError("The dataset is empty.")

    if data.columns.duplicated().any():
        raise ValueError("Duplicate column names are not allowed.")

    return True


def validate_workflow(workflow):
    """
    Validate an ETL workflow definition.

    Expected format:

    [
        {
            "operation": "rename_columns",
            "parameters": {
                "mapping": {
                    "old_name": "new_name"
                }
            }
        }
    ]
    """

    if not isinstance(workflow, list):
        raise ValueError("Workflow must be a list of steps.")

    if not workflow:
        raise ValueError("Workflow contains no steps.")

    for position, step in enumerate(workflow, start=1):

        if not isinstance(step, dict):
            raise ValueError(
                f"Step {position} must be a dictionary."
            )

        operation_name = step.get("operation")

        if operation_name not in SUPPORTED_OPERATIONS:
            raise ValueError(
                f"Unsupported operation in step {position}: "
                f"{operation_name}"
            )

        parameters = step.get("parameters", {})

        if not isinstance(parameters, dict):
            raise ValueError(
                f"Parameters for step {position} must be a dictionary."
            )

    return True


# ---------------------------------------------------------
# RENAME COLUMNS
# ---------------------------------------------------------

def rename_columns(data, mapping):
    """
    Rename dataset columns.
    """

    if not isinstance(mapping, dict) or not mapping:
        raise ValueError("A valid column mapping is required.")

    missing = [
        column
        for column in mapping
        if column not in data.columns
    ]

    if missing:
        raise ValueError(
            f"Columns not found: {missing}"
        )

    renamed = data.rename(columns=mapping)

    if renamed.columns.duplicated().any():
        raise ValueError(
            "Renaming would create duplicate column names."
        )

    return renamed


# ---------------------------------------------------------
# REMOVE COLUMNS
# ---------------------------------------------------------

def remove_columns(data, columns):
    """
    Remove selected columns.
    """

    if isinstance(columns, str):
        columns = [columns]

    if not isinstance(columns, list) or not columns:
        raise ValueError("Select at least one column to remove.")

    missing = [
        column
        for column in columns
        if column not in data.columns
    ]

    if missing:
        raise ValueError(
            f"Columns not found: {missing}"
        )

    if len(columns) >= len(data.columns):
        raise ValueError(
            "An ETL step cannot remove every column."
        )

    return data.drop(columns=columns)


# ---------------------------------------------------------
# REMOVE DUPLICATES
# ---------------------------------------------------------

def remove_duplicates(data, subset=None, keep="first"):
    """
    Remove duplicate records.
    """

    if keep not in {"first", "last", False}:
        raise ValueError(
            "Keep must be 'first', 'last', or False."
        )

    if subset is not None:

        if isinstance(subset, str):
            subset = [subset]

        missing = [
            column
            for column in subset
            if column not in data.columns
        ]

        if missing:
            raise ValueError(
                f"Columns not found: {missing}"
            )

    return data.drop_duplicates(
        subset=subset,
        keep=keep,
    )


# ---------------------------------------------------------
# HANDLE MISSING VALUES
# ---------------------------------------------------------

def handle_missing_values(
    data,
    columns,
    strategy="drop_rows",
    fill_value=None,
):
    """
    Handle missing values.

    Strategies:
        drop_rows
        drop_columns
        mean
        median
        mode
        constant
        forward_fill
        backward_fill
    """

    if isinstance(columns, str):
        columns = [columns]

    if not isinstance(columns, list) or not columns:
        raise ValueError("Select columns to process.")

    missing_columns = [
        column
        for column in columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Columns not found: {missing_columns}"
        )

    result = data.copy()

    if strategy == "drop_rows":

        return result.dropna(subset=columns)

    if strategy == "drop_columns":

        return result.drop(columns=columns)

    if strategy == "constant":

        if fill_value is None:
            raise ValueError(
                "A fill value is required."
            )

        for column in columns:
            result[column] = result[column].fillna(
                fill_value
            )

        return result

    if strategy in {"mean", "median"}:

        for column in columns:

            if not pd.api.types.is_numeric_dtype(
                result[column]
            ):
                raise ValueError(
                    f"{column} must be numeric for {strategy} filling."
                )

            value = (
                result[column].mean()
                if strategy == "mean"
                else result[column].median()
            )

            result[column] = result[column].fillna(value)

        return result

    if strategy == "mode":

        for column in columns:

            modes = result[column].mode(dropna=True)

            if not modes.empty:
                result[column] = result[column].fillna(
                    modes.iloc[0]
                )

        return result

    if strategy == "forward_fill":

        result[columns] = result[columns].ffill()

        return result

    if strategy == "backward_fill":

        result[columns] = result[columns].bfill()

        return result

    raise ValueError(
        f"Unsupported missing-value strategy: {strategy}"
    )


# ---------------------------------------------------------
# CONVERT DATA TYPES
# ---------------------------------------------------------

def convert_column_type(data, column, target_type):
    """
    Convert a column to a selected data type.
    """

    if column not in data.columns:
        raise ValueError(
            f"Column not found: {column}"
        )

    result = data.copy()

    supported_types = {
        "integer",
        "float",
        "string",
        "category",
        "boolean",
        "datetime",
    }

    if target_type not in supported_types:
        raise ValueError(
            f"Unsupported target type: {target_type}"
        )

    if target_type == "integer":

        result[column] = pd.to_numeric(
            result[column],
            errors="raise",
        ).astype("Int64")

    elif target_type == "float":

        result[column] = pd.to_numeric(
            result[column],
            errors="raise",
        ).astype(float)

    elif target_type == "string":

        result[column] = result[column].astype("string")

    elif target_type == "category":

        result[column] = result[column].astype("category")

    elif target_type == "boolean":

        mapping = {
            "true": True,
            "false": False,
            "1": True,
            "0": False,
            "yes": True,
            "no": False,
        }

        def convert_boolean(value):

            if pd.isna(value):
                return pd.NA

            if isinstance(value, (bool, np.bool_)):
                return bool(value)

            key = str(value).strip().lower()

            if key not in mapping:
                raise ValueError(
                    f"Cannot convert {value!r} to boolean."
                )

            return mapping[key]

        result[column] = result[column].map(
            convert_boolean
        ).astype("boolean")

    elif target_type == "datetime":

        result[column] = pd.to_datetime(
            result[column],
            errors="raise",
        )

    return result


# ---------------------------------------------------------
# CALCULATED COLUMNS
# ---------------------------------------------------------

def calculate_column(
    data,
    new_column,
    first_column,
    second_column,
    calculation_operator,
):
    """
    Create a calculated numeric column.

    Supported operators:
        +, -, *, /, **
    """

    if first_column not in data.columns:
        raise ValueError(
            f"Column not found: {first_column}"
        )

    if second_column not in data.columns:
        raise ValueError(
            f"Column not found: {second_column}"
        )

    if calculation_operator not in CALCULATION_OPERATORS:
        raise ValueError(
            "Unsupported calculation operator."
        )

    first_values = pd.to_numeric(
        data[first_column],
        errors="raise",
    )

    second_values = pd.to_numeric(
        data[second_column],
        errors="raise",
    )

    if calculation_operator == "/" and (
        second_values == 0
    ).any():

        raise ValueError(
            "Division by zero is not allowed."
        )

    result = data.copy()

    result[new_column] = CALCULATION_OPERATORS[
        calculation_operator
    ](
        first_values,
        second_values,
    )

    return result


# ---------------------------------------------------------
# FILTER ROWS
# ---------------------------------------------------------

def filter_rows(
    data,
    column,
    condition,
    value,
):
    """
    Filter records using a comparison condition.

    Supported conditions:
        equals
        not_equals
        greater_than
        greater_than_or_equal
        less_than
        less_than_or_equal
        contains
        not_contains
        is_missing
        is_not_missing
    """

    if column not in data.columns:
        raise ValueError(
            f"Column not found: {column}"
        )

    series = data[column]

    if condition == "is_missing":

        mask = series.isna()

    elif condition == "is_not_missing":

        mask = series.notna()

    elif condition in {"contains", "not_contains"}:

        if value is None:
            raise ValueError(
                "A search value is required."
            )

        mask = series.astype("string").str.contains(
            str(value),
            case=False,
            na=False,
            regex=False,
        )

        if condition == "not_contains":
            mask = ~mask

    elif condition in FILTER_OPERATORS:

        if condition in {
            "greater_than",
            "greater_than_or_equal",
            "less_than",
            "less_than_or_equal",
        }:

            series = pd.to_numeric(
                series,
                errors="coerce",
            )

            value = pd.to_numeric(
                pd.Series([value]),
                errors="raise",
            ).iloc[0]

        mask = FILTER_OPERATORS[condition](
            series,
            value,
        )

    else:
        raise ValueError(
            f"Unsupported filter condition: {condition}"
        )

    return data.loc[mask].copy()


# ---------------------------------------------------------
# SORT ROWS
# ---------------------------------------------------------

def sort_rows(
    data,
    columns,
    ascending=True,
):
    """
    Sort records using one or more columns.
    """

    if isinstance(columns, str):
        columns = [columns]

    if not columns:
        raise ValueError(
            "At least one sorting column is required."
        )

    missing = [
        column
        for column in columns
        if column not in data.columns
    ]

    if missing:
        raise ValueError(
            f"Columns not found: {missing}"
        )

    return data.sort_values(
        by=columns,
        ascending=ascending,
        na_position="last",
    )


# ---------------------------------------------------------
# CLEAN TEXT
# ---------------------------------------------------------

def clean_text_columns(
    data,
    columns,
    operation="trim",
):
    """
    Clean text columns.

    Operations:
        trim
        lowercase
        uppercase
        title
        remove_extra_spaces
    """

    if isinstance(columns, str):
        columns = [columns]

    if not columns:
        raise ValueError(
            "Select at least one text column."
        )

    result = data.copy()

    for column in columns:

        if column not in result.columns:
            raise ValueError(
                f"Column not found: {column}"
            )

        if not (
            pd.api.types.is_string_dtype(result[column])
            or pd.api.types.is_object_dtype(result[column])
        ):
            raise ValueError(
                f"{column} is not a text column."
            )

        values = result[column].astype("string")

        if operation == "trim":

            values = values.str.strip()

        elif operation == "lowercase":

            values = values.str.lower()

        elif operation == "uppercase":

            values = values.str.upper()

        elif operation == "title":

            values = values.str.title()

        elif operation == "remove_extra_spaces":

            values = values.str.replace(
                r"\s+",
                " ",
                regex=True,
            ).str.strip()

        else:
            raise ValueError(
                f"Unsupported text operation: {operation}"
            )

        result[column] = values

    return result


# ---------------------------------------------------------
# EXTRACT DATE COMPONENTS
# ---------------------------------------------------------

def extract_date_component(
    data,
    source_column,
    component,
    new_column,
):
    """
    Extract a component from a date column.

    Components:
        year
        month
        day
        weekday
        quarter
        hour
    """

    if source_column not in data.columns:
        raise ValueError(
            f"Column not found: {source_column}"
        )

    result = data.copy()

    dates = pd.to_datetime(
        result[source_column],
        errors="coerce",
    )

    components = {
        "year": dates.dt.year,
        "month": dates.dt.month,
        "day": dates.dt.day,
        "weekday": dates.dt.day_name(),
        "quarter": dates.dt.quarter,
        "hour": dates.dt.hour,
    }

    if component not in components:
        raise ValueError(
            f"Unsupported date component: {component}"
        )

    result[new_column] = components[component]

    return result


# ---------------------------------------------------------
# GROUP AND AGGREGATE
# ---------------------------------------------------------

def group_and_aggregate(
    data,
    group_columns,
    value_columns,
    aggregation="mean",
):
    """
    Group records and calculate summary values.

    Supported aggregations:
        sum
        mean
        median
        min
        max
        count
    """

    if isinstance(group_columns, str):
        group_columns = [group_columns]

    if isinstance(value_columns, str):
        value_columns = [value_columns]

    if not group_columns or not value_columns:
        raise ValueError(
            "Grouping and value columns are required."
        )

    for column in group_columns + value_columns:

        if column not in data.columns:
            raise ValueError(
                f"Column not found: {column}"
            )

    supported = {
        "sum",
        "mean",
        "median",
        "min",
        "max",
        "count",
    }

    if aggregation not in supported:
        raise ValueError(
            "Unsupported aggregation method."
        )

    if aggregation in {"sum", "mean", "median"}:

        for column in value_columns:

            if not pd.api.types.is_numeric_dtype(
                data[column]
            ):
                raise ValueError(
                    f"{column} must be numeric for {aggregation}."
                )

    grouped = data.groupby(
        group_columns,
        dropna=False,
    )[value_columns]

    return grouped.agg(aggregation).reset_index()


# ---------------------------------------------------------
# EXECUTE ONE STEP
# ---------------------------------------------------------

def execute_etl_step(data, step):
    """
    Execute one ETL workflow step.
    """

    operation_name = step["operation"]
    parameters = deepcopy(
        step.get("parameters", {})
    )

    if operation_name == "rename_columns":

        return rename_columns(
            data,
            parameters["mapping"],
        )

    if operation_name == "remove_columns":

        return remove_columns(
            data,
            parameters["columns"],
        )

    if operation_name == "remove_duplicates":

        return remove_duplicates(
            data,
            subset=parameters.get("subset"),
            keep=parameters.get("keep", "first"),
        )

    if operation_name == "handle_missing":

        return handle_missing_values(
            data,
            columns=parameters["columns"],
            strategy=parameters.get(
                "strategy",
                "drop_rows",
            ),
            fill_value=parameters.get("fill_value"),
        )

    if operation_name == "convert_type":

        return convert_column_type(
            data,
            column=parameters["column"],
            target_type=parameters["target_type"],
        )

    if operation_name == "calculate_column":

        return calculate_column(
            data,
            new_column=parameters["new_column"],
            first_column=parameters["first_column"],
            second_column=parameters["second_column"],
            calculation_operator=parameters["operator"],
        )

    if operation_name == "filter_rows":

        return filter_rows(
            data,
            column=parameters["column"],
            condition=parameters["condition"],
            value=parameters.get("value"),
        )

    if operation_name == "sort_rows":

        return sort_rows(
            data,
            columns=parameters["columns"],
            ascending=parameters.get("ascending", True),
        )

    if operation_name == "clean_text":

        return clean_text_columns(
            data,
            columns=parameters["columns"],
            operation=parameters.get("operation", "trim"),
        )

    if operation_name == "extract_date":

        return extract_date_component(
            data,
            source_column=parameters["source_column"],
            component=parameters["component"],
            new_column=parameters["new_column"],
        )

    if operation_name == "group_aggregate":

        return group_and_aggregate(
            data,
            group_columns=parameters["group_columns"],
            value_columns=parameters["value_columns"],
            aggregation=parameters.get(
                "aggregation",
                "mean",
            ),
        )

    raise ValueError(
        f"Unsupported ETL operation: {operation_name}"
    )


# ---------------------------------------------------------
# EXECUTE COMPLETE WORKFLOW
# ---------------------------------------------------------

def execute_etl_workflow(
    data,
    workflow,
    stop_on_error=True,
):
    """
    Execute an entire ETL workflow sequentially.

    Returns:
        {
            "success": bool,
            "data": DataFrame,
            "steps_completed": int,
            "steps_failed": int,
            "execution_log": list,
            "initial_shape": tuple,
            "final_shape": tuple
        }

    The original input DataFrame is never modified.
    """

    validate_dataframe(data)
    validate_workflow(workflow)

    result = data.copy(deep=True)

    initial_shape = result.shape

    execution_log = []
    steps_completed = 0
    steps_failed = 0

    for position, step in enumerate(workflow, start=1):

        operation_name = step["operation"]

        before_shape = result.shape

        try:

            updated = execute_etl_step(
                result.copy(deep=True),
                step,
            )

            if not isinstance(updated, pd.DataFrame):
                raise ValueError(
                    "ETL operation did not return a DataFrame."
                )

            if updated.columns.duplicated().any():
                raise ValueError(
                    "Operation produced duplicate column names."
                )

            result = updated

            steps_completed += 1

            execution_log.append({
                "step": position,
                "operation": operation_name,
                "status": "completed",
                "rows_before": before_shape[0],
                "rows_after": result.shape[0],
                "columns_before": before_shape[1],
                "columns_after": result.shape[1],
                "error": None,
            })

        except Exception as error:

            steps_failed += 1

            execution_log.append({
                "step": position,
                "operation": operation_name,
                "status": "failed",
                "rows_before": before_shape[0],
                "rows_after": before_shape[0],
                "columns_before": before_shape[1],
                "columns_after": before_shape[1],
                "error": str(error),
            })

            if stop_on_error:
                break

    success = (
        steps_failed == 0
        and steps_completed == len(workflow)
    )

    return {
        "success": success,
        "data": result,
        "steps_completed": steps_completed,
        "steps_failed": steps_failed,
        "execution_log": execution_log,
        "initial_shape": initial_shape,
        "final_shape": result.shape,
    }


# ---------------------------------------------------------
# WORKFLOW SUMMARY
# ---------------------------------------------------------

def get_workflow_summary(workflow):
    """
    Generate a readable summary of workflow steps.
    """

    validate_workflow(workflow)

    records = []

    for position, step in enumerate(workflow, start=1):

        records.append({
            "Step": position,
            "Operation": step["operation"].replace(
                "_",
                " ",
            ).title(),
            "Parameters": str(
                step.get("parameters", {})
            ),
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------
# EXECUTION REPORT
# ---------------------------------------------------------

def generate_etl_report(execution_result):
    """
    Convert workflow execution logs into a report.
    """

    if not isinstance(execution_result, dict):
        raise ValueError(
            "A valid execution result is required."
        )

    required = {
        "success",
        "steps_completed",
        "steps_failed",
        "execution_log",
        "initial_shape",
        "final_shape",
    }

    missing = required.difference(
        execution_result.keys()
    )

    if missing:
        raise ValueError(
            f"Execution result is missing: {sorted(missing)}"
        )

    return {
        "success": execution_result["success"],
        "steps_completed": execution_result["steps_completed"],
        "steps_failed": execution_result["steps_failed"],
        "initial_rows": execution_result["initial_shape"][0],
        "initial_columns": execution_result["initial_shape"][1],
        "final_rows": execution_result["final_shape"][0],
        "final_columns": execution_result["final_shape"][1],
        "execution_log": pd.DataFrame(
            execution_result["execution_log"]
        ),
    }
