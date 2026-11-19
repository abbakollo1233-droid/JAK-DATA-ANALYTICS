"""
JAK Data Analytics
Data Profiling Module

Provides intelligent dataset profiling, statistical summaries,
data quality assessment and interactive visualizations.

Uses native Streamlit components without HTML.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from ...ui.layout import (
    render_topbar,
    render_page_intro,
    render_section_heading,
)

from ...ui.theme import show_footer


# =====================================================
# DATASET STORAGE
# =====================================================

def get_datasets():
    """Retrieve datasets from the current session."""

    return st.session_state.get("jak_datasets", [])


# =====================================================
# DATA QUALITY SCORE
# =====================================================

def calculate_quality_score(data):
    """
    Calculate an initial data quality indicator.

    Considers missing values and duplicate rows.
    This is not a complete measure of data correctness.
    """

    if data.empty or len(data.columns) == 0:
        return 0

    total_cells = data.size

    missing_cells = int(data.isna().sum().sum())

    duplicate_rows = int(data.duplicated().sum())

    missing_rate = missing_cells / total_cells

    duplicate_rate = duplicate_rows / len(data)

    score = 100 - (
        missing_rate * 70
        + duplicate_rate * 30
    )

    return round(max(0, min(100, score)), 2)


# =====================================================
# DATA SUMMARY
# =====================================================

def get_data_summary(data):
    """Generate general dataset information."""

    return {
        "rows": len(data),
        "columns": len(data.columns),
        "missing_values": int(data.isna().sum().sum()),
        "duplicate_rows": int(data.duplicated().sum()),

        "numeric_columns": len(
            data.select_dtypes(include="number").columns
        ),

        "categorical_columns": len(
            data.select_dtypes(
                include=["object", "category", "string", "bool"]
            ).columns
        ),

        "datetime_columns": len(
            data.select_dtypes(include=["datetime"]).columns
        ),
    }


# =====================================================
# PROFILING INTRODUCTION
# =====================================================

def render_profiling_hero():
    """Display the profiling introduction."""

    with st.container(border=True):

        st.subheader("🔍 Intelligent Data Profiling")

        st.write(
            "Automatically understand your datasets. "
            "Examine data structures, identify missing values, "
            "detect duplicates and evaluate data quality."
        )


# =====================================================
# DATASET SELECTOR
# =====================================================

def render_dataset_selector():
    """Allow users to select a dataset."""

    datasets = get_datasets()

    if not datasets:
        st.warning(
            "No datasets found. Upload a dataset first "
            "from the Dataset Management page."
        )
        return None

    dataset_names = {
        item["name"]: item
        for item in datasets
        if isinstance(item, dict)
        and "name" in item
        and isinstance(item.get("data"), pd.DataFrame)
    }

    if not dataset_names:
        st.warning(
            "No valid datasets are available for profiling."
        )
        return None

    selected_name = st.selectbox(
        "Select Dataset to Profile",
        list(dataset_names.keys()),
        key="jak_profiling_dataset"
    )

    return dataset_names[selected_name]["data"]


# =====================================================
# OVERVIEW METRICS
# =====================================================

def render_overview_metrics(data):
    """Display dataset overview metrics."""

    summary = get_data_summary(data)

    quality_score = calculate_quality_score(data)

    render_section_heading(
        "Dataset Overview",
        "A quick summary of your selected dataset."
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Rows",
        f"{summary['rows']:,}"
    )

    col2.metric(
        "Total Columns",
        f"{summary['columns']:,}"
    )

    col3.metric(
        "Missing Values",
        f"{summary['missing_values']:,}"
    )

    col4.metric(
        "Quality Indicator",
        f"{quality_score}%"
    )

    st.progress(
        quality_score / 100,
        text=f"Data quality indicator: {quality_score}%"
    )


# =====================================================
# COLUMN INFORMATION
# =====================================================

def render_column_information(data):
    """Display information about every column."""

    render_section_heading(
        "Column Information",
        "Examine the structure and characteristics of each column."
    )

    column_data = []

    for column in data.columns:

        series = data[column]

        column_data.append({
            "Column": str(column),
            "Data Type": str(series.dtype),
            "Non-Null Values": int(series.count()),
            "Missing Values": int(series.isna().sum()),
            "Unique Values": int(series.nunique()),
            "Missing (%)": round(
                series.isna().mean() * 100,
                2
            ),
        })

    profile_df = pd.DataFrame(column_data)

    st.dataframe(
        profile_df,
        use_container_width=True,
        hide_index=True
    )

    return profile_df


# =====================================================
# MISSING VALUES ANALYSIS
# =====================================================

def render_missing_values_analysis(data):
    """Analyze missing values."""

    render_section_heading(
        "Missing Values Analysis",
        "Identify columns containing incomplete records."
    )

    missing = data.isna().sum()

    missing = missing[
        missing > 0
    ].sort_values(ascending=False)

    if missing.empty:
        st.success(
            "Excellent! No missing values were detected."
        )
        return

    missing_df = pd.DataFrame({
        "Column": missing.index.astype(str),
        "Missing Values": missing.values,
        "Missing Percentage": (
            missing.values / len(data) * 100
        ).round(2)
    })

    col1, col2 = st.columns([2, 1])

    with col1:

        fig = px.bar(
            missing_df,
            x="Column",
            y="Missing Values",
            color="Missing Values",
            title="Missing Values by Column",
            text="Missing Values"
        )

        fig.update_layout(
            template="plotly_white",
            height=380
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        st.dataframe(
            missing_df,
            use_container_width=True,
            hide_index=True
        )


# =====================================================
# DUPLICATE ANALYSIS
# =====================================================

def render_duplicate_analysis(data):
    """Analyze duplicate records."""

    render_section_heading(
        "Duplicate Records Analysis",
        "Identify repeated rows in your dataset."
    )

    duplicate_count = int(data.duplicated().sum())

    unique_count = len(data) - duplicate_count

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Records",
        f"{len(data):,}"
    )

    col2.metric(
        "Duplicate Records",
        f"{duplicate_count:,}"
    )

    col3.metric(
        "Unique Records",
        f"{unique_count:,}"
    )

    if duplicate_count == 0:

        st.success(
            "No duplicate records were detected."
        )

    else:

        st.warning(
            f"{duplicate_count:,} duplicate rows were detected."
        )

        if st.checkbox(
            "Preview duplicate records",
            key="jak_profile_duplicate_preview"
        ):

            duplicates = data[
                data.duplicated(keep=False)
            ]

            st.dataframe(
                duplicates,
                use_container_width=True
            )


# =====================================================
# STATISTICAL SUMMARY
# =====================================================

def render_statistical_summary(data):
    """Display descriptive statistics."""

    render_section_heading(
        "Statistical Summary",
        "Understand numerical distributions and measurements."
    )

    numeric_data = data.select_dtypes(
        include="number"
    )

    if numeric_data.empty:

        st.info(
            "No numerical columns were found in this dataset."
        )
        return

    statistics = numeric_data.describe().T

    statistics["missing"] = numeric_data.isna().sum()

    statistics["unique"] = numeric_data.nunique()

    st.dataframe(
        statistics,
        use_container_width=True
    )


# =====================================================
# CATEGORICAL SUMMARY
# =====================================================

def render_categorical_summary(data):
    """Display categorical column summaries."""

    render_section_heading(
        "Categorical Data Summary",
        "Understand categories and their frequency."
    )

    categorical_data = data.select_dtypes(
        include=["object", "category", "string", "bool"]
    )

    if categorical_data.empty:

        st.info(
            "No categorical columns were found."
        )
        return

    selected_column = st.selectbox(
        "Select Categorical Column",
        categorical_data.columns,
        key="jak_profile_categorical_column"
    )

    frequencies = (
        data[selected_column]
        .astype("string")
        .fillna("(Missing)")
        .value_counts()
        .head(20)
        .reset_index()
    )

    frequencies.columns = [
        "Value",
        "Frequency"
    ]

    fig = px.bar(
        frequencies,
        x="Value",
        y="Frequency",
        title=f"Value Distribution: {selected_column}",
        text="Frequency"
    )

    fig.update_layout(
        template="plotly_white",
        height=400
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.dataframe(
        frequencies,
        use_container_width=True,
        hide_index=True
    )


# =====================================================
# CORRELATION ANALYSIS
# =====================================================

def render_correlation_analysis(data):
    """Display correlation between numerical columns."""

    render_section_heading(
        "Correlation Analysis",
        "Explore relationships between numerical variables."
    )

    numeric_data = data.select_dtypes(
        include="number"
    )

    if numeric_data.shape[1] < 2:

        st.info(
            "At least two numerical columns are required "
            "for correlation analysis."
        )
        return

    correlation = numeric_data.corr()

    fig = px.imshow(
        correlation,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Numerical Correlation Matrix"
    )

    fig.update_layout(
        height=550
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =====================================================
# DATA QUALITY REPORT
# =====================================================

def render_quality_report(data):
    """Generate an initial data quality report."""

    render_section_heading(
        "Data Quality Report",
        "Review potential data quality issues."
    )

    score = calculate_quality_score(data)

    missing_count = int(data.isna().sum().sum())

    duplicate_count = int(data.duplicated().sum())

    st.metric(
        "Overall Quality Indicator",
        f"{score}%"
    )

    if missing_count:

        st.warning(
            f"{missing_count:,} missing cell values detected."
        )

    else:

        st.success(
            "No missing cell values detected."
        )

    if duplicate_count:

        st.warning(
            f"{duplicate_count:,} duplicate rows detected."
        )

    else:

        st.success(
            "No duplicate rows detected."
        )

    constant_columns = [
        column
        for column in data.columns
        if data[column].nunique(dropna=False) <= 1
    ]

    if constant_columns:

        st.warning(
            "Columns with only one distinct value: "
            + ", ".join(map(str, constant_columns))
        )

    else:

        st.success(
            "No constant columns detected."
        )

    st.caption(
        "This is an initial automated quality assessment. "
        "It does not establish that values are accurate, "
        "valid or appropriate for a particular analysis."
    )


# =====================================================
# MAIN PROFILING PAGE
# =====================================================

def render_profiling_page():
    """Main data profiling page."""

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
        "Data Profiling",
        "Automatically inspect and understand your datasets."
    )

    render_profiling_hero()

    data = render_dataset_selector()

    if data is None:

        show_footer()
        return

    if not isinstance(data, pd.DataFrame) or data.empty:

        st.warning(
            "The selected dataset is empty or invalid."
        )

        show_footer()
        return

    st.divider()

    render_overview_metrics(data)

    st.divider()

    render_column_information(data)

    st.divider()

    render_missing_values_analysis(data)

    st.divider()

    render_duplicate_analysis(data)

    st.divider()

    render_statistical_summary(data)

    st.divider()

    render_categorical_summary(data)

    st.divider()

    render_correlation_analysis(data)

    st.divider()

    render_quality_report(data)

    show_footer()


# =====================================================
# PAGE ALIASES
# =====================================================

render_data_profiling = render_profiling_page