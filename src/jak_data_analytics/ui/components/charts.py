"""
JAK Data Analytics
Interactive Charts Component

Provides reusable Plotly visualisations.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from ...config.constants import COLORS


# =====================================
# DEFAULT CHART THEME
# =====================================

def apply_chart_theme(fig, title=None, height=400):

    """
    Apply a consistent design to Plotly charts.
    """

    fig.update_layout(
        title=title,
        height=height,
        template="plotly_white",
        font=dict(
            family="Inter, sans-serif",
            color=COLORS["text"]
        ),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=30, r=30, t=60, b=30),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    fig.update_xaxes(showgrid=False)

    fig.update_yaxes(
        gridcolor="#EAECF0",
        zeroline=False
    )

    return fig


# =====================================
# BAR CHART
# =====================================

def render_bar_chart(
    data,
    x,
    y,
    title="Bar Chart",
    color=None
):

    fig = px.bar(
        data,
        x=x,
        y=y,
        color=color,
        color_discrete_sequence=[
            COLORS["primary"],
            COLORS["secondary"],
            "#818CF8",
            "#F59E0B"
        ]
    )

    fig = apply_chart_theme(fig, title)

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =====================================
# LINE CHART
# =====================================

def render_line_chart(
    data,
    x,
    y,
    title="Line Chart",
    color=None
):

    fig = px.line(
        data,
        x=x,
        y=y,
        color=color,
        markers=True,
        color_discrete_sequence=[
            COLORS["primary"],
            COLORS["secondary"]
        ]
    )

    fig = apply_chart_theme(fig, title)

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =====================================
# PIE CHART
# =====================================

def render_pie_chart(
    data,
    names,
    values,
    title="Pie Chart"
):

    fig = px.pie(
        data,
        names=names,
        values=values,
        hole=0.45,
        color_discrete_sequence=[
            COLORS["primary"],
            COLORS["secondary"],
            "#818CF8",
            "#F59E0B",
            "#EF4444"
        ]
    )

    fig = apply_chart_theme(fig, title)

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =====================================
# SCATTER CHART
# =====================================

def render_scatter_chart(
    data,
    x,
    y,
    title="Scatter Plot",
    color=None
):

    fig = px.scatter(
        data,
        x=x,
        y=y,
        color=color,
        color_discrete_sequence=[
            COLORS["primary"],
            COLORS["secondary"]
        ]
    )

    fig = apply_chart_theme(fig, title)

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =====================================
# HISTOGRAM
# =====================================

def render_histogram(
    data,
    x,
    title="Distribution"
):

    fig = px.histogram(
        data,
        x=x,
        color_discrete_sequence=[
            COLORS["primary"]
        ],
        marginal="box"
    )

    fig = apply_chart_theme(fig, title)

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =====================================
# AREA CHART
# =====================================

def render_area_chart(
    data,
    x,
    y,
    title="Area Chart"
):

    fig = px.area(
        data,
        x=x,
        y=y,
        color_discrete_sequence=[
            COLORS["secondary"]
        ]
    )

    fig = apply_chart_theme(fig, title)

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =====================================
# HEATMAP
# =====================================

def render_heatmap(
    data,
    title="Correlation Heatmap"
):

    fig = px.imshow(
        data,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Blues"
    )

    fig = apply_chart_theme(fig, title)

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =====================================
# CUSTOM PLOTLY CHART
# =====================================

def render_custom_chart(fig, title=None):

    """
    Display a custom Plotly figure.
    """

    fig = apply_chart_theme(fig, title)

    st.plotly_chart(
        fig,
        use_container_width=True
    )