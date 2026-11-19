"""
JAK Data Analytics
Statistical Analysis Service

Provides reusable statistical analysis functionality.

Features:
- Descriptive statistics
- Central tendency
- Dispersion
- Distribution analysis
- Correlation analysis
- Hypothesis testing
- Confidence intervals
- Outlier detection
- Frequency analysis

This module does not depend on Streamlit.
"""

import numpy as np
import pandas as pd

from scipy import stats


# ==================================================
# VALIDATION
# ==================================================

def validate_dataframe(data):
    """Validate input DataFrame."""

    if not isinstance(data, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    if data.empty:
        raise ValueError("The dataset is empty.")

    return True


def validate_numeric_series(series):
    """Convert and validate numerical data."""

    values = pd.to_numeric(
        pd.Series(series),
        errors="coerce"
    ).dropna()

    values = values[
        np.isfinite(values)
    ]

    if values.empty:
        raise ValueError(
            "At least one valid numerical value is required."
        )

    return values


def validate_alpha(alpha):
    """Validate statistical significance level."""

    if not 0 < alpha < 1:
        raise ValueError(
            "Significance level must be between 0 and 1."
        )


# ==================================================
# DESCRIPTIVE STATISTICS
# ==================================================

def descriptive_statistics(data):
    """Calculate descriptive statistics for numerical columns."""

    validate_dataframe(data)

    numeric = data.select_dtypes(
        include=np.number
    )

    if numeric.empty:
        return pd.DataFrame()

    result = numeric.describe().T

    result["variance"] = numeric.var()
    result["skewness"] = numeric.skew()
    result["kurtosis"] = numeric.kurtosis()
    result["median"] = numeric.median()
    result["missing_values"] = numeric.isna().sum()

    return result.reset_index(
        names="column"
    )


# ==================================================
# CENTRAL TENDENCY
# ==================================================

def calculate_central_tendency(series):
    """Calculate mean, median and mode."""

    values = validate_numeric_series(series)

    modes = stats.mode(
        values,
        keepdims=False
    )

    return {
        "mean": float(values.mean()),
        "median": float(values.median()),
        "mode": float(modes.mode),
        "mode_frequency": int(modes.count),
    }


# ==================================================
# DISPERSION
# ==================================================

def calculate_dispersion(series):
    """Calculate measures of data dispersion."""

    values = validate_numeric_series(series)

    return {
        "minimum": float(values.min()),
        "maximum": float(values.max()),
        "range": float(values.max() - values.min()),
        "variance": float(values.var(ddof=1))
        if len(values) > 1 else None,
        "standard_deviation": float(values.std(ddof=1))
        if len(values) > 1 else None,
        "interquartile_range": float(
            values.quantile(0.75) - values.quantile(0.25)
        ),
        "coefficient_of_variation": (
            float(values.std(ddof=1) / abs(values.mean()))
            if len(values) > 1 and values.mean() != 0
            else None
        ),
    }


# ==================================================
# DISTRIBUTION ANALYSIS
# ==================================================

def analyze_distribution(series):
    """Analyse numerical distribution characteristics."""

    values = validate_numeric_series(series)

    skewness = float(stats.skew(values))
    kurtosis = float(stats.kurtosis(values))

    if skewness > 0.5:
        shape = "Right-skewed"

    elif skewness < -0.5:
        shape = "Left-skewed"

    else:
        shape = "Approximately symmetric"

    if len(values) >= 3 and values.nunique() > 1:
        normality = stats.shapiro(
            values.sample(
                min(len(values), 5000),
                random_state=42
            )
        )

        normality_p_value = float(
            normality.pvalue
        )

    else:
        normality_p_value = None

    return {
        "skewness": skewness,
        "kurtosis": kurtosis,
        "distribution_shape": shape,
        "normality_p_value": normality_p_value,
        "sample_size": len(values),
    }


# ==================================================
# CORRELATION ANALYSIS
# ==================================================

def correlation_analysis(
    data,
    method="pearson"
):
    """Calculate correlations between numerical columns."""

    validate_dataframe(data)

    allowed = [
        "pearson",
        "spearman",
        "kendall",
    ]

    if method not in allowed:
        raise ValueError(
            "Unsupported correlation method."
        )

    numeric = data.select_dtypes(
        include=np.number
    )

    if numeric.shape[1] < 2:
        raise ValueError(
            "At least two numerical columns are required."
        )

    return numeric.corr(
        method=method
    )


# ==================================================
# CORRELATION SIGNIFICANCE
# ==================================================

def calculate_correlation(
    series_a,
    series_b,
    method="pearson"
):
    """Calculate correlation and its statistical significance."""

    if method not in [
        "pearson",
        "spearman",
        "kendall",
    ]:
        raise ValueError(
            "Unsupported correlation method."
        )

    left = pd.to_numeric(
        pd.Series(series_a),
        errors="coerce"
    )

    right = pd.to_numeric(
        pd.Series(series_b),
        errors="coerce"
    )

    paired = pd.concat(
        [left, right],
        axis=1
    ).replace(
        [np.inf, -np.inf],
        np.nan
    ).dropna()

    if len(paired) < 3:
        raise ValueError(
            "At least three valid paired observations are required."
        )

    if paired.iloc[:, 0].nunique() < 2:
        raise ValueError(
            "The first variable must contain variation."
        )

    if paired.iloc[:, 1].nunique() < 2:
        raise ValueError(
            "The second variable must contain variation."
        )

    if method == "pearson":
        result = stats.pearsonr(
            paired.iloc[:, 0],
            paired.iloc[:, 1]
        )

    elif method == "spearman":
        result = stats.spearmanr(
            paired.iloc[:, 0],
            paired.iloc[:, 1]
        )

    else:
        result = stats.kendalltau(
            paired.iloc[:, 0],
            paired.iloc[:, 1]
        )

    return {
        "method": method,
        "correlation": float(result.statistic),
        "p_value": float(result.pvalue),
        "sample_size": len(paired),
    }


# ==================================================
# ONE-SAMPLE T-TEST
# ==================================================

def one_sample_t_test(
    series,
    population_mean,
    alpha=0.05
):
    """Compare a sample mean with a hypothesised mean."""

    validate_alpha(alpha)

    values = validate_numeric_series(series)

    if len(values) < 2:
        raise ValueError(
            "At least two observations are required."
        )

    result = stats.ttest_1samp(
        values,
        popmean=population_mean
    )

    return {
        "test": "One-sample t-test",
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "sample_mean": float(values.mean()),
        "population_mean": float(population_mean),
        "alpha": alpha,
        "significant": bool(result.pvalue < alpha),
    }


# ==================================================
# INDEPENDENT T-TEST
# ==================================================

def independent_t_test(
    group_a,
    group_b,
    alpha=0.05
):
    """Compare two independent numerical groups using Welch's t-test."""

    validate_alpha(alpha)

    first = validate_numeric_series(group_a)
    second = validate_numeric_series(group_b)

    if len(first) < 2 or len(second) < 2:
        raise ValueError(
            "Each group must contain at least two observations."
        )

    result = stats.ttest_ind(
        first,
        second,
        equal_var=False
    )

    return {
        "test": "Welch independent t-test",
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "group_a_mean": float(first.mean()),
        "group_b_mean": float(second.mean()),
        "mean_difference": float(
            first.mean() - second.mean()
        ),
        "alpha": alpha,
        "significant": bool(result.pvalue < alpha),
    }


# ==================================================
# PAIRED T-TEST
# ==================================================

def paired_t_test(
    group_a,
    group_b,
    alpha=0.05
):
    """Compare paired numerical observations."""

    validate_alpha(alpha)

    first = pd.to_numeric(
        pd.Series(group_a),
        errors="coerce"
    )

    second = pd.to_numeric(
        pd.Series(group_b),
        errors="coerce"
    )

    paired = pd.concat(
        [first, second],
        axis=1
    ).replace(
        [np.inf, -np.inf],
        np.nan
    ).dropna()

    if len(paired) < 2:
        raise ValueError(
            "At least two valid paired observations are required."
        )

    result = stats.ttest_rel(
        paired.iloc[:, 0],
        paired.iloc[:, 1]
    )

    return {
        "test": "Paired t-test",
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "sample_size": len(paired),
        "alpha": alpha,
        "significant": bool(result.pvalue < alpha),
    }


# ==================================================
# ONE-WAY ANOVA
# ==================================================

def one_way_anova(
    groups,
    alpha=0.05
):
    """Compare three or more independent numerical groups."""

    validate_alpha(alpha)

    if len(groups) < 2:
        raise ValueError(
            "At least two groups are required."
        )

    cleaned_groups = [
        validate_numeric_series(group).to_numpy()
        for group in groups
    ]

    if any(len(group) < 2 for group in cleaned_groups):
        raise ValueError(
            "Each group must contain at least two observations."
        )

    result = stats.f_oneway(
        *cleaned_groups
    )

    return {
        "test": "One-way ANOVA",
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "number_of_groups": len(cleaned_groups),
        "alpha": alpha,
        "significant": bool(result.pvalue < alpha),
    }


# ==================================================
# CHI-SQUARE TEST
# ==================================================

def chi_square_test(
    contingency_table,
    alpha=0.05
):
    """Test association between categorical variables."""

    validate_alpha(alpha)

    table = np.asarray(
        contingency_table,
        dtype=float
    )

    if table.ndim != 2 or min(table.shape) < 2:
        raise ValueError(
            "A contingency table with at least two rows and columns is required."
        )

    if not np.isfinite(table).all():
        raise ValueError(
            "Contingency table must contain finite values."
        )

    if (table < 0).any():
        raise ValueError(
            "Contingency table cannot contain negative values."
        )

    if (table.sum(axis=0) == 0).any() or (
        table.sum(axis=1) == 0
    ).any():
        raise ValueError(
            "Contingency table cannot contain entirely empty rows or columns."
        )

    result = stats.chi2_contingency(table)

    expected = result.expected_freq

    return {
        "test": "Chi-square test of independence",
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "degrees_of_freedom": int(result.dof),
        "alpha": alpha,
        "significant": bool(result.pvalue < alpha),
        "minimum_expected_frequency": float(expected.min()),
        "expected_cells_below_5": int(
            (expected < 5).sum()
        ),
        "expected_cell_count": int(expected.size),
    }


# ==================================================
# CONFIDENCE INTERVAL
# ==================================================

def calculate_confidence_interval(
    series,
    confidence=0.95
):
    """Calculate a confidence interval for the sample mean."""

    if not 0 < confidence < 1:
        raise ValueError(
            "Confidence must be between 0 and 1."
        )

    values = validate_numeric_series(series)

    if len(values) < 2:
        raise ValueError(
            "At least two observations are required."
        )

    result = stats.t.interval(
        confidence,
        df=len(values) - 1,
        loc=values.mean(),
        scale=stats.sem(values)
    )

    return {
        "confidence_level": confidence,
        "sample_mean": float(values.mean()),
        "lower_bound": float(result.low),
        "upper_bound": float(result.high),
        "sample_size": len(values),
    }


# ==================================================
# OUTLIER DETECTION
# ==================================================

def detect_outliers_iqr(
    series,
    multiplier=1.5
):
    """Detect outliers using the IQR method."""

    if multiplier <= 0:
        raise ValueError(
            "Multiplier must be greater than zero."
        )

    values = validate_numeric_series(series)

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)

    iqr = q3 - q1

    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr

    mask = (
        (values < lower)
        | (values > upper)
    )

    outliers = values[mask]

    return {
        "method": "IQR",
        "lower_bound": float(lower),
        "upper_bound": float(upper),
        "outlier_count": int(len(outliers)),
        "outlier_percentage": round(
            len(outliers) / len(values) * 100,
            2
        ),
        "outlier_values": outliers.tolist(),
    }


# ==================================================
# FREQUENCY ANALYSIS
# ==================================================

def frequency_analysis(
    series,
    top_n=20
):
    """Calculate value frequencies for categorical data."""

    if top_n < 1:
        raise ValueError(
            "Top N must be at least 1."
        )

    values = pd.Series(series).dropna()

    if values.empty:
        return pd.DataFrame(
            columns=[
                "value",
                "frequency",
                "percentage",
            ]
        )

    frequencies = (
        values.value_counts()
        .head(min(top_n, 100))
    )

    result = pd.DataFrame({
        "value": frequencies.index.astype(str),
        "frequency": frequencies.values,
    })

    result["percentage"] = (
        result["frequency"]
        / len(values)
        * 100
    ).round(2)

    return result.reset_index(drop=True)