"""
JAK Data Analytics
Data Visualisation Module

Creates interactive charts and visual reports.

Features:
- Interactive chart builder
- Bar, line and area charts
- Pie and donut charts
- Scatter and bubble charts
- Histogram, box and violin plots
- Correlation heatmaps
- Funnel charts
- Treemaps and sunburst charts
- Downloadable interactive charts

Uses native Streamlit components.
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
# DATASET MANAGEMENT
# =====================================================

def get_datasets():
    """Return available datasets."""

    return st.session_state.get("jak_datasets", [])


def render_visualisation_hero():
    """Display the visualisation introduction."""

    with st.container(border=True):

        st.subheader("📊 Interactive Data Visualisation Studio")

        st.write(
            "Transform your datasets into meaningful charts, "
            "interactive graphs and visual insights. "
            "Explore patterns and communicate your findings."
        )


# =====================================================
# DATASET SELECTOR
# =====================================================

def render_dataset_selector():

    datasets = get_datasets()

    valid_datasets = []

    for item in datasets:

        if (
            isinstance(item, dict)
            and isinstance(item.get("data"), pd.DataFrame)
        ):
            valid_datasets.append(item)

    if not valid_datasets:

        st.warning(
            "No datasets available. Upload a dataset first."
        )

        return None, None

    options = {}

    for index, item in enumerate(valid_datasets):

        name = item.get("name", f"Dataset {index + 1}")

        if name in options:
            name = f"{name} ({index + 1})"

        options[name] = item

    selected_name = st.selectbox(
        "Select Dataset",
        list(options.keys()),
        key="jak_visualisation_dataset"
    )

    return options[selected_name], selected_name


# =====================================================
# DATASET OVERVIEW
# =====================================================

def render_dataset_overview(data):

    numeric_count = len(
        data.select_dtypes(include="number").columns
    )

    categorical_count = len(
        data.select_dtypes(
            include=["object", "string", "category", "bool"]
        ).columns
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Records",
        f"{len(data):,}"
    )

    col2.metric(
        "Total Columns",
        f"{len(data.columns):,}"
    )

    col3.metric(
        "Numeric Columns",
        numeric_count
    )

    col4.metric(
        "Categorical Columns",
        categorical_count
    )


# =====================================================
# CHART CONFIGURATION
# =====================================================

def render_chart_settings(data):

    render_section_heading(
        "Chart Configuration",
        "Choose a chart type and configure the variables."
    )

    chart_types = [
        "Bar Chart",
        "Line Chart",
        "Area Chart",
        "Pie Chart",
        "Donut Chart",
        "Scatter Plot",
        "Bubble Chart",
        "Histogram",
        "Box Plot",
        "Violin Plot",
        "Heatmap",
        "Funnel Chart",
        "Treemap",
        "Sunburst Chart"
    ]

    chart_type = st.selectbox(
        "Choose Visualisation Type",
        chart_types,
        key="jak_chart_type"
    )

    columns = data.columns.tolist()

    numeric_columns = data.select_dtypes(
        include="number"
    ).columns.tolist()

    categorical_columns = data.select_dtypes(
        include=["object", "string", "category", "bool"]
    ).columns.tolist()

    x_column = None
    y_column = None
    color_column = None
    size_column = None

    aggregation = "Sum"
    bins = 30

    category_charts = [
        "Bar Chart",
        "Line Chart",
        "Area Chart",
        "Pie Chart",
        "Donut Chart",
        "Funnel Chart",
        "Treemap",
        "Sunburst Chart"
    ]

    distribution_charts = [
        "Box Plot",
        "Violin Plot"
    ]

    # ---------------------------------------------
    # CATEGORY-BASED CHARTS
    # ---------------------------------------------

    if chart_type in category_charts + distribution_charts:

        preferred_x = (
            categorical_columns
            if categorical_columns
            else columns
        )

        x_column = st.selectbox(
            "Category / X-Axis",
            preferred_x,
            key="jak_visual_x"
        )

    # ---------------------------------------------
    # SCATTER AND BUBBLE CHARTS
    # ---------------------------------------------

    elif chart_type in ["Scatter Plot", "Bubble Chart"]:

        if len(numeric_columns) < 2:

            st.warning(
                "This chart requires at least two numeric columns."
            )

            return None

        col1, col2 = st.columns(2)

        with col1:

            x_column = st.selectbox(
                "X-Axis",
                numeric_columns,
                key="jak_visual_x"
            )

        with col2:

            y_column = st.selectbox(
                "Y-Axis",
                numeric_columns,
                index=1,
                key="jak_visual_y"
            )

        if chart_type == "Bubble Chart":

            size_column = st.selectbox(
                "Bubble Size",
                numeric_columns,
                key="jak_visual_size"
            )

    # ---------------------------------------------
    # HISTOGRAM
    # ---------------------------------------------

    elif chart_type == "Histogram":

        if not numeric_columns:

            st.warning(
                "Histogram requires at least one numeric column."
            )

            return None

        x_column = st.selectbox(
            "Numeric Variable",
            numeric_columns,
            key="jak_visual_x"
        )

        bins = st.slider(
            "Number of Bins",
            min_value=5,
            max_value=100,
            value=30,
            key="jak_visual_bins"
        )

    # ---------------------------------------------
    # HEATMAP
    # ---------------------------------------------

    elif chart_type == "Heatmap":

        if len(numeric_columns) < 2:

            st.warning(
                "Heatmap requires at least two numeric columns."
            )

            return None

        return {
            "type": chart_type
        }

    # ---------------------------------------------
    # NUMERIC VALUE AND AGGREGATION
    # ---------------------------------------------

    if chart_type in category_charts:

        if numeric_columns:

            y_column = st.selectbox(
                "Numeric Value",
                numeric_columns,
                key="jak_visual_y"
            )

            aggregation = st.selectbox(
                "Aggregation",
                [
                    "Sum",
                    "Mean",
                    "Median",
                    "Count",
                    "Minimum",
                    "Maximum"
                ],
                key="jak_visual_aggregation"
            )

        elif chart_type in ["Pie Chart", "Donut Chart"]:

            aggregation = "Count"

        else:

            st.warning(
                "This chart requires a numeric column. "
                "Choose a Pie Chart or Donut Chart to visualise counts."
            )

            return None

    # ---------------------------------------------
    # BOX AND VIOLIN PLOT VALUES
    # ---------------------------------------------

    if chart_type in distribution_charts:

        if not numeric_columns:

            st.warning(
                "This chart requires at least one numeric column."
            )

            return None

        y_column = st.selectbox(
            "Numeric Variable",
            numeric_columns,
            key="jak_visual_distribution_y"
        )

    # ---------------------------------------------
    # COLOUR GROUP
    # ---------------------------------------------

    if chart_type in [
        "Bar Chart",
        "Line Chart",
        "Area Chart",
        "Scatter Plot",
        "Bubble Chart",
        "Box Plot",
        "Violin Plot"
    ]:

        color_options = ["(None)"] + columns

        color_column = st.selectbox(
            "Colour Group",
            color_options,
            key="jak_visual_color"
        )

        if color_column == "(None)":
            color_column = None

    return {
        "type": chart_type,
        "x": x_column,
        "y": y_column,
        "color": color_column,
        "size": size_column,
        "aggregation": aggregation,
        "bins": bins
    }


# =====================================================
# DATA AGGREGATION
# =====================================================

def prepare_aggregated_data(data, settings):

    x = settings["x"]
    y = settings["y"]

    aggregation_map = {
        "Sum": "sum",
        "Mean": "mean",
        "Median": "median",
        "Count": "count",
        "Minimum": "min",
        "Maximum": "max"
    }

    if y is None:

        result = (
            data.groupby(
                x,
                dropna=False,
                observed=False
            )
            .size()
            .reset_index(name="Count")
        )

        return result, "Count"

    operation = aggregation_map[
        settings["aggregation"]
    ]

    if operation == "count":

        result = (
            data.groupby(
                x,
                dropna=False,
                observed=False
            )[y]
            .count()
            .reset_index(name="Count")
        )

        return result, "Count"

    result = (
        data.groupby(
            x,
            dropna=False,
            observed=False
        )[y]
        .agg(operation)
        .reset_index()
    )

    return result, y


# =====================================================
# BUILD VISUALISATION
# =====================================================

def build_visualisation(data, settings):

    chart_type = settings["type"]

    x = settings.get("x")
    y = settings.get("y")
    color = settings.get("color")

    # ---------------------------------------------
    # CATEGORY-BASED CHARTS
    # ---------------------------------------------

    if chart_type in [
        "Bar Chart",
        "Line Chart",
        "Area Chart",
        "Pie Chart",
        "Donut Chart",
        "Funnel Chart",
        "Treemap",
        "Sunburst Chart"
    ]:

        chart_data, value_column = prepare_aggregated_data(
            data,
            settings
        )

        if chart_type == "Bar Chart":

            fig = px.bar(
                chart_data,
                x=x,
                y=value_column,
                color=color if color in chart_data.columns else None,
                title=f"{settings['aggregation']} of {value_column} by {x}"
            )

        elif chart_type == "Line Chart":

            fig = px.line(
                chart_data,
                x=x,
                y=value_column,
                markers=True,
                title=f"{value_column} by {x}"
            )

        elif chart_type == "Area Chart":

            fig = px.area(
                chart_data,
                x=x,
                y=value_column,
                title=f"{value_column} by {x}"
            )

        elif chart_type == "Pie Chart":

            fig = px.pie(
                chart_data,
                names=x,
                values=value_column,
                title=f"{value_column} Distribution"
            )

        elif chart_type == "Donut Chart":

            fig = px.pie(
                chart_data,
                names=x,
                values=value_column,
                hole=0.55,
                title=f"{value_column} Distribution"
            )

        elif chart_type == "Funnel Chart":

            fig = px.funnel(
                chart_data,
                x=value_column,
                y=x,
                title=f"{value_column} Funnel"
            )

        elif chart_type == "Treemap":

            fig = px.treemap(
                chart_data,
                path=[x],
                values=value_column,
                title=f"{value_column} Treemap"
            )

        else:

            fig = px.sunburst(
                chart_data,
                path=[x],
                values=value_column,
                title=f"{value_column} Sunburst"
            )

    # ---------------------------------------------
    # SCATTER PLOT
    # ---------------------------------------------

    elif chart_type == "Scatter Plot":

        fig = px.scatter(
            data,
            x=x,
            y=y,
            color=color,
            title=f"{y} vs {x}"
        )

    # ---------------------------------------------
    # BUBBLE CHART
    # ---------------------------------------------

    elif chart_type == "Bubble Chart":

        fig = px.scatter(
            data,
            x=x,
            y=y,
            size=settings["size"],
            color=color,
            title=f"{y} vs {x} Bubble Chart"
        )

    # ---------------------------------------------
    # HISTOGRAM
    # ---------------------------------------------

    elif chart_type == "Histogram":

        fig = px.histogram(
            data,
            x=x,
            nbins=settings["bins"],
            title=f"Distribution of {x}"
        )

    # ---------------------------------------------
    # BOX PLOT
    # ---------------------------------------------

    elif chart_type == "Box Plot":

        fig = px.box(
            data,
            x=x,
            y=y,
            color=color,
            title=f"Box Plot of {y} by {x}"
        )

    # ---------------------------------------------
    # VIOLIN PLOT
    # ---------------------------------------------

    elif chart_type == "Violin Plot":

        fig = px.violin(
            data,
            x=x,
            y=y,
            color=color,
            box=True,
            points="outliers",
            title=f"Violin Plot of {y} by {x}"
        )

    # ---------------------------------------------
    # CORRELATION HEATMAP
    # ---------------------------------------------

    elif chart_type == "Heatmap":

        numeric = data.select_dtypes(
            include="number"
        )

        correlation = numeric.corr()

        fig = px.imshow(
            correlation,
            text_auto=".2f",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            title="Correlation Heatmap"
        )

    else:

        raise ValueError(
            "Unsupported chart type."
        )

    fig.update_layout(
        template="plotly_white",
        height=520,
        margin=dict(
            l=30,
            r=30,
            t=70,
            b=40
        ),
        font=dict(
            family="Inter, sans-serif"
        )
    )

    return fig


# =====================================================
# CHART BUILDER
# =====================================================

def render_chart_builder(data, dataset_name):

    settings = render_chart_settings(data)

    if settings is None:
        return

    if st.button(
        "Generate Visualisation",
        type="primary",
        use_container_width=True,
        key="jak_generate_visualisation"
    ):

        try:

            fig = build_visualisation(
                data,
                settings
            )

            st.session_state["jak_current_visualisation"] = {
                "figure": fig,
                "dataset_name": dataset_name,
                "chart_type": settings["type"]
            }

            st.success(
                "Visualisation generated successfully."
            )

        except Exception as error:

            st.error(
                f"Unable to generate chart: {error}"
            )

    current = st.session_state.get(
        "jak_current_visualisation"
    )

    if (
        current
        and current.get("dataset_name") == dataset_name
    ):

        st.divider()

        st.subheader("Visualisation Preview")

        st.plotly_chart(
            current["figure"],
            use_container_width=True,
            key="jak_visualisation_preview"
        )

        st.download_button(
            "⬇️ Download Interactive Chart",
            data=current["figure"].to_html(
                include_plotlyjs="cdn"
            ),
            file_name="jak_visualisation.html",
            mime="text/html",
            use_container_width=True
        )

        st.caption(
            "The downloaded HTML file can be opened in a web browser."
        )


# =====================================================
# MAIN PAGE
# =====================================================

def render_visualisations_page():

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
        "Data Visualisations",
        "Create interactive charts and explore your data visually."
    )

    render_visualisation_hero()

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

    st.session_state["jak_selected_visual_dataset"] = dataset_name

    st.divider()

    render_dataset_overview(data)

    st.divider()

    render_chart_builder(
        data,
        dataset_name
    )

    show_footer()


# =====================================================
# COMPATIBILITY ALIASES
# =====================================================

render_visualisations = render_visualisations_page