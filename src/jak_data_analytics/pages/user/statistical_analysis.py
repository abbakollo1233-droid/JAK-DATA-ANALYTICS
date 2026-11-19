"""
JAK Data Analytics
Statistical Analysis Module

Provides descriptive and inferential statistical tools.
Uses native Streamlit components and Plotly charts.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from scipy import stats

from ...ui.layout import (
    render_topbar,
    render_page_intro,
    render_section_heading,
)

from ...ui.theme import show_footer


# ==========================================
# DATASET MANAGEMENT
# ==========================================

def get_datasets():
    """Retrieve available datasets."""

    return st.session_state.get("jak_datasets", [])


def render_statistics_hero():
    """Display the statistical analysis introduction."""

    with st.container(border=True):
        st.subheader("📊 Statistical Analysis Studio")

        st.write(
            "Discover patterns, measure relationships, "
            "understand distributions and generate "
            "statistical insights from your datasets."
        )


def render_dataset_selector():
    """Allow users to select a dataset."""

    datasets = get_datasets()

    if not datasets:
        st.warning("No datasets available. Upload a dataset first.")
        return None, None

    options = {
        item["name"]: item
        for item in datasets
        if isinstance(item, dict)
        and isinstance(item.get("data"), pd.DataFrame)
    }

    if not options:
        st.warning("No valid datasets are available.")
        return None, None

    selected_name = st.selectbox(
        "Select Dataset",
        list(options.keys()),
        key="jak_statistics_dataset"
    )

    return options[selected_name], selected_name


# ==========================================
# DATA PREPARATION
# ==========================================

def get_numeric_data(data):
    """Return numeric columns with at least one valid value."""

    numeric = data.select_dtypes(include="number")

    return numeric.dropna(how="all")


def get_categorical_data(data):
    """Return categorical columns."""

    return data.select_dtypes(
        include=["object", "string", "category", "bool"]
    )


# ==========================================
# DATASET OVERVIEW
# ==========================================

def render_overview(data):
    """Display dataset statistics."""

    numeric = get_numeric_data(data)
    categorical = get_categorical_data(data)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Records", f"{len(data):,}")

    col2.metric("Total Variables", f"{len(data.columns):,}")

    col3.metric("Numeric Variables", len(numeric.columns))

    col4.metric("Categorical Variables", len(categorical.columns))


# ==========================================
# DESCRIPTIVE STATISTICS
# ==========================================

def render_descriptive_statistics(data):
    """Display descriptive statistical measures."""

    render_section_heading(
        "Descriptive Statistics",
        "Understand the central tendency and spread of your data."
    )

    numeric = get_numeric_data(data)

    if numeric.empty:
        st.info(
            "No numeric columns are available for descriptive statistics."
        )
        return

    summary = numeric.describe().T

    summary["Median"] = numeric.median()
    summary["Variance"] = numeric.var()
    summary["Skewness"] = numeric.skew()
    summary["Kurtosis"] = numeric.kurtosis()
    summary["Missing Values"] = numeric.isna().sum()

    st.dataframe(
        summary.round(3),
        use_container_width=True
    )

    st.download_button(
        "⬇️ Download Statistical Summary",
        data=summary.to_csv().encode("utf-8"),
        file_name="jak_statistical_summary.csv",
        mime="text/csv",
        use_container_width=True
    )


# ==========================================
# CENTRAL TENDENCY
# ==========================================

def render_central_tendency(data):
    """Calculate mean, median and mode."""

    render_section_heading(
        "Measures of Central Tendency",
        "Compare mean, median and mode."
    )

    numeric = get_numeric_data(data)

    if numeric.empty:
        st.info("No numeric variables available.")
        return

    column = st.selectbox(
        "Select Numeric Variable",
        numeric.columns.tolist(),
        key="jak_central_tendency_column"
    )

    values = numeric[column].dropna()

    if values.empty:
        st.warning("This column has no valid numeric values.")
        return

    mode_values = values.mode()

    mean_value = values.mean()
    median_value = values.median()

    mode_value = (
        mode_values.iloc[0]
        if not mode_values.empty
        else np.nan
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Mean", f"{mean_value:,.3f}")
    col2.metric("Median", f"{median_value:,.3f}")

    col3.metric(
        "Mode",
        f"{mode_value:,.3f}" if pd.notna(mode_value) else "N/A"
    )


# ==========================================
# DISPERSION ANALYSIS
# ==========================================

def render_dispersion_analysis(data):
    """Calculate measures of dispersion."""

    render_section_heading(
        "Measures of Dispersion",
        "Understand how widely values are spread."
    )

    numeric = get_numeric_data(data)

    if numeric.empty:
        st.info("No numeric variables available.")
        return

    column = st.selectbox(
        "Select Variable",
        numeric.columns.tolist(),
        key="jak_dispersion_column"
    )

    values = numeric[column].dropna()

    if values.empty:
        st.warning("No valid values available.")
        return

    variance = values.var()
    std = values.std()
    value_range = values.max() - values.min()

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Variance",
        f"{variance:,.3f}" if pd.notna(variance) else "N/A"
    )

    col2.metric(
        "Standard Deviation",
        f"{std:,.3f}" if pd.notna(std) else "N/A"
    )

    col3.metric("Range", f"{value_range:,.3f}")

    st.write(f"**First Quartile (Q1):** {q1:,.3f}")
    st.write(f"**Third Quartile (Q3):** {q3:,.3f}")
    st.write(f"**Interquartile Range:** {iqr:,.3f}")


# ==========================================
# DISTRIBUTION ANALYSIS
# ==========================================

def render_distribution_analysis(data):
    """Visualize numeric data distributions."""

    render_section_heading(
        "Distribution Analysis",
        "Explore how values are distributed."
    )

    numeric = get_numeric_data(data)

    if numeric.empty:
        st.info("No numeric variables available.")
        return

    column = st.selectbox(
        "Select Variable",
        numeric.columns.tolist(),
        key="jak_distribution_column"
    )

    values = numeric[column].dropna()

    if values.empty:
        st.warning("No valid values available.")
        return

    fig = px.histogram(
        x=values,
        nbins=30,
        marginal="box",
        title=f"Distribution of {column}",
        labels={"x": column}
    )

    fig.update_layout(
        template="plotly_white",
        height=450
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    skewness = values.skew()

    if pd.isna(skewness):
        st.info("Skewness cannot be calculated for this variable.")

    elif skewness > 0.5:
        st.info(
            f"The distribution is positively skewed. "
            f"Skewness: {skewness:.3f}"
        )

    elif skewness < -0.5:
        st.info(
            f"The distribution is negatively skewed. "
            f"Skewness: {skewness:.3f}"
        )

    else:
        st.info(
            f"The distribution is approximately symmetric. "
            f"Skewness: {skewness:.3f}"
        )


# ==========================================
# CORRELATION ANALYSIS
# ==========================================

def render_correlation_analysis(data):
    """Calculate and visualize correlations."""

    render_section_heading(
        "Correlation Analysis",
        "Measure relationships between numeric variables."
    )

    numeric = get_numeric_data(data)

    if len(numeric.columns) < 2:
        st.info("At least two numeric variables are required.")
        return

    method = st.selectbox(
        "Correlation Method",
        ["Pearson", "Spearman", "Kendall"],
        key="jak_correlation_method"
    )

    correlation = numeric.corr(
        method=method.lower()
    )

    if correlation.empty:
        st.info("Correlation could not be calculated.")
        return

    fig = px.imshow(
        correlation,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title=f"{method} Correlation Matrix"
    )

    fig.update_layout(
        height=550,
        template="plotly_white"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.caption(
        "Correlation measures association, not causation. "
        "Pearson measures linear association, while Spearman "
        "and Kendall use rank-based relationships."
    )


# ==========================================
# STATISTICAL TEST RESULT
# ==========================================

def display_test_result(statistic, p_value, alpha):
    """Display hypothesis test results."""

    st.subheader("Test Results")

    if not np.isfinite(statistic) or not np.isfinite(p_value):
        st.warning(
            "The test produced an undefined result. "
            "Check your sample data and assumptions."
        )
        return

    col1, col2 = st.columns(2)

    col1.metric(
        "Test Statistic",
        f"{statistic:.4f}"
    )

    col2.metric(
        "P-Value",
        f"{p_value:.6f}"
    )

    if p_value < alpha:
        st.success(
            "Reject the null hypothesis at the selected "
            "significance level."
        )
    else:
        st.info(
            "Fail to reject the null hypothesis at the selected "
            "significance level."
        )

    st.caption(
        "Statistical significance does not necessarily imply "
        "practical importance or causation."
    )


# ==========================================
# HYPOTHESIS TESTING
# ==========================================

def render_hypothesis_testing(data):
    """Perform basic inferential statistical tests."""

    render_section_heading(
        "Hypothesis Testing",
        "Perform basic statistical significance tests."
    )

    numeric = get_numeric_data(data)
    categorical = get_categorical_data(data)

    if numeric.empty:
        st.info("Numeric columns are required for these tests.")
        return

    test_type = st.selectbox(
        "Select Statistical Test",
        [
            "One-Sample T-Test",
            "Independent Two-Sample T-Test",
            "Paired T-Test",
            "One-Way ANOVA",
            "Chi-Square Test"
        ],
        key="jak_hypothesis_test_type"
    )

    alpha = st.number_input(
        "Significance Level (Alpha)",
        min_value=0.001,
        max_value=0.20,
        value=0.05,
        step=0.01,
        format="%.3f",
        key="jak_test_alpha"
    )

    # ONE-SAMPLE T-TEST

    if test_type == "One-Sample T-Test":

        column = st.selectbox(
            "Select Variable",
            numeric.columns,
            key="jak_one_sample_column"
        )

        hypothesized_mean = st.number_input(
            "Hypothesized Population Mean",
            value=0.0,
            key="jak_hypothesized_mean"
        )

        if st.button(
            "Run One-Sample T-Test",
            key="jak_run_one_sample"
        ):

            values = numeric[column].dropna()

            if len(values) < 2:
                st.error("At least two observations are required.")
                return

            statistic, p_value = stats.ttest_1samp(
                values,
                hypothesized_mean
            )

            display_test_result(statistic, p_value, alpha)

    # INDEPENDENT T-TEST

    elif test_type == "Independent Two-Sample T-Test":

        if categorical.empty:
            st.warning("A categorical grouping column is required.")
            return

        column = st.selectbox(
            "Numeric Variable",
            numeric.columns,
            key="jak_independent_numeric"
        )

        group_column = st.selectbox(
            "Grouping Variable",
            categorical.columns,
            key="jak_independent_group"
        )

        categories = data[group_column].dropna().unique()

        if len(categories) < 2:
            st.warning("The grouping variable needs at least two categories.")
            return

        group1 = st.selectbox(
            "First Group",
            categories,
            key="jak_independent_group1"
        )

        remaining_groups = [
            item for item in categories
            if item != group1
        ]

        group2 = st.selectbox(
            "Second Group",
            remaining_groups,
            key="jak_independent_group2"
        )

        if st.button(
            "Run Independent T-Test",
            key="jak_run_independent"
        ):

            first = pd.to_numeric(
                data.loc[
                    data[group_column] == group1,
                    column
                ],
                errors="coerce"
            ).dropna()

            second = pd.to_numeric(
                data.loc[
                    data[group_column] == group2,
                    column
                ],
                errors="coerce"
            ).dropna()

            if len(first) < 2 or len(second) < 2:
                st.error(
                    "Each group needs at least two valid observations."
                )
                return

            statistic, p_value = stats.ttest_ind(
                first,
                second,
                equal_var=False
            )

            display_test_result(statistic, p_value, alpha)

    # PAIRED T-TEST

    elif test_type == "Paired T-Test":

        first_column, second_column = st.columns(2)

        with first_column:
            first = st.selectbox(
                "First Measurement",
                numeric.columns,
                key="jak_paired_first"
            )

        with second_column:
            second = st.selectbox(
                "Second Measurement",
                numeric.columns,
                key="jak_paired_second"
            )

        if first == second:
            st.warning("Select two different measurement columns.")
            return

        if st.button(
            "Run Paired T-Test",
            key="jak_run_paired"
        ):

            paired = data[
                [first, second]
            ].apply(
                pd.to_numeric,
                errors="coerce"
            ).dropna()

            if len(paired) < 2:
                st.error("At least two complete pairs are required.")
                return

            statistic, p_value = stats.ttest_rel(
                paired[first],
                paired[second]
            )

            display_test_result(statistic, p_value, alpha)

    # ONE-WAY ANOVA

    elif test_type == "One-Way ANOVA":

        if categorical.empty:
            st.warning("A categorical grouping column is required.")
            return

        column = st.selectbox(
            "Numeric Variable",
            numeric.columns,
            key="jak_anova_numeric"
        )

        group_column = st.selectbox(
            "Grouping Variable",
            categorical.columns,
            key="jak_anova_group"
        )

        if st.button(
            "Run ANOVA",
            key="jak_run_anova"
        ):

            grouped_data = data[
                [group_column, column]
            ].copy()

            grouped_data[column] = pd.to_numeric(
                grouped_data[column],
                errors="coerce"
            )

            grouped_data = grouped_data.dropna()

            group_values = [
                group[column].values
                for _, group in grouped_data.groupby(group_column)
                if len(group) > 0
            ]

            if len(group_values) < 2:
                st.error("At least two non-empty groups are required.")
                return

            statistic, p_value = stats.f_oneway(
                *group_values
            )

            display_test_result(statistic, p_value, alpha)

    # CHI-SQUARE TEST

    elif test_type == "Chi-Square Test":

        if len(categorical.columns) < 2:
            st.warning(
                "At least two categorical variables are required."
            )
            return

        col1, col2 = st.columns(2)

        with col1:
            first = st.selectbox(
                "First Categorical Variable",
                categorical.columns,
                key="jak_chi_first"
            )

        with col2:
            second = st.selectbox(
                "Second Categorical Variable",
                categorical.columns,
                index=1,
                key="jak_chi_second"
            )

        if first == second:
            st.warning("Select two different categorical variables.")
            return

        if st.button(
            "Run Chi-Square Test",
            key="jak_run_chi_square"
        ):

            table = pd.crosstab(
                data[first],
                data[second]
            )

            if table.shape[0] < 2 or table.shape[1] < 2:
                st.error(
                    "The contingency table needs at least two rows "
                    "and two columns."
                )
                return

            statistic, p_value, dof, expected = (
                stats.chi2_contingency(table)
            )

            display_test_result(statistic, p_value, alpha)

            st.write("Degrees of Freedom:", dof)

            if (expected < 5).any():
                st.warning(
                    "Some expected cell counts are below 5. "
                    "The chi-square approximation may be unreliable."
                )


# ==========================================
# OUTLIER ANALYSIS
# ==========================================

def render_outlier_analysis(data):
    """Detect outliers using the IQR method."""

    render_section_heading(
        "Outlier Detection",
        "Identify unusually high or low numeric observations."
    )

    numeric = get_numeric_data(data)

    if numeric.empty:
        st.info("No numeric variables available.")
        return

    column = st.selectbox(
        "Select Variable",
        numeric.columns,
        key="jak_outlier_column"
    )

    values = numeric[column].dropna()

    if values.empty:
        st.warning("No valid values available.")
        return

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)

    iqr = q3 - q1

    lower = q1 - (1.5 * iqr)
    upper = q3 + (1.5 * iqr)

    outlier_mask = (
        (data[column] < lower)
        | (data[column] > upper)
    )

    outliers = data.loc[
        outlier_mask.fillna(False)
    ]

    col1, col2, col3 = st.columns(3)

    col1.metric("Lower Boundary", f"{lower:,.3f}")
    col2.metric("Upper Boundary", f"{upper:,.3f}")
    col3.metric("Outliers", f"{len(outliers):,}")

    if not outliers.empty:

        st.subheader("Detected Outlier Records")

        st.dataframe(
            outliers,
            use_container_width=True
        )

        st.caption(
            "Outliers are flagged for investigation. "
            "They are not automatically removed."
        )

    else:
        st.success(
            "No outliers detected using the 1.5 × IQR rule."
        )


# ==========================================
# MAIN STATISTICAL ANALYSIS PAGE
# ==========================================

def render_statistical_analysis_page():
    """Main statistical analysis page."""

    username = st.session_state.get(
        "jak_user_name",
        "Guest"
    )

    role = st.session_state.get(
        "jak_user_role",
        "User"
    )

    render_topbar(
        username=username,
        role=role
    )

    render_page_intro(
        "Statistical Analysis",
        "Explore your data using statistical methods and tests."
    )

    render_statistics_hero()

    selected_dataset, dataset_name = render_dataset_selector()

    if selected_dataset is None:
        show_footer()
        return

    data = selected_dataset["data"].copy()

    if data.empty:
        st.warning("The selected dataset is empty.")
        show_footer()
        return

    st.divider()

    render_overview(data)

    st.divider()

    tabs = st.tabs([
        "Descriptive Statistics",
        "Central Tendency",
        "Dispersion",
        "Distribution",
        "Correlation",
        "Hypothesis Testing",
        "Outliers"
    ])

    with tabs[0]:
        render_descriptive_statistics(data)

    with tabs[1]:
        render_central_tendency(data)

    with tabs[2]:
        render_dispersion_analysis(data)

    with tabs[3]:
        render_distribution_analysis(data)

    with tabs[4]:
        render_correlation_analysis(data)

    with tabs[5]:
        render_hypothesis_testing(data)

    with tabs[6]:
        render_outlier_analysis(data)

    show_footer()


# ==========================================
# COMPATIBILITY ALIASES
# ==========================================

render_statistical_analysis = render_statistical_analysis_page