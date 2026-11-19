"""
JAK Data Analytics
Decision Centre

Features:
- Decision matrix creation
- Multiple alternatives
- Weighted decision criteria
- Benefit and cost criteria
- Automatic alternative ranking
- Decision score visualisation
- Criteria weight analysis
- Sensitivity analysis
- Dataset-based group comparison
- Downloadable decision reports

Decision scores support structured comparison.
They do not guarantee that the highest-scoring
alternative is objectively the best choice.
"""

import streamlit as st
import pandas as pd
import numpy as np
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

def initialize_decision_state():

    defaults = {
        "jak_decision_results": None,
        "jak_decision_information": None,
        "jak_decision_matrix": None,
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


# =========================================================
# DEFAULT DECISION MATRIX
# =========================================================

def create_default_matrix():

    return pd.DataFrame(
        {
            "Alternative": [
                "Option A",
                "Option B",
                "Option C",
            ],
            "Cost": [
                5000,
                7000,
                6000,
            ],
            "Quality": [
                7,
                9,
                8,
            ],
            "Reliability": [
                8,
                7,
                9,
            ],
        }
    )


# =========================================================
# PAGE INTRODUCTION
# =========================================================

def render_decision_hero():

    with st.container(border=True):

        st.caption("JAK INTELLIGENCE")

        st.title("Intelligent Decision Centre")

        st.write(
            "Compare alternatives, evaluate important criteria, "
            "assign priorities and identify strong options using "
            "structured, data-driven analysis."
        )


def render_decision_information():

    with st.container(border=True):

        st.subheader("How Decision Scoring Works")

        st.write(
            "Each alternative is evaluated against selected criteria. "
            "Criteria receive weights based on their importance. "
            "The system normalises the values and calculates a "
            "weighted score for each alternative."
        )

        st.info(
            "Benefit criteria reward higher values. "
            "Cost criteria reward lower values. "
            "The final ranking depends on the alternatives, "
            "criteria and weights you provide."
        )


# =========================================================
# DECISION SETUP
# =========================================================

def render_decision_setup():

    render_section_heading(
        "Decision Setup",
        "Describe the decision you want to evaluate.",
    )

    existing = st.session_state.get(
        "jak_decision_information"
    ) or {}

    with st.form("jak_decision_setup_form"):

        decision_name = st.text_input(
            "Decision Name",
            value=existing.get("name", ""),
            placeholder="Example: Selecting the best supplier",
        )

        decision_description = st.text_area(
            "Decision Description",
            value=existing.get("description", ""),
            placeholder="Describe the decision and what you want to achieve.",
        )

        submitted = st.form_submit_button(
            "Save Decision Information",
            use_container_width=True,
        )

    if submitted:

        if not decision_name.strip():

            st.error("Please enter a decision name.")

            return None

        information = {
            "name": decision_name.strip(),
            "description": decision_description.strip(),
        }

        st.session_state[
            "jak_decision_information"
        ] = information

        st.success("Decision information saved.")

    return st.session_state.get(
        "jak_decision_information"
    )


# =========================================================
# DECISION MATRIX
# =========================================================

def render_decision_matrix():

    render_section_heading(
        "Decision Matrix",
        "Enter the alternatives and their evaluation values.",
    )

    st.caption(
        "Edit the sample values or replace them with your own "
        "alternatives and criteria. Every criterion must contain "
        "valid numerical values."
    )

    if st.session_state.get(
        "jak_decision_matrix"
    ) is None:

        st.session_state[
            "jak_decision_matrix"
        ] = create_default_matrix()

    edited_matrix = st.data_editor(
        st.session_state["jak_decision_matrix"],
        num_rows="dynamic",
        use_container_width=True,
        key="jak_decision_matrix_editor",
    )

    edited_matrix = edited_matrix.copy()

    st.session_state[
        "jak_decision_matrix"
    ] = edited_matrix.copy()

    return edited_matrix


# =========================================================
# CRITERIA CONFIGURATION
# =========================================================

def render_criteria_configuration(matrix):

    render_section_heading(
        "Criteria Configuration",
        "Choose the importance and evaluation direction of each criterion.",
    )

    criteria = [
        column
        for column in matrix.columns
        if column != "Alternative"
    ]

    if not criteria:

        st.warning(
            "Add at least one evaluation criterion to the matrix."
        )

        return None

    configuration = {}

    columns = st.columns(
        min(2, len(criteria))
    )

    for index, criterion in enumerate(criteria):

        with columns[index % len(columns)]:

            st.markdown(f"**{criterion}**")

            weight = st.number_input(
                f"Weight for {criterion}",
                min_value=0.0,
                max_value=100.0,
                value=100.0 / len(criteria),
                step=1.0,
                key=f"jak_weight_{criterion}",
            )

            direction = st.selectbox(
                f"Evaluation direction for {criterion}",
                [
                    "Benefit (Higher is better)",
                    "Cost (Lower is better)",
                ],
                key=f"jak_direction_{criterion}",
            )

            configuration[criterion] = {
                "weight": float(weight),
                "direction": direction,
            }

    total_weight = sum(
        item["weight"]
        for item in configuration.values()
    )

    st.metric(
        "Total Assigned Weight",
        f"{total_weight:.2f}",
    )

    if total_weight <= 0:

        st.error(
            "The total criteria weight must be greater than zero."
        )

        return None

    return configuration


# =========================================================
# MATRIX VALIDATION
# =========================================================

def validate_decision_matrix(matrix, configuration):

    if not isinstance(matrix, pd.DataFrame):

        raise ValueError(
            "The decision matrix must be a pandas DataFrame."
        )

    if "Alternative" not in matrix.columns:

        raise ValueError(
            "The decision matrix must contain an Alternative column."
        )

    if matrix.empty:

        raise ValueError(
            "The decision matrix is empty."
        )

    if len(matrix) < 2:

        raise ValueError(
            "Add at least two alternatives for comparison."
        )

    if matrix.columns.duplicated().any():

        raise ValueError(
            "Column names must be unique."
        )

    names = matrix["Alternative"].astype(
        "string"
    ).str.strip()

    if names.isna().any() or names.eq("").any():

        raise ValueError(
            "Every alternative must have a valid name."
        )

    if names.duplicated().any():

        raise ValueError(
            "Alternative names must be unique."
        )

    criteria = list(configuration.keys())

    if not criteria:

        raise ValueError(
            "At least one decision criterion is required."
        )

    for criterion in criteria:

        if criterion not in matrix.columns:

            raise ValueError(
                f"Missing criterion: {criterion}"
            )

        numeric = pd.to_numeric(
            matrix[criterion],
            errors="coerce",
        )

        if numeric.isna().any():

            raise ValueError(
                f"Criterion '{criterion}' contains missing "
                "or non-numeric values."
            )

        if not np.isfinite(
            numeric.to_numpy(dtype=float)
        ).all():

            raise ValueError(
                f"Criterion '{criterion}' contains invalid numerical values."
            )

        weight = configuration[criterion]["weight"]

        if not np.isfinite(weight) or weight < 0:

            raise ValueError(
                f"Invalid weight for criterion '{criterion}'."
            )

        direction = configuration[criterion]["direction"]

        if direction not in [
            "Benefit (Higher is better)",
            "Cost (Lower is better)",
        ]:

            raise ValueError(
                f"Invalid evaluation direction for '{criterion}'."
            )

    return True


# =========================================================
# DECISION SCORE CALCULATION
# =========================================================

def calculate_decision_scores(
    matrix,
    configuration,
):

    validate_decision_matrix(
        matrix,
        configuration,
    )

    criteria = list(configuration.keys())

    values = matrix[criteria].apply(
        pd.to_numeric
    )

    weights = np.array(
        [
            configuration[column]["weight"]
            for column in criteria
        ],
        dtype=float,
    )

    if np.any(weights < 0):

        raise ValueError(
            "Criteria weights cannot be negative."
        )

    if weights.sum() <= 0:

        raise ValueError(
            "Total criteria weight must be greater than zero."
        )

    normalized_weights = weights / weights.sum()

    normalized_values = pd.DataFrame(
        index=values.index
    )

    for criterion in criteria:

        column_values = values[criterion]

        minimum = column_values.min()
        maximum = column_values.max()

        if maximum == minimum:

            normalized_values[criterion] = 1.0

        elif configuration[criterion]["direction"].startswith(
            "Benefit"
        ):

            normalized_values[criterion] = (
                (column_values - minimum)
                / (maximum - minimum)
            )

        else:

            normalized_values[criterion] = (
                (maximum - column_values)
                / (maximum - minimum)
            )

    scores = normalized_values.dot(
        normalized_weights
    )

    results = matrix[
        ["Alternative"]
    ].copy()

    results["Decision Score"] = scores

    results["Decision Score (%)"] = (
        scores * 100
    )

    results = results.sort_values(
        "Decision Score",
        ascending=False,
        kind="stable",
    ).reset_index(drop=True)

    results["Rank"] = (
        np.arange(len(results)) + 1
    )

    return (
        results,
        normalized_values,
        normalized_weights,
    )


# =========================================================
# WINNING ALTERNATIVE
# =========================================================

def render_decision_winner(results):

    if results.empty:
        return

    winner = results.iloc[0]

    with st.container(border=True):

        st.success("Highest-Scoring Alternative")

        st.title(str(winner["Alternative"]))

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Decision Score",
                f"{winner['Decision Score (%)']:.2f}%",
            )

        with col2:

            st.metric(
                "Ranking",
                f"#{int(winner['Rank'])}",
            )

        st.write(
            "This alternative achieved the highest weighted score "
            "using the criteria and weights provided."
        )


# =========================================================
# ALTERNATIVE RANKING
# =========================================================

def render_decision_ranking(results):

    render_section_heading(
        "Alternative Ranking",
        "Compare the overall weighted scores of the alternatives.",
    )

    chart_data = results.sort_values(
        "Decision Score (%)",
        ascending=True,
    )

    fig = px.bar(
        chart_data,
        x="Decision Score (%)",
        y="Alternative",
        orientation="h",
        color="Decision Score (%)",
        color_continuous_scale="Blues",
        text="Decision Score (%)",
        title="Weighted Decision Scores",
    )

    fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
    )

    fig.update_layout(
        xaxis_title="Decision Score (%)",
        yaxis_title="Alternative",
        showlegend=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.dataframe(
        results,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# CRITERIA WEIGHT ANALYSIS
# =========================================================

def render_criteria_weights(
    configuration,
    normalized_weights,
):

    render_section_heading(
        "Criteria Importance",
        "Review the relative influence of each criterion.",
    )

    weight_data = pd.DataFrame(
        {
            "Criterion": list(configuration.keys()),
            "Weight (%)": normalized_weights * 100,
        }
    )

    fig = px.pie(
        weight_data,
        names="Criterion",
        values="Weight (%)",
        hole=0.55,
        title="Relative Criteria Weights",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.dataframe(
        weight_data,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# PERFORMANCE HEATMAP
# =========================================================

def render_decision_heatmap(
    normalized_values,
    matrix,
):

    render_section_heading(
        "Alternative Performance Matrix",
        "Compare how each alternative performs across individual criteria.",
    )

    heatmap_data = normalized_values.copy()

    heatmap_data.index = matrix[
        "Alternative"
    ].astype(str).values

    fig = px.imshow(
        heatmap_data,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdYlGn",
        title="Normalised Alternative Performance",
    )

    fig.update_layout(
        height=max(
            350,
            len(heatmap_data) * 65,
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# =========================================================
# SENSITIVITY ANALYSIS
# =========================================================

def perform_sensitivity_analysis(
    matrix,
    configuration,
):

    results = []

    for criterion in configuration:

        modified = {
            name: values.copy()
            for name, values in configuration.items()
        }

        original_weight = modified[criterion]["weight"]

        if original_weight > 0:

            modified[criterion]["weight"] = (
                original_weight * 1.20
            )

        else:

            modified[criterion]["weight"] = 1.0

        scores, _, _ = calculate_decision_scores(
            matrix,
            modified,
        )

        results.append(
            {
                "Changed Criterion": criterion,
                "Highest-Scoring Alternative": scores.iloc[0]["Alternative"],
                "New Highest Score (%)": scores.iloc[0]["Decision Score (%)"],
            }
        )

    return pd.DataFrame(results)


def render_sensitivity_analysis(
    matrix,
    configuration,
):

    render_section_heading(
        "Sensitivity Analysis",
        "Explore how changing individual criterion weights may affect the ranking.",
    )

    st.caption(
        "Each criterion is increased by 20% individually. "
        "All weights are then normalised again. "
        "A criterion with zero weight is assigned a small test weight."
    )

    sensitivity = perform_sensitivity_analysis(
        matrix,
        configuration,
    )

    st.dataframe(
        sensitivity,
        use_container_width=True,
        hide_index=True,
    )

    original_results, _, _ = calculate_decision_scores(
        matrix,
        configuration,
    )

    original_winner = original_results.iloc[0][
        "Alternative"
    ]

    changed_winners = sensitivity[
        "Highest-Scoring Alternative"
    ]

    changed_count = (
        changed_winners != original_winner
    ).sum()

    if changed_count:

        st.warning(
            f"The highest-scoring alternative changed in "
            f"{changed_count} sensitivity test(s). "
            "The ranking may be sensitive to criterion weights."
        )

    else:

        st.success(
            "The highest-scoring alternative remained unchanged "
            "across the individual weight tests."
        )


# =========================================================
# DOWNLOAD DECISION REPORTS
# =========================================================

def render_decision_download(
    results,
    normalized_values,
    matrix=None,
):

    st.divider()

    render_section_heading(
        "Download Decision Reports",
        "Export your decision analysis for further review.",
    )

    ranking_csv = results.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "Download Decision Ranking",
        data=ranking_csv,
        file_name="jak_decision_ranking.csv",
        mime="text/csv",
        use_container_width=True,
    )

    performance = normalized_values.copy()

    if matrix is not None:

        performance.insert(
            0,
            "Alternative",
            matrix["Alternative"].astype(str).values,
        )

    performance_csv = performance.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "Download Performance Matrix",
        data=performance_csv,
        file_name="jak_decision_performance_matrix.csv",
        mime="text/csv",
        use_container_width=True,
    )


# =========================================================
# MATRIX DECISION PAGE
# =========================================================

def render_matrix_decision_page():

    information = render_decision_setup()

    if information is None:

        st.info(
            "Enter and save your decision information to continue."
        )

        return

    st.divider()

    matrix = render_decision_matrix()

    if matrix.empty:

        st.warning(
            "Add alternatives to the decision matrix."
        )

        return

    st.divider()

    configuration = render_criteria_configuration(
        matrix
    )

    if configuration is None:
        return

    st.warning(
        "Ensure that every criterion uses a consistent measurement "
        "scale. Normalised results depend on the alternatives "
        "included in the comparison."
    )

    if st.button(
        "Calculate Decision Ranking",
        use_container_width=True,
        type="primary",
    ):

        try:

            with st.spinner(
                "JAK is evaluating the alternatives..."
            ):

                (
                    results,
                    normalized_values,
                    normalized_weights,
                ) = calculate_decision_scores(
                    matrix,
                    configuration,
                )

                st.session_state[
                    "jak_decision_results"
                ] = {
                    "information": information.copy(),
                    "matrix": matrix.copy(),
                    "configuration": {
                        name: values.copy()
                        for name, values in configuration.items()
                    },
                    "results": results.copy(),
                    "normalized_values": normalized_values.copy(),
                    "normalized_weights": normalized_weights.copy(),
                }

            st.success(
                "Decision analysis completed successfully."
            )

        except Exception as error:

            st.error(
                f"Decision analysis failed: {error}"
            )

    saved = st.session_state.get(
        "jak_decision_results"
    )

    if not saved:
        return

    st.divider()

    st.header(
        saved["information"]["name"]
    )

    if saved["information"].get("description"):

        st.write(
            saved["information"]["description"]
        )

    render_decision_winner(
        saved["results"]
    )

    render_decision_ranking(
        saved["results"]
    )

    st.divider()

    render_criteria_weights(
        saved["configuration"],
        saved["normalized_weights"],
    )

    st.divider()

    render_decision_heatmap(
        saved["normalized_values"],
        saved["matrix"],
    )

    st.divider()

    render_sensitivity_analysis(
        saved["matrix"],
        saved["configuration"],
    )

    render_decision_download(
        saved["results"],
        saved["normalized_values"],
        saved["matrix"],
    )


# =========================================================
# DATASET-BASED GROUP COMPARISON
# =========================================================

def render_dataset_comparison_page(data):

    render_section_heading(
        "Dataset-Based Decision Analysis",
        "Compare groups using numerical indicators from your dataset.",
    )

    if not isinstance(data, pd.DataFrame) or data.empty:

        st.warning(
            "The selected dataset is empty or invalid."
        )

        return

    numeric_columns = data.select_dtypes(
        include="number"
    ).columns.tolist()

    categorical_columns = data.select_dtypes(
        include=["object", "string", "category", "bool"]
    ).columns.tolist()

    if not numeric_columns or not categorical_columns:

        st.info(
            "This analysis requires at least one categorical "
            "column and one numerical column."
        )

        return

    col1, col2 = st.columns(2)

    with col1:

        group_column = st.selectbox(
            "Select Grouping Variable",
            categorical_columns,
            key="jak_decision_group_column",
        )

    with col2:

        metric_column = st.selectbox(
            "Select Numerical Indicator",
            numeric_columns,
            key="jak_decision_metric_column",
        )

    aggregation = st.selectbox(
        "Comparison Method",
        [
            "Mean",
            "Median",
            "Sum",
            "Minimum",
            "Maximum",
            "Count",
        ],
        key="jak_decision_aggregation",
    )

    grouped_data = data[
        [group_column, metric_column]
    ].copy()

    grouped_data[metric_column] = pd.to_numeric(
        grouped_data[metric_column],
        errors="coerce",
    )

    grouped_data = grouped_data.dropna(
        subset=[group_column, metric_column]
    )

    if grouped_data.empty:

        st.warning(
            "No valid records are available for comparison."
        )

        return

    operations = {
        "Mean": "mean",
        "Median": "median",
        "Sum": "sum",
        "Minimum": "min",
        "Maximum": "max",
        "Count": "count",
    }

    comparison = (
        grouped_data.groupby(
            group_column,
            observed=True,
        )[metric_column]
        .agg(operations[aggregation])
        .reset_index()
    )

    comparison.columns = [
        "Group",
        aggregation,
    ]

    comparison = comparison.sort_values(
        aggregation,
        ascending=False,
    )

    st.subheader("Group Comparison Results")

    st.dataframe(
        comparison,
        use_container_width=True,
        hide_index=True,
    )

    fig = px.bar(
        comparison,
        x="Group",
        y=aggregation,
        title=f"{aggregation} {metric_column} by {group_column}",
        color=aggregation,
        color_continuous_scale="Blues",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    if not comparison.empty:

        winner = comparison.iloc[0]

        st.info(
            f"Highest {aggregation.lower()}: "
            f"{winner['Group']} "
            f"({winner[aggregation]:,.2f})"
        )

    csv_data = comparison.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "Download Group Comparison",
        data=csv_data,
        file_name="jak_group_comparison.csv",
        mime="text/csv",
        use_container_width=True,
    )


# =========================================================
# MAIN DECISION CENTRE PAGE
# =========================================================

def render_decision_centre_page():

    initialize_decision_state()

    username = st.session_state.get(
        "jak_user_name",
        "Guest",
    )

    role = st.session_state.get(
        "jak_user_role",
        "User",
    )

    render_topbar(
        username=username,
        role=role,
    )

    render_page_intro(
        "Decision Centre",
        "Compare alternatives and support informed decisions using structured data analysis.",
    )

    render_decision_hero()

    render_decision_information()

    tab1, tab2 = st.tabs(
        [
            "Decision Matrix",
            "Dataset Comparison",
        ]
    )

    with tab1:

        render_matrix_decision_page()

    with tab2:

        datasets = st.session_state.get(
            "jak_datasets",
            [],
        )

        valid_datasets = [
            item
            for item in datasets
            if isinstance(item, dict)
            and isinstance(item.get("data"), pd.DataFrame)
            and not item["data"].empty
        ]

        if not valid_datasets:

            st.info(
                "Upload a valid dataset first to use dataset-based comparison."
            )

        else:

            dataset_options = {}

            for index, item in enumerate(valid_datasets):

                display_name = item.get(
                    "name",
                    f"Dataset {index + 1}",
                )

                option_key = (
                    f"{display_name} ({index + 1})"
                )

                dataset_options[option_key] = item

            selected_name = st.selectbox(
                "Select Dataset",
                list(dataset_options.keys()),
                key="jak_decision_dataset",
            )

            selected_data = dataset_options[
                selected_name
            ]["data"]

            render_dataset_comparison_page(
                selected_data
            )

    st.divider()

    with st.container(border=True):

        st.subheader("Decision-Making Limitation")

        st.write(
            "A high score indicates the strongest result under "
            "the selected criteria and weights. It does not "
            "establish causation or guarantee the best real-world "
            "outcome."
        )

        st.warning(
            "Consider uncertainty, missing information, fairness, "
            "costs and domain expertise before acting on a decision."
        )

    show_footer()


# =========================================================
# COMPATIBILITY ALIASES
# =========================================================

render_decision_centre = render_decision_centre_page
render_decision_center = render_decision_centre_page
render_decision_center_page = render_decision_centre_page