"""
JAK Data Analytics
Scenario Simulation Engine

Features:
- Dataset selection
- Baseline scenario
- Multiple custom scenarios
- Numerical variable adjustments
- Percentage and fixed-value changes
- Scenario comparison
- KPI impact analysis
- Sensitivity analysis
- Interactive charts
- Downloadable simulation reports

This module performs assumption-based simulations.
Results are estimates, not guaranteed predictions.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import uuid
import hashlib
import json

from ...ui.layout import (
    render_topbar,
    render_page_intro,
    render_section_heading,
)

from ...ui.theme import show_footer


# =========================================================
# INITIALIZATION
# =========================================================

def initialize_simulation_state():

    defaults = {
        "jak_scenarios": [],
        "jak_simulation_results": None,
        "jak_simulation_signature": None,
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


# =========================================================
# PAGE INTRODUCTION
# =========================================================

def render_simulation_hero():

    with st.container(border=True):

        st.caption("JAK INTELLIGENCE")

        st.title("Scenario Simulation Centre")

        st.write(
            "Explore possible outcomes by changing important "
            "business variables, testing assumptions and "
            "comparing alternative scenarios."
        )


def render_simulation_information():

    with st.container(border=True):

        st.subheader("How Simulation Works")

        st.write(
            "JAK starts with baseline values calculated from "
            "your selected dataset. You can create alternative "
            "scenarios by increasing or decreasing selected "
            "numerical variables."
        )

        st.info(
            "Scenario results are calculated from the assumptions "
            "you enter. They are not guaranteed predictions of "
            "future events."
        )


# =========================================================
# DATA HELPERS
# =========================================================

def get_numeric_columns(data):

    if not isinstance(data, pd.DataFrame):
        return []

    return data.select_dtypes(
        include="number"
    ).columns.tolist()


def calculate_baseline(data, selected_metrics):

    baseline = {}

    for column in selected_metrics:

        values = pd.to_numeric(
            data[column],
            errors="coerce",
        )

        values = values.replace(
            [np.inf, -np.inf],
            np.nan,
        ).dropna()

        baseline[column] = {
            "mean": float(values.mean()) if not values.empty else 0.0,
            "sum": float(values.sum()) if not values.empty else 0.0,
            "minimum": float(values.min()) if not values.empty else 0.0,
            "maximum": float(values.max()) if not values.empty else 0.0,
            "count": int(values.count()),
        }

    return baseline


# =========================================================
# SIMULATION SETUP
# =========================================================

def render_simulation_setup(data):

    render_section_heading(
        "Simulation Setup",
        "Choose the numerical indicators you want to investigate.",
    )

    numeric_columns = get_numeric_columns(data)

    if not numeric_columns:

        st.warning(
            "The selected dataset does not contain numerical columns."
        )

        return None

    selected_metrics = st.multiselect(
        "Select variables to simulate",
        numeric_columns,
        default=numeric_columns[:min(3, len(numeric_columns))],
        key="jak_simulation_metrics",
    )

    if not selected_metrics:

        st.info(
            "Select at least one numerical variable."
        )

        return None

    aggregation = st.selectbox(
        "Baseline Calculation",
        [
            "Sum",
            "Mean",
            "Minimum",
            "Maximum",
        ],
        key="jak_simulation_aggregation",
    )

    aggregation_map = {
        "Sum": "sum",
        "Mean": "mean",
        "Minimum": "minimum",
        "Maximum": "maximum",
    }

    baseline_data = calculate_baseline(
        data,
        selected_metrics,
    )

    baseline = {
        column: baseline_data[column][
            aggregation_map[aggregation]
        ]
        for column in selected_metrics
    }

    st.subheader("Baseline Values")

    baseline_table = pd.DataFrame(
        [
            {
                "Variable": column,
                "Baseline Value": value,
                "Calculation": aggregation,
                "Valid Records": baseline_data[column]["count"],
            }
            for column, value in baseline.items()
        ]
    )

    st.dataframe(
        baseline_table,
        use_container_width=True,
        hide_index=True,
    )

    return {
        "metrics": selected_metrics,
        "aggregation": aggregation,
        "baseline": baseline,
    }


# =========================================================
# SCENARIO SIGNATURE
# =========================================================

def create_simulation_signature(
    dataset_name,
    simulation_setup,
):

    signature_data = {
        "dataset": dataset_name,
        "metrics": simulation_setup["metrics"],
        "aggregation": simulation_setup["aggregation"],
        "baseline": simulation_setup["baseline"],
    }

    encoded = json.dumps(
        signature_data,
        sort_keys=True,
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(
        encoded
    ).hexdigest()


def synchronize_simulation_state(signature):

    previous_signature = st.session_state.get(
        "jak_simulation_signature"
    )

    if previous_signature != signature:

        st.session_state[
            "jak_scenarios"
        ] = []

        st.session_state[
            "jak_simulation_results"
        ] = None

        st.session_state[
            "jak_simulation_signature"
        ] = signature

        if previous_signature is not None:

            st.info(
                "Your dataset or simulation settings changed. "
                "Previous scenarios were cleared to prevent "
                "comparisons using outdated baseline values."
            )


# =========================================================
# SCENARIO CALCULATION
# =========================================================

def create_scenario(
    name,
    description,
    baseline,
    adjustments,
):

    scenario_values = {}

    for column, original_value in baseline.items():

        adjustment = adjustments.get(
            column,
            {
                "type": "Percentage",
                "value": 0.0,
            },
        )

        change_value = float(
            adjustment["value"]
        )

        if not np.isfinite(change_value):

            raise ValueError(
                f"Invalid adjustment value for {column}."
            )

        if adjustment["type"] == "Percentage":

            new_value = original_value * (
                1 + change_value / 100
            )

        elif adjustment["type"] == "Fixed Value":

            new_value = original_value + change_value

        else:

            raise ValueError(
                f"Unsupported adjustment type for {column}."
            )

        if not np.isfinite(new_value):

            raise ValueError(
                f"The simulated value for {column} is invalid."
            )

        difference = new_value - original_value

        if original_value != 0:

            percentage_change = (
                difference / abs(original_value)
            ) * 100

        else:

            percentage_change = np.nan

        scenario_values[column] = {
            "baseline": float(original_value),
            "adjustment_type": adjustment["type"],
            "adjustment": change_value,
            "simulated": float(new_value),
            "difference": float(difference),
            "percentage_change": float(percentage_change)
            if np.isfinite(percentage_change)
            else np.nan,
        }

    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
        "values": scenario_values,
    }


# =========================================================
# SCENARIO BUILDER
# =========================================================

def render_scenario_builder(simulation_setup):

    render_section_heading(
        "Create a Scenario",
        "Define assumptions and see how they change your selected variables.",
    )

    baseline = simulation_setup["baseline"]

    with st.form("jak_scenario_builder_form"):

        scenario_name = st.text_input(
            "Scenario Name",
            placeholder="Example: 15% Sales Growth",
        )

        description = st.text_area(
            "Scenario Description",
            placeholder="Describe the assumptions behind this scenario.",
        )

        adjustments = {}

        for column, value in baseline.items():

            st.markdown(f"**{column}**")

            col1, col2 = st.columns(2)

            with col1:

                adjustment_type = st.selectbox(
                    f"Adjustment Type — {column}",
                    [
                        "Percentage",
                        "Fixed Value",
                    ],
                    key=f"jak_adjustment_type_{column}",
                )

            with col2:

                adjustment_value = st.number_input(
                    f"Change — {column}",
                    value=0.0,
                    step=1.0,
                    key=f"jak_adjustment_value_{column}",
                )

            adjustments[column] = {
                "type": adjustment_type,
                "value": adjustment_value,
            }

        submitted = st.form_submit_button(
            "Add Scenario",
            use_container_width=True,
        )

    if submitted:

        if not scenario_name.strip():

            st.error(
                "Please enter a scenario name."
            )

            return

        existing_names = [
            item["name"].strip().lower()
            for item in st.session_state["jak_scenarios"]
        ]

        if scenario_name.strip().lower() in existing_names:

            st.error(
                "A scenario with this name already exists."
            )

            return

        try:

            scenario = create_scenario(
                scenario_name.strip(),
                description.strip(),
                baseline,
                adjustments,
            )

            st.session_state[
                "jak_scenarios"
            ].append(scenario)

            st.session_state[
                "jak_simulation_results"
            ] = None

            st.success(
                "Scenario created successfully."
            )

        except Exception as error:

            st.error(
                f"Unable to create scenario: {error}"
            )


# =========================================================
# SAVED SCENARIOS
# =========================================================

def render_saved_scenarios():

    render_section_heading(
        "Saved Scenarios",
        "Review and manage the scenarios created in this session.",
    )

    scenarios = st.session_state.get(
        "jak_scenarios",
        [],
    )

    if not scenarios:

        st.info(
            "No scenarios have been created yet."
        )

        return

    for scenario in scenarios:

        with st.expander(
            scenario["name"],
            expanded=False,
        ):

            st.write(
                scenario["description"]
                or "No description provided."
            )

            scenario_table = pd.DataFrame(
                [
                    {
                        "Variable": column,
                        "Baseline": values["baseline"],
                        "Adjustment Type": values["adjustment_type"],
                        "Adjustment": values["adjustment"],
                        "Simulated": values["simulated"],
                        "Difference": values["difference"],
                        "Change (%)": values["percentage_change"],
                    }
                    for column, values in scenario["values"].items()
                ]
            )

            st.dataframe(
                scenario_table,
                use_container_width=True,
                hide_index=True,
            )

            if st.button(
                "Delete Scenario",
                key=f"jak_delete_scenario_{scenario['id']}",
            ):

                st.session_state[
                    "jak_scenarios"
                ] = [
                    item
                    for item in st.session_state["jak_scenarios"]
                    if item["id"] != scenario["id"]
                ]

                st.session_state[
                    "jak_simulation_results"
                ] = None

                st.rerun()


# =========================================================
# COMPARISON TABLE
# =========================================================

def build_comparison_table(
    baseline,
    scenarios,
):

    rows = []

    for column, value in baseline.items():

        rows.append(
            {
                "Variable": column,
                "Scenario": "Baseline",
                "Value": value,
                "Change": 0.0,
                "Change (%)": 0.0,
            }
        )

    for scenario in scenarios:

        for column, values in scenario["values"].items():

            rows.append(
                {
                    "Variable": column,
                    "Scenario": scenario["name"],
                    "Value": values["simulated"],
                    "Change": values["difference"],
                    "Change (%)": values["percentage_change"],
                }
            )

    return pd.DataFrame(rows)


# =========================================================
# SCENARIO METRICS
# =========================================================

def render_scenario_metrics(
    baseline,
    scenarios,
):

    total_scenarios = len(scenarios)

    total_variables = len(baseline)

    first, second, third = st.columns(3)

    first.metric(
        "Scenarios Created",
        total_scenarios,
    )

    second.metric(
        "Variables Analysed",
        total_variables,
    )

    third.metric(
        "Compared Outcomes",
        total_scenarios + 1,
    )


# =========================================================
# SCENARIO COMPARISON
# =========================================================

def render_scenario_comparison(
    baseline,
    scenarios,
):

    render_section_heading(
        "Scenario Comparison",
        "Compare baseline values with simulated outcomes.",
    )

    comparison = build_comparison_table(
        baseline,
        scenarios,
    )

    selected_variable = st.selectbox(
        "Select Variable to Compare",
        list(baseline.keys()),
        key="jak_comparison_variable",
    )

    filtered = comparison[
        comparison["Variable"] == selected_variable
    ].copy()

    fig = px.bar(
        filtered,
        x="Scenario",
        y="Value",
        color="Scenario",
        text="Value",
        title=f"Scenario Comparison: {selected_variable}",
    )

    fig.update_traces(
        texttemplate="%{text:,.2f}",
        textposition="outside",
    )

    fig.update_layout(
        xaxis_title="Scenario",
        yaxis_title="Simulated Value",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
    )

    return comparison


# =========================================================
# IMPACT ANALYSIS
# =========================================================

def render_scenario_impact(comparison):

    render_section_heading(
        "Impact Analysis",
        "Understand the numerical differences between scenarios.",
    )

    impact = comparison[
        comparison["Scenario"] != "Baseline"
    ].copy()

    if impact.empty:

        st.info(
            "Create at least one scenario to see its impact."
        )

        return

    fig = px.bar(
        impact,
        x="Variable",
        y="Change (%)",
        color="Scenario",
        barmode="group",
        title="Percentage Change by Scenario",
    )

    fig.update_layout(
        xaxis_title="Variable",
        yaxis_title="Percentage Change (%)",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    positive = int(
        (impact["Change"] > 0).sum()
    )

    negative = int(
        (impact["Change"] < 0).sum()
    )

    unchanged = int(
        (impact["Change"] == 0).sum()
    )

    first, second, third = st.columns(3)

    first.metric(
        "Increased Values",
        positive,
    )

    second.metric(
        "Decreased Values",
        negative,
    )

    third.metric(
        "Unchanged Values",
        unchanged,
    )

    zero_baseline = impact[
        impact["Change (%)"].isna()
    ]

    if not zero_baseline.empty:

        st.caption(
            "Percentage changes are unavailable for variables "
            "whose baseline value is zero. Their absolute changes "
            "are still displayed."
        )


# =========================================================
# SENSITIVITY ANALYSIS
# =========================================================

def render_sensitivity_analysis(baseline):

    render_section_heading(
        "Sensitivity Analysis",
        "Test how different percentage assumptions affect one variable.",
    )

    if not baseline:
        return

    variable = st.selectbox(
        "Select Variable",
        list(baseline.keys()),
        key="jak_sensitivity_variable",
    )

    change_range = st.slider(
        "Percentage Change Range",
        min_value=5,
        max_value=100,
        value=30,
        step=5,
        key="jak_sensitivity_range",
    )

    percentages = np.linspace(
        -change_range,
        change_range,
        11,
    )

    original_value = baseline[variable]

    sensitivity = pd.DataFrame(
        {
            "Percentage Change": percentages,
            "Simulated Value": [
                original_value * (1 + change / 100)
                for change in percentages
            ],
        }
    )

    fig = px.line(
        sensitivity,
        x="Percentage Change",
        y="Simulated Value",
        markers=True,
        title=f"Sensitivity of {variable}",
    )

    fig.add_hline(
        y=original_value,
        line_dash="dash",
        annotation_text="Baseline",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.dataframe(
        sensitivity,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# DOWNLOAD SIMULATION REPORT
# =========================================================

def render_simulation_download(comparison):

    csv_data = comparison.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "Download Simulation Report",
        data=csv_data,
        file_name="jak_scenario_simulation.csv",
        mime="text/csv",
        use_container_width=True,
    )


# =========================================================
# SIMULATION RESULTS
# =========================================================

def render_simulation_analysis(simulation_setup):

    scenarios = st.session_state.get(
        "jak_scenarios",
        [],
    )

    if not scenarios:

        st.info(
            "Create at least one scenario to view simulation results."
        )

        return

    baseline = simulation_setup["baseline"]

    render_section_heading(
        "Simulation Results",
        "Review the outcomes of your different assumptions.",
    )

    render_scenario_metrics(
        baseline,
        scenarios,
    )

    st.divider()

    comparison = render_scenario_comparison(
        baseline,
        scenarios,
    )

    st.divider()

    render_scenario_impact(
        comparison,
    )

    st.divider()

    render_sensitivity_analysis(
        baseline,
    )

    st.divider()

    render_simulation_download(
        comparison,
    )

    st.session_state[
        "jak_simulation_results"
    ] = comparison


# =========================================================
# MAIN SIMULATION PAGE
# =========================================================

def render_scenario_simulation_page():

    initialize_simulation_state()

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
        "Scenario Simulation",
        "Explore alternative possibilities and measure their potential impact.",
    )

    render_simulation_hero()

    render_simulation_information()

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

        st.warning(
            "Upload a valid dataset first to use Scenario Simulation."
        )

        show_footer()

        return

    dataset_options = {}

    for index, item in enumerate(valid_datasets):

        display_name = item.get(
            "name",
            f"Dataset {index + 1}",
        )

        option_key = f"{display_name} ({index + 1})"

        dataset_options[option_key] = item

    selected_dataset = st.selectbox(
        "Select Dataset",
        list(dataset_options.keys()),
        key="jak_scenario_dataset",
    )

    data = dataset_options[
        selected_dataset
    ]["data"]

    simulation_setup = render_simulation_setup(
        data
    )

    if simulation_setup is None:

        show_footer()

        return

    signature = create_simulation_signature(
        selected_dataset,
        simulation_setup,
    )

    synchronize_simulation_state(
        signature
    )

    st.divider()

    tab1, tab2, tab3 = st.tabs(
        [
            "Create Scenario",
            "Saved Scenarios",
            "Simulation Results",
        ]
    )

    with tab1:

        render_scenario_builder(
            simulation_setup
        )

    with tab2:

        render_saved_scenarios()

    with tab3:

        render_simulation_analysis(
            simulation_setup
        )

    st.divider()

    with st.container(border=True):

        st.subheader("Simulation Limitations")

        st.write(
            "Scenario simulation uses the assumptions entered "
            "by the user. It does not automatically predict "
            "the future, establish causation or account for "
            "every external factor."
        )

        st.warning(
            "Review your assumptions and consider external "
            "conditions before using simulation results to "
            "make business or operational decisions."
        )

    show_footer()


# =========================================================
# COMPATIBILITY ALIASES
# =========================================================

render_scenario_simulation = render_scenario_simulation_page
render_scenario_simulation_centre = render_scenario_simulation_page
render_scenario_simulation_center = render_scenario_simulation_page