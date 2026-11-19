"""
JAK Data Analytics
Reusable Metric Cards
"""

import streamlit as st


def render_metric_card(
    title,
    value,
    description=None,
    delta=None,
):
    """Display a reusable Streamlit metric."""

    st.metric(
        label=title,
        value=value,
        delta=delta,
        help=description,
    )


def render_metric_grid(metrics, columns=4):
    """
    Display multiple metrics in a responsive grid.

    metrics example:
    [
        {"title": "Rows", "value": 1000},
        {"title": "Columns", "value": 12}
    ]
    """

    if not metrics:
        return

    columns = max(1, min(int(columns), 6))

    for start in range(0, len(metrics), columns):

        row_metrics = metrics[start:start + columns]

        cols = st.columns(len(row_metrics))

        for col, metric in zip(cols, row_metrics):

            with col:

                render_metric_card(
                    title=metric.get("title", "Metric"),
                    value=metric.get("value", 0),
                    description=metric.get("description"),
                    delta=metric.get("delta"),
                )