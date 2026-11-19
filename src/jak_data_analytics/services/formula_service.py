"""
JAK Data Analytics
Formula Engine Service

A safe, vectorised formula engine for Pandas DataFrames.

Features:
- Formula validation
- Safe AST-based expression evaluation
- Numeric calculations
- Comparison operations
- Boolean operations
- Conditional formulas
- Text functions
- Mathematical functions
- Column references
- Calculated column creation
- Formula explanations

Security:
- Does not use Python eval().
- Only explicitly supported AST operations are allowed.
- Arbitrary Python execution is prohibited.
"""

import ast
import operator
import math
import re

import numpy as np
import pandas as pd


# ---------------------------------------------------------
# SUPPORTED OPERATORS
# ---------------------------------------------------------

BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.BitAnd: operator.and_,
    ast.BitOr: operator.or_,
}

UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Not: operator.invert,
}

COMPARISON_OPERATORS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}


# ---------------------------------------------------------
# SUPPORTED FORMULA FUNCTIONS
# ---------------------------------------------------------

def formula_abs(value):
    return abs(value)


def formula_round(value, digits=0):
    return np.round(value, int(digits))


def formula_min(*values):
    if not values:
        raise ValueError("min() requires at least one argument.")

    return reduce_values(values, np.minimum)


def formula_max(*values):
    if not values:
        raise ValueError("max() requires at least one argument.")

    return reduce_values(values, np.maximum)


def reduce_values(values, function):
    """Apply a vectorised reduction across values."""

    result = values[0]

    for value in values[1:]:
        result = function(result, value)

    return result


def formula_sqrt(value):
    return np.sqrt(value)


def formula_log(value):
    return np.log(value)


def formula_log10(value):
    return np.log10(value)


def formula_exp(value):
    return np.exp(value)


def formula_ceil(value):
    return np.ceil(value)


def formula_floor(value):
    return np.floor(value)


def formula_power(value, exponent):
    return np.power(value, exponent)


def formula_if_else(condition, true_value, false_value):
    return np.where(
        condition,
        true_value,
        false_value,
    )


def formula_is_null(value):
    return pd.isna(value)


def formula_is_not_null(value):
    return pd.notna(value)


def formula_fill_null(value, replacement):
    if isinstance(value, pd.Series):
        return value.fillna(replacement)

    if isinstance(value, np.ndarray):
        return np.where(
            pd.isna(value),
            replacement,
            value,
        )

    return replacement if pd.isna(value) else value


def formula_lower(value):
    if isinstance(value, pd.Series):
        return value.astype("string").str.lower()

    return str(value).lower()


def formula_upper(value):
    if isinstance(value, pd.Series):
        return value.astype("string").str.upper()

    return str(value).upper()


def formula_trim(value):
    if isinstance(value, pd.Series):
        return value.astype("string").str.strip()

    return str(value).strip()


def formula_length(value):
    if isinstance(value, pd.Series):
        return value.astype("string").str.len()

    return len(str(value))


def formula_contains(value, text):
    if isinstance(value, pd.Series):
        return (
            value.astype("string")
            .str.contains(
                str(text),
                case=False,
                regex=False,
                na=False,
            )
        )

    return str(text).lower() in str(value).lower()


def formula_replace(value, old, new):
    if isinstance(value, pd.Series):
        return value.astype("string").str.replace(
            str(old),
            str(new),
            regex=False,
        )

    return str(value).replace(
        str(old),
        str(new),
    )


def formula_to_number(value):
    if isinstance(value, pd.Series):
        return pd.to_numeric(
            value,
            errors="coerce",
        )

    return pd.to_numeric(
        value,
        errors="coerce",
    )


def formula_to_string(value):
    if isinstance(value, pd.Series):
        return value.astype("string")

    return str(value)


def formula_year(value):
    dates = pd.to_datetime(
        value,
        errors="coerce",
    )

    if isinstance(dates, pd.Series):
        return dates.dt.year

    return dates.year if not pd.isna(dates) else np.nan


def formula_month(value):
    dates = pd.to_datetime(
        value,
        errors="coerce",
    )

    if isinstance(dates, pd.Series):
        return dates.dt.month

    return dates.month if not pd.isna(dates) else np.nan


def formula_day(value):
    dates = pd.to_datetime(
        value,
        errors="coerce",
    )

    if isinstance(dates, pd.Series):
        return dates.dt.day

    return dates.day if not pd.isna(dates) else np.nan


FORMULA_FUNCTIONS = {
    "abs": formula_abs,
    "round": formula_round,
    "min": formula_min,
    "max": formula_max,
    "sqrt": formula_sqrt,
    "log": formula_log,
    "log10": formula_log10,
    "exp": formula_exp,
    "ceil": formula_ceil,
    "floor": formula_floor,
    "power": formula_power,
    "where": formula_if_else,
    "is_null": formula_is_null,
    "is_not_null": formula_is_not_null,
    "fill_null": formula_fill_null,
    "lower": formula_lower,
    "upper": formula_upper,
    "trim": formula_trim,
    "length": formula_length,
    "contains": formula_contains,
    "replace": formula_replace,
    "to_number": formula_to_number,
    "to_string": formula_to_string,
    "year": formula_year,
    "month": formula_month,
    "day": formula_day,
}


# ---------------------------------------------------------
# FORMULA CONFIGURATION
# ---------------------------------------------------------

MAX_FORMULA_LENGTH = 1000
MAX_AST_NODES = 100
MAX_POWER_EXPONENT = 100

FORMULA_EXAMPLES = [
    {
        "name": "Basic multiplication",
        "formula": "Price * Quantity",
    },
    {
        "name": "Percentage calculation",
        "formula": "Salary * 0.10",
    },
    {
        "name": "Rounding",
        "formula": "round(Price * Quantity, 2)",
    },
    {
        "name": "Conditional formula",
        "formula": 'where(Age >= 18, "Adult", "Minor")',
    },
    {
        "name": "Text formatting",
        "formula": "upper(Department)",
    },
    {
        "name": "Null handling",
        "formula": "fill_null(Salary, 0)",
    },
    {
        "name": "Column with spaces",
        "formula": 'col("Employee Salary") * 0.15',
    },
]


# ---------------------------------------------------------
# GENERAL VALIDATION
# ---------------------------------------------------------

def validate_dataframe(data):
    """Validate a DataFrame before formula execution."""

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
            "Dataset contains duplicate column names."
        )

    return True


def normalize_formula(formula):
    """Validate and normalize a formula string."""

    if not isinstance(formula, str):
        raise ValueError(
            "Formula must be a string."
        )

    formula = formula.strip()

    if not formula:
        raise ValueError(
            "Formula cannot be empty."
        )

    if len(formula) > MAX_FORMULA_LENGTH:
        raise ValueError(
            "Formula exceeds the maximum allowed length."
        )

    return formula


# ---------------------------------------------------------
# AST VALIDATION
# ---------------------------------------------------------

def parse_formula(formula):
    """
    Parse a formula into an AST.

    Only expression mode is accepted.
    """

    formula = normalize_formula(formula)

    try:
        tree = ast.parse(
            formula,
            mode="eval",
        )

    except SyntaxError as error:
        raise ValueError(
            f"Invalid formula syntax: {error.msg}"
        )

    nodes = list(ast.walk(tree))

    if len(nodes) > MAX_AST_NODES:
        raise ValueError(
            "Formula is too complex."
        )

    return tree


def validate_ast_node(node):
    """Check that every AST node is explicitly supported."""

    allowed_nodes = (
        ast.Expression,
        ast.Constant,
        ast.Name,
        ast.BinOp,
        ast.UnaryOp,
        ast.Compare,
        ast.Call,
        ast.Load,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.FloorDiv,
        ast.Mod,
        ast.Pow,
        ast.BitAnd,
        ast.BitOr,
        ast.UAdd,
        ast.USub,
        ast.Not,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
    )

    for node_item in ast.walk(node):

        if not isinstance(node_item, allowed_nodes):
            raise ValueError(
                "Formula contains an unsupported operation: "
                f"{type(node_item).__name__}"
            )

        if isinstance(node_item, ast.Name):

            if node_item.id.startswith("__"):
                raise ValueError(
                    "Private names are not allowed."
                )

        if isinstance(node_item, ast.Call):

            if not isinstance(node_item.func, ast.Name):
                raise ValueError(
                    "Only approved formula functions are allowed."
                )

            if node_item.keywords:
                raise ValueError(
                    "Keyword arguments are not supported."
                )

            function_name = node_item.func.id

            if (
                function_name not in FORMULA_FUNCTIONS
                and function_name != "col"
            ):
                raise ValueError(
                    f"Unsupported formula function: {function_name}"
                )

    return True


# ---------------------------------------------------------
# COLUMN DISCOVERY
# ---------------------------------------------------------

def extract_column_references(tree, dataframe):
    """Find all dataset columns referenced by a formula."""

    references = set()

    for node in ast.walk(tree):

        if isinstance(node, ast.Name):

            if node.id in dataframe.columns:
                references.add(node.id)

            elif node.id not in FORMULA_FUNCTIONS:
                if node.id not in {
                    "True",
                    "False",
                    "None",
                }:
                    raise ValueError(
                        f"Unknown column or name: {node.id}"
                    )

        if isinstance(node, ast.Call):

            if (
                isinstance(node.func, ast.Name)
                and node.func.id == "col"
            ):

                if len(node.args) != 1:
                    raise ValueError(
                        'col() requires exactly one column name.'
                    )

                argument = node.args[0]

                if not isinstance(argument, ast.Constant):
                    raise ValueError(
                        'Use col("Column Name") with a text column name.'
                    )

                column_name = argument.value

                if not isinstance(column_name, str):
                    raise ValueError(
                        "Column name must be text."
                    )

                if column_name not in dataframe.columns:
                    raise ValueError(
                        f"Column does not exist: {column_name}"
                    )

                references.add(column_name)

    return sorted(references)


# ---------------------------------------------------------
# SAFE EXPRESSION EVALUATION
# ---------------------------------------------------------

def evaluate_node(node, dataframe):
    """
    Safely evaluate an AST node.

    This interpreter supports only explicitly approved
    operations and functions.
    """

    # -----------------------------------------------------
    # CONSTANTS
    # -----------------------------------------------------

    if isinstance(node, ast.Constant):
        return node.value

    # -----------------------------------------------------
    # COLUMN NAMES
    # -----------------------------------------------------

    if isinstance(node, ast.Name):

        if node.id in dataframe.columns:
            return dataframe[node.id]

        constants = {
            "True": True,
            "False": False,
            "None": None,
        }

        if node.id in constants:
            return constants[node.id]

        raise ValueError(
            f"Unknown column or name: {node.id}"
        )

    # -----------------------------------------------------
    # BINARY OPERATIONS
    # -----------------------------------------------------

    if isinstance(node, ast.BinOp):

        operator_type = type(node.op)

        if operator_type not in BINARY_OPERATORS:
            raise ValueError(
                "Unsupported mathematical operator."
            )

        left = evaluate_node(
            node.left,
            dataframe,
        )

        right = evaluate_node(
            node.right,
            dataframe,
        )

        if isinstance(node.op, ast.Pow):

            try:
                if np.isscalar(right):
                    if abs(float(right)) > MAX_POWER_EXPONENT:
                        raise ValueError(
                            "Power exponent is too large."
                        )

            except (TypeError, ValueError):
                raise ValueError(
                    "Invalid power exponent."
                )

        try:
            return BINARY_OPERATORS[operator_type](
                left,
                right,
            )

        except ZeroDivisionError:
            raise ValueError(
                "Division by zero occurred."
            )

        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError(
                f"Calculation failed: {error}"
            )

    # -----------------------------------------------------
    # UNARY OPERATIONS
    # -----------------------------------------------------

    if isinstance(node, ast.UnaryOp):

        operator_type = type(node.op)

        if operator_type not in UNARY_OPERATORS:
            raise ValueError(
                "Unsupported unary operator."
            )

        value = evaluate_node(
            node.operand,
            dataframe,
        )

        return UNARY_OPERATORS[operator_type](
            value
        )

    # -----------------------------------------------------
    # COMPARISONS
    # -----------------------------------------------------

    if isinstance(node, ast.Compare):

        left = evaluate_node(
            node.left,
            dataframe,
        )

        result = None

        for operation, comparator in zip(
            node.ops,
            node.comparators,
        ):

            operator_type = type(operation)

            if operator_type not in COMPARISON_OPERATORS:
                raise ValueError(
                    "Unsupported comparison operator."
                )

            right = evaluate_node(
                comparator,
                dataframe,
            )

            comparison = COMPARISON_OPERATORS[
                operator_type
            ](left, right)

            if result is None:
                result = comparison

            else:
                result = result & comparison

            left = right

        return result

    # -----------------------------------------------------
    # FUNCTION CALLS
    # -----------------------------------------------------

    if isinstance(node, ast.Call):

        if not isinstance(node.func, ast.Name):
            raise ValueError(
                "Invalid function call."
            )

        function_name = node.func.id

        if function_name == "col":

            if len(node.args) != 1:
                raise ValueError(
                    "col() requires exactly one argument."
                )

            column_name = evaluate_node(
                node.args[0],
                dataframe,
            )

            if not isinstance(column_name, str):
                raise ValueError(
                    "Column name must be a string."
                )

            if column_name not in dataframe.columns:
                raise ValueError(
                    f"Unknown column: {column_name}"
                )

            return dataframe[column_name]

        if function_name not in FORMULA_FUNCTIONS:
            raise ValueError(
                f"Unsupported function: {function_name}"
            )

        arguments = [
            evaluate_node(argument, dataframe)
            for argument in node.args
        ]

        try:
            return FORMULA_FUNCTIONS[
                function_name
            ](*arguments)

        except Exception as error:
            raise ValueError(
                f"Function '{function_name}' failed: {error}"
            )

    raise ValueError(
        f"Unsupported expression: {type(node).__name__}"
    )


# ---------------------------------------------------------
# FORMULA VALIDATION
# ---------------------------------------------------------

def validate_formula(formula, dataframe):
    """Validate a formula without calculating its result."""

    validate_dataframe(dataframe)

    tree = parse_formula(formula)

    validate_ast_node(tree)

    references = extract_column_references(
        tree,
        dataframe,
    )

    return {
        "valid": True,
        "formula": normalize_formula(formula),
        "columns": references,
        "column_count": len(references),
        "functions": sorted({
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id != "col"
        }),
    }


# ---------------------------------------------------------
# FORMULA EVALUATION
# ---------------------------------------------------------

def evaluate_formula(formula, dataframe):
    """
    Evaluate a formula against a DataFrame.

    Returns a scalar, Series or array depending on
    the formula expression.
    """

    validate_dataframe(dataframe)

    tree = parse_formula(formula)

    validate_ast_node(tree)

    extract_column_references(
        tree,
        dataframe,
    )

    result = evaluate_node(
        tree.body,
        dataframe,
    )

    if np.isscalar(result) or result is None:
        return pd.Series(
            [result] * len(dataframe),
            index=dataframe.index,
        )

    if isinstance(result, pd.Series):

        if len(result) != len(dataframe):
            raise ValueError(
                "Formula result has an unexpected length."
            )

        return result.reindex(
            dataframe.index
        )

    if isinstance(result, pd.Index):
        result = result.to_numpy()

    if isinstance(result, np.ndarray):

        if result.ndim == 0:
            return pd.Series(
                [result.item()] * len(dataframe),
                index=dataframe.index,
            )

        if len(result) != len(dataframe):
            raise ValueError(
                "Formula result has an unexpected length."
            )

        return pd.Series(
            result,
            index=dataframe.index,
        )

    raise ValueError(
        "Formula produced an unsupported result."
    )


# ---------------------------------------------------------
# CREATE CALCULATED COLUMN
# ---------------------------------------------------------

def create_calculated_column(
    dataframe,
    column_name,
    formula,
    overwrite=False,
):
    """
    Create a new calculated column.

    The original DataFrame is never modified.
    """

    validate_dataframe(dataframe)

    column_name = str(
        column_name
    ).strip()

    if not column_name:
        raise ValueError(
            "New column name is required."
        )

    if column_name in dataframe.columns and not overwrite:
        raise ValueError(
            f"Column already exists: {column_name}"
        )

    result = evaluate_formula(
        formula,
        dataframe,
    )

    updated = dataframe.copy()

    updated[column_name] = result

    return {
        "data": updated,
        "column_name": column_name,
        "formula": normalize_formula(formula),
        "rows_affected": len(updated),
        "data_type": str(
            updated[column_name].dtype
        ),
    }


# ---------------------------------------------------------
# FORMULA EXPLANATION
# ---------------------------------------------------------

def explain_formula(formula, dataframe):
    """
    Generate basic information about a formula.

    This is a structural explanation, not an AI-generated
    interpretation.
    """

    validation = validate_formula(
        formula,
        dataframe,
    )

    return {
        "formula": validation["formula"],
        "valid": validation["valid"],
        "referenced_columns": validation["columns"],
        "functions_used": validation["functions"],
        "description": (
            "This formula uses "
            f"{validation['column_count']} dataset column(s) "
            "and "
            f"{len(validation['functions'])} approved function(s)."
        ),
    }


# ---------------------------------------------------------
# FORMULA PREVIEW
# ---------------------------------------------------------

def preview_formula(
    dataframe,
    formula,
    limit=10,
):
    """Preview formula results without changing the dataset."""

    validate_dataframe(dataframe)

    result = evaluate_formula(
        formula,
        dataframe,
    )

    preview = pd.DataFrame({
        "Original Index": dataframe.index,
        "Formula Result": result.values,
    })

    return preview.head(
        max(1, int(limit))
    )


# ---------------------------------------------------------
# FORMULA HISTORY UTILITIES
# ---------------------------------------------------------

def create_formula_record(
    column_name,
    formula,
    dataset_id=None,
):
    """Create a formula history record."""

    return {
        "formula_id": str(
            __import__("uuid").uuid4()
        ),
        "dataset_id": (
            str(dataset_id)
            if dataset_id is not None
            else None
        ),
        "column_name": str(column_name),
        "formula": normalize_formula(formula),
        "created_at": pd.Timestamp.now(
            tz="UTC"
        ).isoformat(),
    }


# ---------------------------------------------------------
# AVAILABLE FUNCTIONS
# ---------------------------------------------------------

def get_available_formula_functions():
    """Return available formula functions and descriptions."""

    descriptions = {
        "abs": "Returns the absolute value.",
        "round": "Rounds a number to a specified number of decimals.",
        "min": "Returns the minimum of supplied values.",
        "max": "Returns the maximum of supplied values.",
        "sqrt": "Calculates the square root.",
        "log": "Calculates the natural logarithm.",
        "log10": "Calculates the base-10 logarithm.",
        "exp": "Calculates the exponential.",
        "ceil": "Rounds a number upward.",
        "floor": "Rounds a number downward.",
        "power": "Raises a number to a specified power.",
        "where": "Returns one value when a condition is true and another when false.",
        "is_null": "Checks whether a value is missing.",
        "is_not_null": "Checks whether a value is not missing.",
        "fill_null": "Replaces missing values.",
        "lower": "Converts text to lowercase.",
        "upper": "Converts text to uppercase.",
        "trim": "Removes leading and trailing spaces.",
        "length": "Returns the length of text.",
        "contains": "Checks whether text contains another value.",
        "replace": "Replaces text with another value.",
        "to_number": "Converts values to numbers.",
        "to_string": "Converts values to text.",
        "year": "Extracts the year from a date.",
        "month": "Extracts the month from a date.",
        "day": "Extracts the day from a date.",
        "col": "References a dataset column by its exact name.",
    }

    return [
        {
            "function": name,
            "description": description,
        }
        for name, description in descriptions.items()
    ]


# ---------------------------------------------------------
# FORMULA EXAMPLES
# ---------------------------------------------------------

def get_formula_examples():
    """Return example formulas."""

    return list(
        FORMULA_EXAMPLES
    )


# ---------------------------------------------------------
# FORMULA TEST
# ---------------------------------------------------------

def test_formula_engine():
    """
    Run basic internal formula checks.

    Returns a summary of passed and failed tests.
    """

    sample = pd.DataFrame({
        "Salary": [1000, 2000, 3000],
        "Quantity": [2, 3, 4],
        "Age": [15, 20, 30],
        "Department": ["Sales", "IT", "Finance"],
        "Employee Salary": [5000, 6000, 7000],
    })

    tests = []

    def run_test(name, callback):

        try:
            callback()

            tests.append({
                "test": name,
                "status": "passed",
                "error": None,
            })

        except Exception as error:

            tests.append({
                "test": name,
                "status": "failed",
                "error": str(error),
            })

    run_test(
        "Basic arithmetic",
        lambda: assert_values(
            evaluate_formula(
                "Salary * 2",
                sample,
            ),
            [2000, 4000, 6000],
        ),
    )

    run_test(
        "Column references with spaces",
        lambda: assert_values(
            evaluate_formula(
                'col("Employee Salary") * 0.10',
                sample,
            ),
            [500, 600, 700],
        ),
    )

    run_test(
        "Conditional formula",
        lambda: assert_values(
            evaluate_formula(
                'where(Age >= 18, "Adult", "Minor")',
                sample,
            ),
            ["Minor", "Adult", "Adult"],
        ),
    )

    run_test(
        "Text function",
        lambda: assert_values(
            evaluate_formula(
                "upper(Department)",
                sample,
            ),
            ["SALES", "IT", "FINANCE"],
        ),
    )

    run_test(
        "Safe formula rejection",
        lambda: assert_rejected(
            "__import__('os').system('echo unsafe')",
            sample,
        ),
    )

    passed = sum(
        item["status"] == "passed"
        for item in tests
    )

    failed = len(tests) - passed

    return {
        "total_tests": len(tests),
        "passed": passed,
        "failed": failed,
        "success": failed == 0,
        "tests": tests,
    }


def assert_values(actual, expected):
    """Internal assertion helper."""

    actual_values = list(actual)

    if actual_values != expected:
        raise AssertionError(
            f"Expected {expected}, got {actual_values}"
        )


def assert_rejected(formula, dataframe):
    """Ensure an unsafe formula is rejected."""

    try:
        evaluate_formula(
            formula,
            dataframe,
        )

    except ValueError:
        return

    raise AssertionError(
        "Unsafe formula was not rejected."
    )
