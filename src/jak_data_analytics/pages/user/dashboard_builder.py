"""
JAK Data Analytics
Dashboard Builder

Allows users to create, preview and save interactive dashboards.

Features:
- Dashboard information
- KPI indicators
- Interactive charts
- Data tables
- Live dashboard preview
- Saved dashboards
- Component management

Uses native Streamlit components.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import uuid

from datetime import datetime

from ...ui.layout import (
    render_topbar,
    render_page_intro,
    render_section_heading,
)

from ...ui.theme import show_footer


# =====================================================
# INITIALIZATION
# =====================================================

def initialize_dashboards():

    if "jak_saved_dashboards" not in st.session_state:
        st.session_state["jak_saved_dashboards"] = []

    if "jak_dashboard_components" not in st.session_state:
        st.session_state["jak_dashboard_components"] = []

    if "jak_builder_information" not in st.session_state:
        st.session_state["jak_builder_information"] = None

    if "jak_dashboard_dataset" not in st.session_state:
        st.session_state["jak_dashboard_dataset"] = None


def get_datasets():

    return st.session_state.get("jak_datasets", [])


def get_valid_datasets():

    return [
        item for item in get_datasets()
        if (
            isinstance(item, dict)
            and isinstance(item.get("data"), pd.DataFrame)
        )
    ]


# =====================================================
# HERO
# =====================================================

def render_builder_hero():

    with st.container(border=True):

        st.subheader("📊 Interactive Dashboard Studio")

        st.write(
            "Build professional dashboards by combining "
            "performance indicators, interactive charts and "
            "data tables into one visual workspace."
        )


# =====================================================
# DATASET OVERVIEW
# =====================================================

def render_dashboard_overview(data):

    numeric_count = len(
        data.select_dtypes(include="number").columns
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Records",
        f"{len(data):,}"
    )

    col2.metric(
        "Total Variables",
        len(data.columns)
    )

    col3.metric(
        "Numeric Variables",
        numeric_count
    )

    col4.metric(
        "Missing Values",
        f"{data.isna().sum().sum():,}"
    )


# =====================================================
# DASHBOARD INFORMATION
# =====================================================

def render_dashboard_information():

    render_section_heading(
        "Dashboard Information",
        "Give your dashboard a name and description."
    )

    existing = st.session_state.get(
        "jak_builder_information"
    ) or {}

    with st.form("jak_dashboard_information"):

        name = st.text_input(
            "Dashboard Name",
            value=existing.get("name", ""),
            placeholder="Example: Employee Performance Dashboard"
        )

        description = st.text_area(
            "Description",
            value=existing.get("description", ""),
            placeholder="Describe what this dashboard will show."
        )

        submitted = st.form_submit_button(
            "Set Dashboard Information",
            use_container_width=True
        )

    if submitted:

        if not name.strip():

            st.error("Dashboard name is required.")

            return None

        information = {
            "name": name.strip(),
            "description": description.strip()
        }

        st.session_state["jak_builder_information"] = information

        st.success("Dashboard information saved.")

        return information

    return st.session_state.get(
        "jak_builder_information"
    )


# =====================================================
# KPI BUILDER
# =====================================================

def render_kpi_builder(data):

    render_section_heading(
        "Add KPI Indicator",
        "Choose a numeric variable to display as a dashboard metric."
    )

    numeric_columns = data.select_dtypes(
        include="number"
    ).columns.tolist()

    if not numeric_columns:

        st.info(
            "No numeric columns are available for KPI indicators."
        )

        return None

    with st.form("jak_kpi_builder"):

        title = st.text_input(
            "KPI Title",
            placeholder="Example: Total Revenue"
        )

        column = st.selectbox(
            "Numeric Variable",
            numeric_columns
        )

        calculation = st.selectbox(
            "Calculation",
            [
                "Sum",
                "Average",
                "Median",
                "Minimum",
                "Maximum",
                "Count"
            ]
        )

        submitted = st.form_submit_button(
            "Add KPI",
            use_container_width=True
        )

    if not submitted:
        return None

    if not title.strip():

        st.error("Enter a KPI title.")

        return None

    return {
        "id": str(uuid.uuid4()),
        "type": "kpi",
        "title": title.strip(),
        "column": column,
        "calculation": calculation
    }


# =====================================================
# CHART BUILDER
# =====================================================

def render_chart_builder(data):

    render_section_heading(
        "Add Dashboard Chart",
        "Create a chart to include in your dashboard."
    )

    numeric_columns = data.select_dtypes(
        include="number"
    ).columns.tolist()

    columns = data.columns.tolist()

    chart_types = [
        "Bar Chart",
        "Line Chart",
        "Area Chart",
        "Pie Chart",
        "Donut Chart",
        "Scatter Plot",
        "Histogram",
        "Box Plot"
    ]

    with st.form("jak_dashboard_chart"):

        title = st.text_input(
            "Chart Title",
            placeholder="Example: Salary by Department"
        )

        chart_type = st.selectbox(
            "Chart Type",
            chart_types
        )

        x_column = st.selectbox(
            "X-Axis / Category",
            columns
        )

        y_column = None

        if chart_type != "Histogram":

            if numeric_columns:

                y_column = st.selectbox(
                    "Numeric Value",
                    numeric_columns
                )

            else:

                st.warning(
                    "This chart requires numeric columns."
                )

        color_options = ["None"] + columns

        color_column = st.selectbox(
            "Colour Group",
            color_options
        )

        submitted = st.form_submit_button(
            "Add Chart",
            use_container_width=True
        )

    if not submitted:
        return None

    if not title.strip():

        st.error("Enter a chart title.")

        return None

    if chart_type != "Histogram" and not numeric_columns:

        st.error("A numeric column is required.")

        return None

    if chart_type in [
        "Scatter Plot",
        "Box Plot"
    ] and y_column is None:

        st.error("Select a numeric Y-axis variable.")

        return None

    return {
        "id": str(uuid.uuid4()),
        "type": "chart",
        "title": title.strip(),
        "chart_type": chart_type,
        "x": x_column,
        "y": y_column,
        "color": (
            None if color_column == "None"
            else color_column
        )
    }


# =====================================================
# TABLE BUILDER
# =====================================================

def render_table_builder(data):

    render_section_heading(
        "Add Data Table",
        "Choose which columns should appear in your dashboard."
    )

    with st.form("jak_dashboard_table"):

        title = st.text_input(
            "Table Title",
            value="Dataset Preview"
        )

        selected_columns = st.multiselect(
            "Select Columns",
            data.columns.tolist(),
            default=data.columns.tolist()[
                :min(5, len(data.columns))
            ]
        )

        row_limit = st.slider(
            "Maximum Rows",
            min_value=5,
            max_value=100,
            value=20
        )

        submitted = st.form_submit_button(
            "Add Table",
            use_container_width=True
        )

    if not submitted:
        return None

    if not title.strip():

        st.error("Enter a table title.")

        return None

    if not selected_columns:

        st.error("Select at least one column.")

        return None

    return {
        "id": str(uuid.uuid4()),
        "type": "table",
        "title": title.strip(),
        "columns": selected_columns,
        "row_limit": row_limit
    }


# =====================================================
# KPI CALCULATIONS
# =====================================================

def calculate_kpi(data, component):

    column = component["column"]

    values = pd.to_numeric(
        data[column],
        errors="coerce"
    ).dropna()

    calculation = component["calculation"]

    if values.empty:
        return None

    if calculation == "Sum":
        return values.sum()

    if calculation == "Average":
        return values.mean()

    if calculation == "Median":
        return values.median()

    if calculation == "Minimum":
        return values.min()

    if calculation == "Maximum":
        return values.max()

    if calculation == "Count":
        return values.count()

    return None


# =====================================================
# CHART GENERATION
# =====================================================

def create_dashboard_chart(data, component):

    chart_type = component["chart_type"]

    x = component["x"]
    y = component["y"]
    color = component["color"]

    if chart_type in [
        "Bar Chart",
        "Line Chart",
        "Area Chart",
        "Pie Chart",
        "Donut Chart"
    ]:

        if y is None:

            chart_data = (
                data.groupby(
                    x,
                    dropna=False,
                    observed=False
                )
                .size()
                .reset_index(name="Count")
            )

            value_column = "Count"

        else:

            chart_data = (
                data.groupby(
                    x,
                    dropna=False,
                    observed=False
                )[y]
                .sum()
                .reset_index()
            )

            value_column = y

        if chart_type == "Bar Chart":

            fig = px.bar(
                chart_data,
                x=x,
                y=value_column,
                title=component["title"]
            )

        elif chart_type == "Line Chart":

            fig = px.line(
                chart_data,
                x=x,
                y=value_column,
                markers=True,
                title=component["title"]
            )

        elif chart_type == "Area Chart":

            fig = px.area(
                chart_data,
                x=x,
                y=value_column,
                title=component["title"]
            )

        elif chart_type == "Pie Chart":

            fig = px.pie(
                chart_data,
                names=x,
                values=value_column,
                title=component["title"]
            )

        else:

            fig = px.pie(
                chart_data,
                names=x,
                values=value_column,
                hole=0.55,
                title=component["title"]
            )

    elif chart_type == "Scatter Plot":

        fig = px.scatter(
            data,
            x=x,
            y=y,
            color=color,
            title=component["title"]
        )

    elif chart_type == "Histogram":

        fig = px.histogram(
            data,
            x=x,
            title=component["title"]
        )

    elif chart_type == "Box Plot":

        fig = px.box(
            data,
            x=x,
            y=y,
            color=color,
            title=component["title"]
        )

    else:

        raise ValueError("Unsupported chart type.")

    fig.update_layout(
        template="plotly_white",
        height=400,
        margin=dict(
            l=25,
            r=25,
            t=60,
            b=35
        ),
        font=dict(
            family="Inter, sans-serif"
        )
    )

    return fig


# =====================================================
# RENDER DASHBOARD COMPONENT
# =====================================================

def render_dashboard_component(data, component):

    component_type = component["type"]

    if component_type == "kpi":

        value = calculate_kpi(
            data,
            component
        )

        if value is None or pd.isna(value):

            display_value = "N/A"

        elif isinstance(value, (int, float)):

            display_value = f"{value:,.2f}"

        else:

            display_value = str(value)

        st.metric(
            component["title"],
            display_value
        )

    elif component_type == "chart":

        fig = create_dashboard_chart(
            data,
            component
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            key=f"dashboard_chart_{component['id']}"
        )

    elif component_type == "table":

        table = data[
            component["columns"]
        ].head(
            component["row_limit"]
        )

        st.markdown(
            f"**{component['title']}**"
        )

        st.dataframe(
            table,
            use_container_width=True
        )


# =====================================================
# DASHBOARD PREVIEW
# =====================================================

def render_dashboard_preview(data, information, components):

    render_section_heading(
        information["name"],
        information.get("description", "")
    )

    if not components:

        st.info(
            "Your dashboard is empty. Add KPI indicators, charts or tables."
        )

        return

    kpis = [
        item for item in components
        if item["type"] == "kpi"
    ]

    charts = [
        item for item in components
        if item["type"] == "chart"
    ]

    tables = [
        item for item in components
        if item["type"] == "table"
    ]

    if kpis:

        st.subheader("Key Performance Indicators")

        columns = st.columns(min(4, len(kpis)))

        for index, component in enumerate(kpis):

            with columns[index % len(columns)]:

                render_dashboard_component(
                    data,
                    component
                )

    if charts:

        st.subheader("Visual Analysis")

        for index in range(0, len(charts), 2):

            chart_columns = st.columns(2)

            for position, component in enumerate(
                charts[index:index + 2]
            ):

                with chart_columns[position]:

                    render_dashboard_component(
                        data,
                        component
                    )

    if tables:

        st.subheader("Data Tables")

        for component in tables:

            render_dashboard_component(
                data,
                component
            )


# =====================================================
# SAVE DASHBOARD
# =====================================================

def save_dashboard(information, dataset, components):

    dashboards = st.session_state.setdefault(
        "jak_saved_dashboards",
        []
    )

    dashboard = {
        "id": str(uuid.uuid4()),
        "name": information["name"],
        "description": information.get("description", ""),
        "dataset_name": dataset.get("name", "Dataset"),
        "dataset_id": dataset.get("id"),
        "components": [
            component.copy()
            for component in components
        ],
        "created_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        )
    }

    dashboards.append(dashboard)

    activities = st.session_state.setdefault(
        "jak_recent_activities",
        []
    )

    activities.append({
        "title": "Dashboard Created",
        "description": f"Created dashboard: {information['name']}"
    })

    return dashboard


# =====================================================
# SAVED DASHBOARDS
# =====================================================

def render_saved_dashboards():

    render_section_heading(
        "My Saved Dashboards",
        "View dashboards saved during this session."
    )

    dashboards = st.session_state.get(
        "jak_saved_dashboards",
        []
    )

    if not dashboards:

        st.info(
            "You have not saved any dashboards yet."
        )

        return

    for dashboard in dashboards:

        with st.expander(
            dashboard["name"]
        ):

            st.write(
                dashboard.get("description", "")
            )

            st.caption(
                f"Dataset: {dashboard['dataset_name']}"
            )

            st.caption(
                f"Created: {dashboard['created_at']}"
            )

            st.write(
                f"Components: {len(dashboard['components'])}"
            )

            if st.button(
                "Delete Dashboard",
                key=f"delete_dashboard_{dashboard['id']}"
            ):

                st.session_state["jak_saved_dashboards"] = [
                    item for item in dashboards
                    if item["id"] != dashboard["id"]
                ]

                st.rerun()


# =====================================================
# MAIN DASHBOARD BUILDER
# =====================================================

def render_dashboard_builder_page():

    initialize_dashboards()

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
        "Dashboard Builder",
        "Design custom dashboards using your datasets."
    )

    render_builder_hero()

    datasets = get_valid_datasets()

    if not datasets:

        st.warning(
            "Upload a dataset before creating a dashboard."
        )

        show_footer()
        return

    dataset_options = {}

    for index, item in enumerate(datasets):

        name = item.get(
            "name",
            f"Dataset {index + 1}"
        )

        if name in dataset_options:
            name = f"{name} ({index + 1})"

        dataset_options[name] = item

    dataset_name = st.selectbox(
        "Choose Dashboard Dataset",
        list(dataset_options.keys()),
        key="jak_dashboard_dataset_selector"
    )

    selected_dataset = dataset_options[dataset_name]

    data = selected_dataset["data"].copy()

    if data.empty:

        st.warning(
            "The selected dataset is empty."
        )

        show_footer()
        return

    # Reset components when the selected dataset changes.
    previous_dataset = st.session_state.get(
        "jak_dashboard_dataset"
    )

    if previous_dataset != dataset_name:

        st.session_state["jak_dashboard_dataset"] = dataset_name

        st.session_state["jak_dashboard_components"] = []

        st.session_state["jak_builder_information"] = None

    st.divider()

    render_dashboard_overview(data)

    st.divider()

    information = render_dashboard_information()

    if information is None:

        st.info(
            "Set your dashboard information to begin."
        )

        render_saved_dashboards()

        show_footer()
        return

    components = st.session_state[
        "jak_dashboard_components"
    ]

    st.divider()

    render_section_heading(
        "Add Dashboard Components",
        "Choose the elements you want to include."
    )

    tab1, tab2, tab3 = st.tabs([
        "KPI Indicators",
        "Charts",
        "Data Tables"
    ])

    # Important: use separate variables.
    # Streamlit tabs all execute on every rerun.

    new_kpi = None
    new_chart = None
    new_table = None

    with tab1:

        new_kpi = render_kpi_builder(data)

    with tab2:

        new_chart = render_chart_builder(data)

    with tab3:

        new_table = render_table_builder(data)

    new_component = (
        new_kpi
        or new_chart
        or new_table
    )

    if new_component:

        components.append(new_component)

        st.session_state[
            "jak_dashboard_components"
        ] = components

        st.success(
            "Component added to your dashboard."
        )

        st.rerun()

    st.divider()

    st.subheader("Dashboard Components")

    if components:

        for index, component in enumerate(components):

            col1, col2 = st.columns([5, 1])

            with col1:

                st.write(
                    f"{index + 1}. {component['title']} "
                    f"({component['type'].upper()})"
                )

            with col2:

                if st.button(
                    "Remove",
                    key=f"remove_component_{component['id']}"
                ):

                    components.pop(index)

                    st.session_state[
                        "jak_dashboard_components"
                    ] = components

                    st.rerun()

    else:

        st.info(
            "No components added yet."
        )

    st.divider()

    st.subheader("Live Dashboard Preview")

    render_dashboard_preview(
        data,
        information,
        components
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "💾 Save Dashboard",
            use_container_width=True,
            type="primary"
        ):

            if not components:

                st.warning(
                    "Add at least one component before saving."
                )

            else:

                dashboard = save_dashboard(
                    information,
                    selected_dataset,
                    components
                )

                st.success(
                    f"{dashboard['name']} saved successfully!"
                )

                st.session_state[
                    "jak_dashboard_components"
                ] = []

                st.session_state[
                    "jak_builder_information"
                ] = None

                st.rerun()

    with col2:

        if st.button(
            "Clear Current Dashboard",
            use_container_width=True
        ):

            st.session_state[
                "jak_dashboard_components"
            ] = []

            st.session_state[
                "jak_builder_information"
            ] = None

            st.rerun()

    st.divider()

    render_saved_dashboards()

    show_footer()


# =====================================================
# COMPATIBILITY ALIAS
# =====================================================

render_dashboard_builder = render_dashboard_builder_page