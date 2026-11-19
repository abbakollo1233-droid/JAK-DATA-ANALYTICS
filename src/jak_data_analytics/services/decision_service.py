"""
JAK Data Analytics
Decision Support Service

Provides independent decision-support calculations:
- Weighted decision matrices
- Benefit and cost criteria
- Criteria normalisation
- Alternative ranking
- Sensitivity analysis
"""

import pandas as pd


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_decision_matrix(
    matrix,
    weights,
    criteria_types,
):
    """
    Validate a decision matrix and its configuration.

    matrix:
        DataFrame where rows are alternatives
        and columns are criteria.
    """

    if not isinstance(matrix, pd.DataFrame):
        return False, "Decision matrix must be a Pandas DataFrame."

    if matrix.empty:
        return False, "Decision matrix cannot be empty."

    if matrix.shape[0] < 2:
        return False, "At least two alternatives are required."

    if matrix.shape[1] < 1:
        return False, "At least one criterion is required."

    if not matrix.index.is_unique:
        return False, "Alternative names must be unique."

    if not matrix.columns.is_unique:
        return False, "Criterion names must be unique."

    if matrix.isnull().any().any():
        return False, "Decision matrix contains missing values."

    numeric_matrix = matrix.apply(
        pd.to_numeric,
        errors="coerce",
    )

    if numeric_matrix.isnull().any().any():
        return False, "All decision matrix values must be numeric."

    if not all(pd.api.types.is_numeric_dtype(dtype)
               for dtype in numeric_matrix.dtypes):
        return False, "Decision matrix contains non-numeric values."

    if weights is None:
        return False, "Criteria weights are required."

    if set(weights.keys()) != set(matrix.columns):
        return False, "Weights must be supplied for every criterion."

    try:
        numeric_weights = {
            criterion: float(weight)
            for criterion, weight in weights.items()
        }
    except (ValueError, TypeError):
        return False, "Criteria weights must be numeric."

    if any(weight < 0 for weight in numeric_weights.values()):
        return False, "Criteria weights cannot be negative."

    if sum(numeric_weights.values()) <= 0:
        return False, "At least one criterion must have a positive weight."

    if criteria_types is None:
        return False, "Criterion types are required."

    if set(criteria_types.keys()) != set(matrix.columns):
        return False, "A type must be supplied for every criterion."

    allowed_types = {"benefit", "cost"}

    for criterion, criterion_type in criteria_types.items():
        if str(criterion_type).lower() not in allowed_types:
            return (
                False,
                f"Invalid criterion type for '{criterion}'. "
                "Use benefit or cost.",
            )

    return True, None


# ---------------------------------------------------------
# NORMALISE WEIGHTS
# ---------------------------------------------------------

def normalize_weights(weights):
    """
    Convert criterion weights into proportions
    that add up to 1.
    """

    if not weights:
        raise ValueError("At least one criterion weight is required.")

    numeric_weights = {
        key: float(value)
        for key, value in weights.items()
    }

    if any(value < 0 for value in numeric_weights.values()):
        raise ValueError("Weights cannot be negative.")

    total = sum(numeric_weights.values())

    if total <= 0:
        raise ValueError("Total weight must be greater than zero.")

    return {
        key: value / total
        for key, value in numeric_weights.items()
    }


# ---------------------------------------------------------
# NORMALISE DECISION MATRIX
# ---------------------------------------------------------

def normalize_decision_matrix(
    matrix,
    criteria_types,
):
    """
    Normalise decision values using min-max normalisation.

    Benefit:
        Higher values receive higher scores.

    Cost:
        Lower values receive higher scores.

    When all values are equal, every alternative
    receives a normalised score of 1.
    """

    if not isinstance(matrix, pd.DataFrame) or matrix.empty:
        raise ValueError("A non-empty decision matrix is required.")

    normalized = pd.DataFrame(
        index=matrix.index,
        columns=matrix.columns,
        dtype=float,
    )

    for criterion in matrix.columns:
        values = pd.to_numeric(
            matrix[criterion],
            errors="coerce",
        )

        if values.isnull().any():
            raise ValueError(
                f"Criterion '{criterion}' contains invalid values."
            )

        minimum = values.min()
        maximum = values.max()
        value_range = maximum - minimum

        if value_range == 0:
            normalized[criterion] = 1.0
            continue

        criterion_type = str(
            criteria_types[criterion]
        ).lower()

        if criterion_type == "benefit":
            normalized[criterion] = (
                (values - minimum) / value_range
            )

        elif criterion_type == "cost":
            normalized[criterion] = (
                (maximum - values) / value_range
            )

        else:
            raise ValueError(
                f"Invalid criterion type: {criterion_type}"
            )

    return normalized


# ---------------------------------------------------------
# CALCULATE WEIGHTED SCORES
# ---------------------------------------------------------

def calculate_weighted_scores(
    matrix,
    weights,
    criteria_types,
):
    """
    Calculate weighted scores for every alternative.

    Returns:
        DataFrame containing:
        - Normalised criterion values
        - Weighted total score
        - Ranking
    """

    is_valid, error = validate_decision_matrix(
        matrix,
        weights,
        criteria_types,
    )

    if not is_valid:
        raise ValueError(error)

    numeric_matrix = matrix.astype(float)

    normalized_weights = normalize_weights(weights)

    normalized_matrix = normalize_decision_matrix(
        numeric_matrix,
        criteria_types,
    )

    weighted_matrix = normalized_matrix.copy()

    for criterion, weight in normalized_weights.items():
        weighted_matrix[criterion] = (
            normalized_matrix[criterion] * weight
        )

    results = weighted_matrix.copy()

    results["Total Score"] = weighted_matrix.sum(axis=1)

    results["Rank"] = (
        results["Total Score"]
        .rank(method="min", ascending=False)
        .astype(int)
    )

    results = results.sort_values(
        by=["Total Score"],
        ascending=False,
    )

    return results


# ---------------------------------------------------------
# GET BEST ALTERNATIVE
# ---------------------------------------------------------

def get_best_alternative(
    matrix,
    weights,
    criteria_types,
):
    """
    Return the highest-ranked alternative.
    """

    results = calculate_weighted_scores(
        matrix,
        weights,
        criteria_types,
    )

    best_name = results.index[0]

    return {
        "alternative": best_name,
        "score": float(results.iloc[0]["Total Score"]),
        "rank": int(results.iloc[0]["Rank"]),
        "results": results,
    }


# ---------------------------------------------------------
# COMPARE ALTERNATIVES
# ---------------------------------------------------------

def compare_alternatives(
    matrix,
    weights,
    criteria_types,
):
    """
    Produce a comparison report for all alternatives.
    """

    results = calculate_weighted_scores(
        matrix,
        weights,
        criteria_types,
    )

    comparison = results.reset_index()

    comparison = comparison.rename(
        columns={
            comparison.columns[0]: "Alternative"
        }
    )

    return comparison


# ---------------------------------------------------------
# SENSITIVITY ANALYSIS
# ---------------------------------------------------------

def run_sensitivity_analysis(
    matrix,
    weights,
    criteria_types,
    adjustment_percentage=20,
):
    """
    Test how increasing each criterion's weight
    affects the final ranking.

    The selected criterion weight is increased by
    the requested percentage. All weights are then
    normalised again.

    Returns:
        DataFrame showing ranking changes.
    """

    is_valid, error = validate_decision_matrix(
        matrix,
        weights,
        criteria_types,
    )

    if not is_valid:
        raise ValueError(error)

    adjustment_percentage = float(adjustment_percentage)

    if adjustment_percentage < 0:
        raise ValueError(
            "Adjustment percentage cannot be negative."
        )

    baseline = calculate_weighted_scores(
        matrix,
        weights,
        criteria_types,
    )

    baseline_ranks = baseline["Rank"].to_dict()

    records = []

    for changed_criterion in weights:

        adjusted_weights = {
            criterion: float(weight)
            for criterion, weight in weights.items()
        }

        original_weight = adjusted_weights[changed_criterion]

        adjusted_weights[changed_criterion] = (
            original_weight
            * (1 + adjustment_percentage / 100)
        )

        adjusted_results = calculate_weighted_scores(
            matrix,
            adjusted_weights,
            criteria_types,
        )

        for alternative in adjusted_results.index:

            new_rank = int(
                adjusted_results.loc[alternative, "Rank"]
            )

            old_rank = int(
                baseline_ranks[alternative]
            )

            records.append({
                "Changed Criterion": changed_criterion,
                "Alternative": alternative,
                "Original Rank": old_rank,
                "Adjusted Rank": new_rank,
                "Rank Change": old_rank - new_rank,
                "Adjusted Score": float(
                    adjusted_results.loc[
                        alternative,
                        "Total Score"
                    ]
                ),
            })

    return pd.DataFrame(records)


# ---------------------------------------------------------
# WEIGHT DISTRIBUTION
# ---------------------------------------------------------

def get_weight_distribution(weights):
    """
    Return normalised weights as a DataFrame.
    """

    normalized = normalize_weights(weights)

    return pd.DataFrame([
        {
            "Criterion": criterion,
            "Weight": weight,
            "Percentage": weight * 100,
        }
        for criterion, weight in normalized.items()
    ])


# ---------------------------------------------------------
# DECISION SUMMARY
# ---------------------------------------------------------

def generate_decision_summary(
    matrix,
    weights,
    criteria_types,
):
    """
    Generate a summary of the decision analysis.
    """

    results = calculate_weighted_scores(
        matrix,
        weights,
        criteria_types,
    )

    best_alternative = results.index[0]

    worst_alternative = results.index[-1]

    best_score = float(
        results.iloc[0]["Total Score"]
    )

    worst_score = float(
        results.iloc[-1]["Total Score"]
    )

    return {
        "number_of_alternatives": len(matrix),
        "number_of_criteria": len(matrix.columns),
        "best_alternative": best_alternative,
        "best_score": best_score,
        "worst_alternative": worst_alternative,
        "worst_score": worst_score,
        "score_difference": best_score - worst_score,
        "ranking": results[["Total Score", "Rank"]].to_dict(
            orient="index"
        ),
    }
