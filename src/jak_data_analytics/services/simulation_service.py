"""
JAK Data Analytics
Scenario Simulation Service

Provides reusable scenario simulation capabilities:
- Baseline calculations
- Percentage adjustments
- Fixed-value adjustments
- Scenario comparisons
- Impact analysis
- Sensitivity analysis
"""

import pandas as pd
import numpy as np


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_simulation_data(data, selected_columns=None):
    """
    Validate a dataset for scenario simulation.
    """

    if not isinstance(data, pd.DataFrame):
        return False, "Input must be a Pandas DataFrame."

    if data.empty:
        return False, "Dataset cannot be empty."

    if selected_columns is None:
        selected_columns = data.select_dtypes(
            include="number"
        ).columns.tolist()

    if not selected_columns:
        return False, "No numerical columns are available."

    missing_columns = [
        column
        for column in selected_columns
        if column not in data.columns
    ]

    if missing_columns:
        return False, (
            f"Columns not found: {missing_columns}"
        )

    for column in selected_columns:
        if not pd.api.types.is_numeric_dtype(data[column]):
            return False, (
                f"Column '{column}' must contain numeric values."
            )

        if not np.isfinite(
            pd.to_numeric(data[column], errors="coerce")
            .dropna()
        ).all():
            return False, (
                f"Column '{column}' contains infinite values."
            )

    return True, None


# ---------------------------------------------------------
# BASELINE CALCULATIONS
# ---------------------------------------------------------

def calculate_baseline(
    data,
    selected_columns,
    aggregation="sum",
):
    """
    Calculate baseline values for selected columns.

    Supported aggregation:
        sum, mean, median, min, max, count
    """

    is_valid, error = validate_simulation_data(
        data,
        selected_columns,
    )

    if not is_valid:
        raise ValueError(error)

    supported_aggregations = {
        "sum",
        "mean",
        "median",
        "min",
        "max",
        "count",
    }

    aggregation = str(aggregation).lower()

    if aggregation not in supported_aggregations:
        raise ValueError(
            "Unsupported aggregation method."
        )

    baseline = {}

    for column in selected_columns:
        series = pd.to_numeric(
            data[column],
            errors="coerce",
        ).dropna()

        if series.empty:
            baseline[column] = 0.0
            continue

        if aggregation == "sum":
            value = series.sum()

        elif aggregation == "mean":
            value = series.mean()

        elif aggregation == "median":
            value = series.median()

        elif aggregation == "min":
            value = series.min()

        elif aggregation == "max":
            value = series.max()

        else:
            value = series.count()

        baseline[column] = float(value)

    return baseline


# ---------------------------------------------------------
# CREATE SCENARIO
# ---------------------------------------------------------

def create_scenario(
    baseline,
    scenario_name,
    adjustments,
):
    """
    Create a scenario using percentage or fixed adjustments.

    adjustments example:

    {
        "Revenue": {
            "type": "percentage",
            "value": 15
        },
        "Expenses": {
            "type": "fixed",
            "value": 5000
        }
    }

    Percentage values represent percentage changes.
    """

    if not isinstance(baseline, dict) or not baseline:
        raise ValueError("A valid baseline is required.")

    scenario_name = str(
        scenario_name or ""
    ).strip()

    if not scenario_name:
        raise ValueError("Scenario name is required.")

    if not isinstance(adjustments, dict):
        raise ValueError("Adjustments must be a dictionary.")

    scenario_values = {}
    adjustment_details = {}

    for column, original_value in baseline.items():

        original_value = float(original_value)

        adjustment = adjustments.get(column)

        if adjustment is None:
            scenario_values[column] = original_value

            adjustment_details[column] = {
                "type": "none",
                "value": 0.0,
            }

            continue

        if not isinstance(adjustment, dict):
            raise ValueError(
                f"Invalid adjustment for '{column}'."
            )

        adjustment_type = str(
            adjustment.get("type", "")
        ).lower()

        adjustment_value = float(
            adjustment.get("value", 0)
        )

        if not np.isfinite(adjustment_value):
            raise ValueError(
                f"Invalid adjustment value for '{column}'."
            )

        if adjustment_type == "percentage":

            new_value = (
                original_value
                * (1 + adjustment_value / 100)
            )

        elif adjustment_type == "fixed":

            new_value = (
                original_value + adjustment_value
            )

        elif adjustment_type == "none":

            new_value = original_value

        else:
            raise ValueError(
                f"Unsupported adjustment type for '{column}'."
            )

        if not np.isfinite(new_value):
            raise ValueError(
                f"Calculated value for '{column}' is invalid."
            )

        scenario_values[column] = float(new_value)

        adjustment_details[column] = {
            "type": adjustment_type,
            "value": adjustment_value,
        }

    return {
        "name": scenario_name,
        "baseline": dict(baseline),
        "values": scenario_values,
        "adjustments": adjustment_details,
    }


# ---------------------------------------------------------
# COMPARE SCENARIOS
# ---------------------------------------------------------

def compare_scenarios(
    baseline,
    scenarios,
):
    """
    Compare baseline values against multiple scenarios.
    """

    if not isinstance(baseline, dict) or not baseline:
        raise ValueError("A valid baseline is required.")

    if not scenarios:
        raise ValueError("At least one scenario is required.")

    records = []

    for column, baseline_value in baseline.items():

        baseline_value = float(baseline_value)

        records.append({
            "Metric": column,
            "Scenario": "Baseline",
            "Value": baseline_value,
            "Change": 0.0,
            "Change Percentage": 0.0,
        })

        for scenario in scenarios:

            scenario_values = scenario.get("values", {})

            if column not in scenario_values:
                continue

            scenario_value = float(
                scenario_values[column]
            )

            change = scenario_value - baseline_value

            if baseline_value == 0:
                percentage_change = np.nan
            else:
                percentage_change = (
                    change / abs(baseline_value)
                ) * 100

            records.append({
                "Metric": column,
                "Scenario": scenario.get(
                    "name",
                    "Unnamed Scenario",
                ),
                "Value": scenario_value,
                "Change": change,
                "Change Percentage": percentage_change,
            })

    return pd.DataFrame(records)


# ---------------------------------------------------------
# IMPACT ANALYSIS
# ---------------------------------------------------------

def calculate_scenario_impact(
    baseline,
    scenario,
):
    """
    Calculate the impact of one scenario against baseline.
    """

    scenario_values = scenario.get("values", {})

    records = []

    for column, baseline_value in baseline.items():

        if column not in scenario_values:
            continue

        baseline_value = float(baseline_value)
        scenario_value = float(scenario_values[column])

        change = scenario_value - baseline_value

        if baseline_value == 0:
            percentage_change = None
        else:
            percentage_change = (
                change / abs(baseline_value)
            ) * 100

        if change > 0:
            direction = "Increase"

        elif change < 0:
            direction = "Decrease"

        else:
            direction = "No Change"

        records.append({
            "Metric": column,
            "Baseline": baseline_value,
            "Scenario Value": scenario_value,
            "Absolute Change": change,
            "Percentage Change": percentage_change,
            "Direction": direction,
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------
# SENSITIVITY ANALYSIS
# ---------------------------------------------------------

def run_sensitivity_analysis(
    baseline,
    column,
    percentage_changes=None,
):
    """
    Test how different percentage changes affect one metric.

    Default changes:
        -20%, -10%, -5%, 0%, 5%, 10%, 20%
    """

    if column not in baseline:
        raise ValueError(
            f"Column '{column}' was not found in the baseline."
        )

    if percentage_changes is None:
        percentage_changes = [
            -20,
            -10,
            -5,
            0,
            5,
            10,
            20,
        ]

    original_value = float(baseline[column])

    records = []

    for percentage in percentage_changes:

        percentage = float(percentage)

        if not np.isfinite(percentage):
            raise ValueError(
                "Sensitivity percentages must be finite."
            )

        adjusted_value = (
            original_value * (1 + percentage / 100)
        )

        records.append({
            "Metric": column,
            "Percentage Change": percentage,
            "Baseline Value": original_value,
            "Adjusted Value": adjusted_value,
            "Absolute Impact": adjusted_value - original_value,
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------
# SCENARIO RANKING
# ---------------------------------------------------------

def rank_scenarios(
    baseline,
    scenarios,
    objective,
    metric,
):
    """
    Rank scenarios based on one selected metric.

    objective:
        maximise or minimise
    """

    if objective not in {"maximise", "minimise"}:
        raise ValueError(
            "Objective must be maximise or minimise."
        )

    if metric not in baseline:
        raise ValueError(
            f"Metric '{metric}' is not in the baseline."
        )

    records = []

    records.append({
        "Scenario": "Baseline",
        "Metric": metric,
        "Value": float(baseline[metric]),
    })

    for scenario in scenarios:

        values = scenario.get("values", {})

        if metric not in values:
            continue

        records.append({
            "Scenario": scenario.get(
                "name",
                "Unnamed Scenario",
            ),
            "Metric": metric,
            "Value": float(values[metric]),
        })

    results = pd.DataFrame(records)

    results = results.sort_values(
        "Value",
        ascending=(objective == "minimise"),
    ).reset_index(drop=True)

    results["Rank"] = range(1, len(results) + 1)

    return results


# ---------------------------------------------------------
# SCENARIO SUMMARY
# ---------------------------------------------------------

def generate_scenario_summary(
    baseline,
    scenarios,
):
    """
    Generate a summary of all scenarios.
    """

    if not isinstance(baseline, dict) or not baseline:
        raise ValueError("A valid baseline is required.")

    summary = {
        "number_of_metrics": len(baseline),
        "number_of_scenarios": len(scenarios),
        "scenarios": [],
    }

    for scenario in scenarios:

        impact = calculate_scenario_impact(
            baseline,
            scenario,
        )

        total_absolute_impact = float(
            impact["Absolute Change"].abs().sum()
        )

        summary["scenarios"].append({
            "name": scenario.get("name", "Unnamed Scenario"),
            "total_absolute_impact": total_absolute_impact,
            "metrics_increased": int(
                (impact["Absolute Change"] > 0).sum()
            ),
            "metrics_decreased": int(
                (impact["Absolute Change"] < 0).sum()
            ),
            "metrics_unchanged": int(
                (impact["Absolute Change"] == 0).sum()
            ),
        })

    return summary
