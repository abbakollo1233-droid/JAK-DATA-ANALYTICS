"""
JAK Data Analytics
Data Visualization Service

Creates reusable interactive Plotly visualizations.

Features:
- Bar charts
- Line charts
- Area charts
- Pie charts
- Donut charts
- Scatter plots
- Bubble charts
- Histograms
- Box plots
- Violin plots
- Heatmaps
- Treemaps
- Sunburst charts
- Funnel charts
- Time series charts
- Automatic chart styling

This module does not depend on Streamlit.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ..config.constants import COLORS


# ==================================================
# VALIDATION
# ==================================================

def validate_dataframe(data):
    """Validate input dataset."""

    if not isinstance(data, pd.DataFrame):
        raise TypeError(
            "Input must be a pandas DataFrame."
        )

    if data.empty:
        raise ValueError(
            "Cannot visualize an empty dataset."
        )

    return True


def validate_column(data, column):
    """Check whether a column exists."""

    if column not in data.columns:
        raise ValueError(
            f"Column '{column}' does not exist."
        )


# ==================================================
# CHART THEME
# ==================================================

def apply_chart_theme(
    figure,
    title=None,
    height=450,
):
    """Apply the standard JAK chart theme."""

    figure.update_layout(
        title={
            "text": title or "",
            "x": 0.02,
            "xanchor": "left",
            "font": {
                "size": 19,
                "color": COLORS["text"],
            },
        },
        height=height,
        template="plotly_white",
        paper_bgcolor=COLORS["card"],
        plot_bgcolor=COLORS["card"],
        font={
            "family": "Inter, Arial, sans-serif",
            "color": COLORS["text"],
            "size": 12,
        },
        margin={
            "l": 45,
            "r": 30,
            "t": 75,
            "b": 45,
        },
        hoverlabel={
            "bgcolor": COLORS["sidebar"],
            "font_color": "#FFFFFF",
            "font_size": 12,
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
    )

    figure.update_xaxes(
        showgrid=False,
        linecolor=COLORS["border"],
        zeroline=False,
    )

    figure.update_yaxes(
        showgrid=True,
        gridcolor=COLORS["border"],
        zeroline=False,
    )

    return figure


# ==================================================
# BAR CHART
# ==================================================

def create_bar_chart(
    data,
    x,
    y,
    color=None,
    title="Bar Chart",
    orientation="v",
    barmode="group",
):
    """Create an interactive bar chart."""

    validate_dataframe(data)
    validate_column(data, x)
    validate_column(data, y)

    if color:
        validate_column(data, color)

    if orientation not in ["v", "h"]:
        raise ValueError(
            "Orientation must be 'v' or 'h'."
        )

    figure = px.bar(
        data,
        x=x,
        y=y,
        color=color,
        orientation=orientation,
        barmode=barmode,
        title=title,
        color_discrete_sequence=px.colors.qualitative.Set2,
        hover_data=None,
    )

    return apply_chart_theme(
        figure,
        title
    )


# ==================================================
# LINE CHART
# ==================================================

def create_line_chart(
    data,
    x,
    y,
    color=None,
    title="Line Chart",
    markers=True,
):
    """Create an interactive line chart."""

    validate_dataframe(data)
    validate_column(data, x)
    validate_column(data, y)

    if color:
        validate_column(data, color)

    figure = px.line(
        data,
        x=x,
        y=y,
        color=color,
        markers=markers,
        title=title,
    )

    return apply_chart_theme(
        figure,
        title
    )


# ==================================================
# AREA CHART
# ==================================================

def create_area_chart(
    data,
    x,
    y,
    color=None,
    title="Area Chart",
):
    """Create an interactive area chart."""

    validate_dataframe(data)
    validate_column(data, x)
    validate_column(data, y)

    if color:
        validate_column(data, color)

    figure = px.area(
        data,
        x=x,
        y=y,
        color=color,
        title=title,
    )

    return apply_chart_theme(
        figure,
        title
    )


# ==================================================
# PIE CHART
# ==================================================

def create_pie_chart(
    data,
    names,
    values=None,
    title="Pie Chart",
):
    """Create an interactive pie chart."""

    validate_dataframe(data)
    validate_column(data, names)

    if values:
        validate_column(data, values)

    figure = px.pie(
        data,
        names=names,
        values=values,
        title=title,
        hole=0,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )

    figure.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate=(
            "%{label}<br>"
            "Value: %{value}<br>"
            "Percentage: %{percent}"
            "<extra></extra>"
        ),
    )

    return apply_chart_theme(
        figure,
        title
    )


# ==================================================
# DONUT CHART
# ==================================================

def create_donut_chart(
    data,
    names,
    values=None,
    title="Donut Chart",
):
    """Create an interactive donut chart."""

    validate_dataframe(data)
    validate_column(data, names)

    if values:
        validate_column(data, values)

    figure = px.pie(
        data,
        names=names,
        values=values,
        title=title,
        hole=0.55,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )

    figure.update_traces(
        textposition="inside",
        textinfo="percent+label",
    )

    return apply_chart_theme(
        figure,
        title
    )


# ==================================================
# SCATTER CHART
# ==================================================

def create_scatter_chart(
    data,
    x,
    y,
    color=None,
    size=None,
    title="Scatter Plot",
):
    """Create an interactive scatter plot."""

    validate_dataframe(data)
    validate_column(data, x)
    validate_column(data, y)

    if color:
        validate_column(data, color)

    if size:
        validate_column(data, size)

    figure = px.scatter(
        data,
        x=x,
        y=y,
        color=color,
        size=size,
        title=title,
        opacity=0.8,
    )

    return apply_chart_theme(
        figure,
        title
    )


# ==================================================
# HISTOGRAM
# ==================================================

def create_histogram(
    data,
    column,
    color=None,
    bins=30,
    title="Histogram",
):
    """Create an interactive histogram."""

    validate_dataframe(data)
    validate_column(data, column)

    if color:
        validate_column(data, color)

    if not 1 <= bins <= 200:
        raise ValueError(
            "Number of bins must be between 1 and 200."
        )

    figure = px.histogram(
        data,
        x=column,
        color=color,
        nbins=bins,
        title=title,
        marginal="box",
    )

    return apply_chart_theme(
        figure,
        title
    )


# ==================================================
# BOX PLOT
# ==================================================

def create_box_plot(
    data,
    y,
    x=None,
    color=None,
    title="Box Plot",
):
    """Create an interactive box plot."""

    validate_dataframe(data)
    validate_column(data, y)

    if x:
        validate_column(data, x)

    if color:
        validate_column(data, color)

    figure = px.box(
        data,
        x=x,
        y=y,
        color=color,
        points="outliers",
        title=title,
    )

    return apply_chart_theme(
        figure,
        title
    )


# ==================================================
# VIOLIN PLOT
# ==================================================

def create_violin_plot(
    data,
    y,
    x=None,
    color=None,
    title="Violin Plot",
):
    """Create an interactive violin plot."""

    validate_dataframe(data)
    validate_column(data, y)

    if x:
        validate_column(data, x)

    if color:
        validate_column(data, color)

    figure = px.violin(
        data,
        x=x,
        y=y,
        color=color,
        box=True,
        points="outliers",
        title=title,
    )

    return apply_chart_theme(
        figure,
        title
    )


# ==================================================
# CORRELATION HEATMAP
# ==================================================

def create_correlation_heatmap(
    data,
    method="pearson",
    title="Correlation Heatmap",
):
    """Create a correlation heatmap."""

    validate_dataframe(data)

    numeric = data.select_dtypes(
        include="number"
    )

    if numeric.shape[1] < 2:
        raise ValueError(
            "At least two numerical columns are required."
        )

    if method not in [
        "pearson",
        "spearman",
        "kendall",
    ]:
        raise ValueError(
            "Unsupported correlation method."
        )

    correlation = numeric.corr(
        method=method
    )

    figure = px.imshow(
        correlation,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title=title,
    )

    return apply_chart_theme(
        figure,
        title,
        height=550,
    )


# ==================================================
# TREEMAP
# ==================================================

def create_treemap(
    data,
    path,
    values=None,
    title="Treemap",
):
    """Create an interactive treemap."""

    validate_dataframe(data)

    if isinstance(path, str):
        path = [path]

    if not path:
        raise ValueError(
            "At least one hierarchy column is required."
        )

    for column in path:
        validate_column(data, column)

    if values:
        validate_column(data, values)

    figure = px.treemap(
        data,
        path=path,
        values=values,
        title=title,
    )

    return apply_chart_theme(
        figure,
        title
    )


# ==================================================
# SUNBURST
# ==================================================

def create_sunburst(
    data,
    path,
    values=None,
    title="Sunburst Chart",
):
    """Create an interactive sunburst chart."""

    validate_dataframe(data)

    if isinstance(path, str):
        path = [path]

    if not path:
        raise ValueError(
            "At least one hierarchy column is required."
        )

    for column in path:
        validate_column(data, column)

    if values:
        validate_column(data, values)

    figure = px.sunburst(
        data,
        path=path,
        values=values,
        title=title,
    )

    return apply_chart_theme(
        figure,
        title
    )


# ==================================================
# FUNNEL CHART
# ==================================================

def create_funnel_chart(
    data,
    x,
    y,
    title="Funnel Chart",
):
    """Create an interactive funnel chart."""

    validate_dataframe(data)
    validate_column(data, x)
    validate_column(data, y)

    figure = px.funnel(
        data,
        x=x,
        y=y,
        title=title,
    )

    return apply_chart_theme(
        figure,
        title
    )


# ==================================================
# TIME SERIES CHART
# ==================================================

def create_time_series_chart(
    data,
    date_column,
    value_column,
    frequency=None,
    aggregation="sum",
    title="Time Series Analysis",
):
    """Create a time series chart with optional aggregation."""

    validate_dataframe(data)
    validate_column(data, date_column)
    validate_column(data, value_column)

    allowed = [
        "sum",
        "mean",
        "median",
        "min",
        "max",
        "count",
    ]

    if aggregation not in allowed:
        raise ValueError(
            "Unsupported aggregation method."
        )

    cleaned = data[
        [date_column, value_column]
    ].copy()

    cleaned[date_column] = pd.to_datetime(
        cleaned[date_column],
        errors="coerce"
    )

    cleaned[value_column] = pd.to_numeric(
        cleaned[value_column],
        errors="coerce"
    )

    cleaned = cleaned.dropna(
        subset=[date_column]
    )

    if cleaned.empty:
        raise ValueError(
            "No valid dates were found."
        )

    if frequency:

        if aggregation == "count":
            result = (
                cleaned.set_index(date_column)
                .resample(frequency)[value_column]
                .count()
                .reset_index()
            )

        else:
            result = (
                cleaned.set_index(date_column)
                .resample(frequency)[value_column]
            )

            result = getattr(
                result,
                aggregation
            )().reset_index()

    else:
        result = cleaned.sort_values(
            date_column
        )

    figure = px.line(
        result,
        x=date_column,
        y=value_column,
        markers=True,
        title=title,
    )

    return apply_chart_theme(
        figure,
        title
    )


# ==================================================
# CUSTOM GRAPH OBJECT
# ==================================================

def create_custom_chart(
    data,
    chart_type,
    x=None,
    y=None,
    title="Custom Visualization",
):
    """Create a chart using a supported chart type."""

    chart_type = chart_type.lower().strip()

    chart_functions = {
        "bar": create_bar_chart,
        "line": create_line_chart,
        "area": create_area_chart,
        "pie": create_pie_chart,
        "donut": create_donut_chart,
        "scatter": create_scatter_chart,
        "histogram": create_histogram,
        "box": create_box_plot,
        "violin": create_violin_plot,
        "funnel": create_funnel_chart,
    }

    if chart_type not in chart_functions:
        raise ValueError(
            f"Unsupported chart type: {chart_type}"
        )

    function = chart_functions[chart_type]

    if chart_type in ["pie", "donut"]:
        return function(
            data,
            names=x,
            values=y,
            title=title,
        )

    if chart_type == "histogram":
        return function(
            data,
            column=x,
            title=title,
        )

    if chart_type in ["box", "violin"]:
        return function(
            data,
            y=y,
            x=x,
            title=title,
        )

    return function(
        data,
        x=x,
        y=y,
        title=title,
    )


# ==================================================
# EXPORT CHART
# ==================================================

def export_chart_html(
    figure,
    file_path,
):
    """Export an interactive chart as a standalone HTML file."""

    if not isinstance(
        figure,
        (go.Figure,)
    ):
        raise TypeError(
            "A Plotly Figure is required."
        )

    figure.write_html(
        str(file_path),
        include_plotlyjs=True,
        full_html=True,
    )

    return str(file_path)


def export_chart_image(
    figure,
    file_path,
    width=1200,
    height=800,
):
    """
    Export a chart as an image.

    Requires the optional Kaleido package.
    """

    if not isinstance(
        figure,
        go.Figure
    ):
        raise TypeError(
            "A Plotly Figure is required."
        )

    figure.write_image(
        str(file_path),
        width=width,
        height=height,
    )

    return str(file_path)