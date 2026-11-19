"""
JAK Data Analytics
Recommendations Engine

Features:
- Automated dataset insights
- Data quality recommendations
- Statistical recommendations
- Correlation-based insights
- Categorical analysis
- Numerical analysis
- Business improvement suggestions
- Downloadable recommendation reports

Note:
Recommendations are generated using statistical rules.
They are suggestions for investigation, not guaranteed
business outcomes or causal conclusions.
"""

import hashlib

import streamlit as st
import pandas as pd
import plotly.express as px

from ...ui.layout import (
    render_topbar,
    render_page_intro,
    render_section_heading,
)

from ...ui.theme import show_footer


# =========================================================
# INITIALIZATION
# =========================================================

def initialize_recommendation_state():

    if "jak_recommendations" not in st.session_state:
        st.session_state["jak_recommendations"] = None


def get_datasets():
    """Return valid datasets from application session state."""

    datasets = st.session_state.get("jak_datasets", [])

    if not isinstance(datasets, list):
        return []

    return [
        item for item in datasets
        if (
            isinstance(item, dict)
            and isinstance(item.get("data"), pd.DataFrame)
        )
    ]


def get_dataset_fingerprint(data):
    """Generate a fingerprint to detect dataset changes."""

    try:
        hashed_data = pd.util.hash_pandas_object(
            data,
            index=True
        ).values.tobytes()

        metadata = (
            str(data.shape)
            + str(data.columns.tolist())
            + str(data.dtypes.astype(str).tolist())
        ).encode("utf-8")

        return hashlib.sha256(
            metadata + hashed_data
        ).hexdigest()

    except Exception:
        return hashlib.sha256(
            pd.util.hash_pandas_object(
                data.astype(str),
                index=True
            ).values.tobytes()
        ).hexdigest()


def get_numeric_columns(data):

    return data.select_dtypes(
        include="number"
    ).columns.tolist()


def get_categorical_columns(data):

    return data.select_dtypes(
        include=["object", "string", "category", "bool"]
    ).columns.tolist()


# =========================================================
# DATASET SELECTION
# =========================================================

def render_dataset_selector():

    datasets = get_datasets()

    if not datasets:

        st.warning(
            "No datasets available. Upload a dataset first."
        )

        return None, None

    options = {}

    for index, item in enumerate(datasets):

        name = str(
            item.get("name", f"Dataset {index + 1}")
        )

        display_name = name

        if display_name in options:
            display_name = f"{name} ({index + 1})"

        options[display_name] = item

    selected_name = st.selectbox(
        "Select Dataset",
        list(options.keys()),
        key="jak_recommendation_dataset_selector"
    )

    return options[selected_name], selected_name


# =========================================================
# DATASET OVERVIEW
# =========================================================

def render_dataset_overview(data):

    numeric_columns = get_numeric_columns(data)

    categorical_columns = get_categorical_columns(data)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Records",
        f"{len(data):,}"
    )

    col2.metric(
        "Total Columns",
        len(data.columns)
    )

    col3.metric(
        "Numeric Features",
        len(numeric_columns)
    )

    col4.metric(
        "Categorical Features",
        len(categorical_columns)
    )


# =========================================================
# RECOMMENDATION CREATION
# =========================================================

def add_recommendation(
    recommendations,
    category,
    title,
    description,
    action,
    priority="Medium"
):

    recommendations.append({
        "Category": category,
        "Title": title,
        "Description": description,
        "Recommended Action": action,
        "Priority": priority
    })


# =========================================================
# DATA QUALITY RECOMMENDATIONS
# =========================================================

def generate_data_quality_recommendations(data):

    recommendations = []

    total_cells = data.shape[0] * data.shape[1]

    if total_cells == 0:
        return recommendations

    missing_cells = int(
        data.isna().sum().sum()
    )

    missing_percentage = (
        missing_cells / total_cells
    ) * 100

    duplicate_count = int(
        data.duplicated().sum()
    )

    duplicate_percentage = (
        duplicate_count / len(data) * 100
        if len(data) else 0
    )

    # Missing values

    if missing_percentage > 20:

        add_recommendation(
            recommendations,
            "Data Quality",
            "High Missing Data",
            f"{missing_percentage:.2f}% of all dataset cells are missing.",
            "Investigate the affected columns and determine whether missing values should be corrected, imputed or retained.",
            "High"
        )

    elif missing_percentage > 5:

        add_recommendation(
            recommendations,
            "Data Quality",
            "Missing Values Detected",
            f"{missing_percentage:.2f}% of dataset cells contain missing values.",
            "Review columns with missing information and establish an appropriate treatment strategy.",
            "Medium"
        )

    else:

        add_recommendation(
            recommendations,
            "Data Quality",
            "Missing Data Under Control",
            f"Only {missing_percentage:.2f}% of dataset cells are missing.",
            "Continue monitoring missing values as new records are collected.",
            "Low"
        )

    # Duplicate records

    if duplicate_percentage > 10:

        add_recommendation(
            recommendations,
            "Data Quality",
            "High Duplicate Records",
            f"{duplicate_count:,} duplicate rows were detected.",
            "Investigate duplicate records and remove only those confirmed to be unintended.",
            "High"
        )

    elif duplicate_count > 0:

        add_recommendation(
            recommendations,
            "Data Quality",
            "Duplicate Records Found",
            f"{duplicate_count:,} duplicate rows were detected.",
            "Check whether repeated records represent legitimate repeated events or accidental duplication.",
            "Medium"
        )

    # Constant columns

    constant_columns = [
        column
        for column in data.columns
        if data[column].nunique(dropna=True) <= 1
    ]

    if constant_columns:

        add_recommendation(
            recommendations,
            "Data Quality",
            "Constant Columns",
            f"{len(constant_columns)} columns contain only one distinct non-missing value.",
            "Review these columns. They may not contribute useful information to analysis or modelling.",
            "Low"
        )

    return recommendations


# =========================================================
# NUMERICAL RECOMMENDATIONS
# =========================================================

def generate_numeric_recommendations(data):

    recommendations = []

    numeric = data.select_dtypes(
        include="number"
    )

    if numeric.empty:
        return recommendations

    for column in numeric.columns:

        series = numeric[column].dropna()

        if len(series) < 5:
            continue

        if series.nunique() <= 1:
            continue

        missing_percentage = (
            data[column].isna().mean() * 100
        )

        if missing_percentage > 20:

            add_recommendation(
                recommendations,
                "Numerical Analysis",
                f"Review {column}",
                f"{missing_percentage:.2f}% of values in this column are missing.",
                f"Investigate the collection process for {column} before relying on its statistical results.",
                "High"
            )

        # Skewness

        skewness = series.skew()

        if pd.notna(skewness) and abs(skewness) > 2:

            direction = (
                "right" if skewness > 0 else "left"
            )

            add_recommendation(
                recommendations,
                "Numerical Analysis",
                f"Highly Skewed Variable: {column}",
                f"The distribution of {column} is strongly skewed to the {direction}.",
                "Inspect the distribution and extreme values. Consider a suitable transformation only if it makes analytical sense.",
                "Medium"
            )

        # IQR-based unusual values

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)

        iqr = q3 - q1

        if iqr > 0:

            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

            unusual_count = int(
                (
                    (series < lower)
                    | (series > upper)
                ).sum()
            )

            if unusual_count > 0:

                unusual_percentage = (
                    unusual_count / len(series) * 100
                )

                if unusual_percentage >= 5:

                    add_recommendation(
                        recommendations,
                        "Numerical Analysis",
                        f"Investigate Unusual Values: {column}",
                        f"{unusual_count:,} observations ({unusual_percentage:.2f}%) fall outside the IQR thresholds.",
                        f"Review unusual values in {column} and determine whether they are valid observations or data errors.",
                        "Medium"
                    )

    return recommendations


# =========================================================
# CORRELATION RECOMMENDATIONS
# =========================================================

def generate_correlation_recommendations(data):

    recommendations = []

    numeric = data.select_dtypes(
        include="number"
    )

    if numeric.shape[1] < 2:
        return recommendations

    correlation = numeric.corr(
        method="pearson"
    )

    columns = correlation.columns.tolist()

    for i in range(len(columns)):

        for j in range(i + 1, len(columns)):

            first = columns[i]
            second = columns[j]

            value = correlation.loc[first, second]

            if pd.isna(value):
                continue

            if abs(value) >= 0.85:

                direction = (
                    "positive" if value > 0 else "negative"
                )

                add_recommendation(
                    recommendations,
                    "Relationships",
                    f"Strong Relationship: {first} and {second}",
                    f"These variables have a strong {direction} Pearson correlation of {value:.3f}.",
                    "Investigate the relationship and check for overlapping information, shared causes or possible data leakage before using both variables in a predictive model.",
                    "Medium"
                )

            elif abs(value) >= 0.60:

                direction = (
                    "positive" if value > 0 else "negative"
                )

                add_recommendation(
                    recommendations,
                    "Relationships",
                    f"Potential Relationship: {first} and {second}",
                    f"These variables have a {direction} Pearson correlation of {value:.3f}.",
                    "Explore this relationship using scatter plots and domain knowledge.",
                    "Low"
                )

    return recommendations


# =========================================================
# CATEGORICAL RECOMMENDATIONS
# =========================================================

def generate_categorical_recommendations(data):

    recommendations = []

    categorical = data.select_dtypes(
        include=["object", "string", "category", "bool"]
    )

    for column in categorical.columns:

        series = categorical[column].dropna()

        if len(series) < 5:
            continue

        unique_count = series.nunique()

        if unique_count <= 1:
            continue

        if unique_count > 100:

            add_recommendation(
                recommendations,
                "Categorical Analysis",
                f"High Category Count: {column}",
                f"This column contains {unique_count:,} distinct categories.",
                "Check whether category names are inconsistent or whether this column contains identifiers better treated separately.",
                "Medium"
            )

        frequencies = series.value_counts(
            normalize=True
        )

        top_category = frequencies.index[0]

        top_percentage = frequencies.iloc[0] * 100

        if top_percentage >= 80:

            add_recommendation(
                recommendations,
                "Categorical Analysis",
                f"Dominant Category: {column}",
                f"The category '{str(top_category)[:60]}' represents {top_percentage:.2f}% of non-missing records.",
                "Investigate whether this distribution is expected and whether smaller categories need further analysis.",
                "Medium"
            )

    return recommendations


# =========================================================
# GENERAL RECOMMENDATIONS
# =========================================================

def generate_general_recommendations(data):

    recommendations = []

    if len(data) < 30:

        add_recommendation(
            recommendations,
            "General Analysis",
            "Small Dataset",
            f"The dataset contains only {len(data):,} records.",
            "Collect more representative observations before making broad conclusions or training complex predictive models.",
            "High"
        )

    if len(data.columns) > 100:

        add_recommendation(
            recommendations,
            "General Analysis",
            "High Number of Features",
            f"The dataset contains {len(data.columns):,} columns.",
            "Review feature relevance, duplicated information and unnecessary columns before advanced analysis.",
            "Medium"
        )

    if len(data.columns) == 1:

        add_recommendation(
            recommendations,
            "General Analysis",
            "Limited Dataset Structure",
            "The dataset contains only one column.",
            "Consider adding relevant variables if your analysis requires relationships between different factors.",
            "Low"
        )

    datetime_columns = data.select_dtypes(
        include=["datetime"]
    ).columns.tolist()

    if datetime_columns:

        add_recommendation(
            recommendations,
            "General Analysis",
            "Time-Based Analysis Opportunity",
            f"The dataset contains {len(datetime_columns)} date/time columns.",
            "Consider trend analysis, time-series visualisation and forecasting where the data has sufficient observations.",
            "Low"
        )

    return recommendations


# =========================================================
# MAIN RECOMMENDATION ENGINE
# =========================================================

def generate_all_recommendations(data):

    recommendations = []

    recommendations.extend(
        generate_data_quality_recommendations(data)
    )

    recommendations.extend(
        generate_numeric_recommendations(data)
    )

    recommendations.extend(
        generate_correlation_recommendations(data)
    )

    recommendations.extend(
        generate_categorical_recommendations(data)
    )

    recommendations.extend(
        generate_general_recommendations(data)
    )

    priority_order = {
        "High": 0,
        "Medium": 1,
        "Low": 2
    }

    recommendations.sort(
        key=lambda item: priority_order.get(
            item["Priority"],
            3
        )
    )

    return recommendations


# =========================================================
# RECOMMENDATION METRICS
# =========================================================

def render_recommendation_metrics(recommendations):

    high = sum(
        item["Priority"] == "High"
        for item in recommendations
    )

    medium = sum(
        item["Priority"] == "Medium"
        for item in recommendations
    )

    low = sum(
        item["Priority"] == "Low"
        for item in recommendations
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Suggestions",
        len(recommendations)
    )

    col2.metric(
        "High Priority",
        high
    )

    col3.metric(
        "Medium Priority",
        medium
    )

    col4.metric(
        "Low Priority",
        low
    )


# =========================================================
# RECOMMENDATION CARDS
# =========================================================

def render_recommendation_cards(recommendations):

    render_section_heading(
        "Generated Recommendations",
        "Review the insights and suggested actions generated from your data."
    )

    if not recommendations:

        st.success(
            "No recommendations were generated using the current rules. "
            "This does not necessarily mean the dataset has no issues."
        )

        return

    categories = sorted(
        set(
            item["Category"]
            for item in recommendations
        )
    )

    selected_category = st.selectbox(
        "Filter by Category",
        ["All Categories"] + categories,
        key="jak_recommendation_category_filter"
    )

    filtered = recommendations

    if selected_category != "All Categories":

        filtered = [
            item
            for item in recommendations
            if item["Category"] == selected_category
        ]

    for item in filtered:

        with st.container(border=True):

            st.subheader(item["Title"])

            priority = item["Priority"]

            if priority == "High":
                st.error("High Priority")

            elif priority == "Medium":
                st.warning("Medium Priority")

            else:
                st.success("Low Priority")

            st.write(item["Description"])

            st.markdown("**Recommended Action**")

            st.write(item["Recommended Action"])

            st.caption(
                f"Category: {item['Category']}"
            )


# =========================================================
# RECOMMENDATION CHARTS
# =========================================================

def render_recommendation_charts(recommendations):

    if not recommendations:
        return

    render_section_heading(
        "Recommendation Analytics",
        "Explore the distribution of generated recommendations."
    )

    recommendation_data = pd.DataFrame(
        recommendations
    )

    col1, col2 = st.columns(2)

    with col1:

        priority_counts = (
            recommendation_data["Priority"]
            .value_counts()
            .reindex(["High", "Medium", "Low"], fill_value=0)
            .rename_axis("Priority")
            .reset_index(name="Count")
        )

        fig = px.pie(
            priority_counts,
            names="Priority",
            values="Count",
            hole=0.55,
            title="Recommendations by Priority"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        category_counts = (
            recommendation_data["Category"]
            .value_counts()
            .rename_axis("Category")
            .reset_index(name="Count")
        )

        fig = px.bar(
            category_counts,
            x="Count",
            y="Category",
            orientation="h",
            title="Recommendations by Category"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# =========================================================
# DOWNLOAD REPORT
# =========================================================

def render_recommendation_download(
    recommendations,
    dataset_name
):

    if not recommendations:
        return

    report = pd.DataFrame(recommendations)

    report.insert(
        0,
        "Dataset",
        dataset_name
    )

    csv_data = report.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "Download Recommendation Report",
        data=csv_data,
        file_name="jak_recommendations_report.csv",
        mime="text/csv",
        use_container_width=True,
        key="jak_recommendation_download"
    )


# =========================================================
# INFORMATION
# =========================================================

def render_recommendation_information():

    with st.container(border=True):

        st.subheader("How JAK Generates Recommendations")

        st.write(
            "JAK examines missing values, duplicate records, "
            "statistical distributions, correlations and "
            "categorical patterns to generate suggestions "
            "for further investigation."
        )

    with st.container(border=True):

        st.subheader("Important Notice")

        st.info(
            "These recommendations are generated from statistical "
            "patterns and predefined rules. They are not proof of "
            "causation, guaranteed business outcomes or AI-generated "
            "business decisions. Review each suggestion using relevant "
            "domain knowledge before taking action."
        )


# =========================================================
# MAIN PAGE
# =========================================================

def render_recommendations_page():

    initialize_recommendation_state()

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
        "Recommendations",
        "Turn dataset insights into practical suggestions and improvement opportunities."
    )

    with st.container(border=True):

        st.title("Intelligent Recommendations Studio")

        st.write(
            "Discover useful insights, identify improvement "
            "opportunities and receive data-driven suggestions "
            "based on your uploaded datasets."
        )

    selected_dataset, dataset_name = render_dataset_selector()

    if selected_dataset is None:

        show_footer()
        return

    data = selected_dataset["data"].copy()

    if data.empty:

        st.warning(
            "The selected dataset is empty."
        )

        show_footer()
        return

    fingerprint = get_dataset_fingerprint(data)

    st.divider()

    render_dataset_overview(data)

    st.divider()

    render_recommendation_information()

    if st.button(
        "Generate Intelligent Recommendations",
        use_container_width=True,
        type="primary",
        key="jak_generate_recommendations"
    ):

        try:

            with st.spinner(
                "JAK is analysing your dataset and generating recommendations..."
            ):

                recommendations = generate_all_recommendations(
                    data
                )

                st.session_state["jak_recommendations"] = {
                    "dataset": dataset_name,
                    "fingerprint": fingerprint,
                    "recommendations": recommendations
                }

            st.success(
                "Recommendations generated successfully!"
            )

        except Exception as error:

            st.error(
                f"Recommendation generation failed: {error}"
            )

    saved = st.session_state.get(
        "jak_recommendations"
    )

    if not saved:
        show_footer()
        return

    # Only display results matching the current dataset.
    if (
        saved.get("dataset") != dataset_name
        or saved.get("fingerprint") != fingerprint
    ):

        st.info(
            "The selected dataset has changed. "
            "Generate recommendations again to refresh the results."
        )

        show_footer()
        return

    recommendations = saved["recommendations"]

    st.divider()

    render_recommendation_metrics(
        recommendations
    )

    st.divider()

    render_recommendation_cards(
        recommendations
    )

    st.divider()

    render_recommendation_charts(
        recommendations
    )

    st.divider()

    render_recommendation_download(
        recommendations,
        dataset_name
    )

    show_footer()


# =========================================================
# COMPATIBILITY ALIAS
# =========================================================

render_recommendations = render_recommendations_page