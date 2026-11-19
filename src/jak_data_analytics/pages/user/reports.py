
"""
JAK Data Analytics
Reports Centre

Features:
- Dataset summary reports
- Data quality reports
- Statistical reports
- Executive summaries
- PDF report generation
- CSV report generation
- Report history

Reports are generated from datasets and analytical
information available in the current session.
"""

import io
import html
import re
from datetime import datetime

import streamlit as st
import pandas as pd
import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from ...ui.layout import (
    render_topbar,
    render_page_intro,
    render_section_heading,
)

from ...ui.theme import show_footer


# =========================================================
# REPORT STATE
# =========================================================

def initialize_report_state():

    if "jak_report_history" not in st.session_state:
        st.session_state["jak_report_history"] = []

    if "jak_generated_report" not in st.session_state:
        st.session_state["jak_generated_report"] = None

    if "jak_report_selected_data" not in st.session_state:
        st.session_state["jak_report_selected_data"] = None

    if "jak_report_signature" not in st.session_state:
        st.session_state["jak_report_signature"] = None


# =========================================================
# REPORT INTRODUCTION
# =========================================================

def render_reports_hero():

    with st.container(border=True):

        st.caption("JAK ANALYTICS | REPORTING")

        st.title("Professional Reports Centre")

        st.write(
            "Transform your data analysis into organised, "
            "professional reports that can be downloaded, "
            "reviewed and shared."
        )

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Export Formats", "PDF and CSV")

        with col2:
            st.metric("Report Storage", "Current Session")


def render_report_information():

    st.info(
        "JAK can combine dataset information, data quality "
        "measurements and statistical summaries into "
        "downloadable analytical reports."
    )


# =========================================================
# DATASET INFORMATION
# =========================================================

def get_dataset_statistics(data):

    numeric_columns = data.select_dtypes(
        include="number"
    ).columns.tolist()

    categorical_columns = data.select_dtypes(
        include=["object", "string", "category", "bool"]
    ).columns.tolist()

    return {
        "rows": len(data),
        "columns": len(data.columns),
        "numeric_columns": len(numeric_columns),
        "categorical_columns": len(categorical_columns),
        "missing_cells": int(data.isna().sum().sum()),
        "duplicate_rows": int(data.duplicated().sum()),
        "memory_mb": round(
            data.memory_usage(deep=True).sum() / (1024 ** 2),
            2
        ),
        "numeric": numeric_columns,
        "categorical": categorical_columns,
    }


# =========================================================
# DATA QUALITY REPORT
# =========================================================

def build_quality_report(data):

    missing = data.isna().sum()

    missing_report = pd.DataFrame({
        "Column": missing.index.astype(str),
        "Missing Values": missing.values,
        "Missing Percentage": (
            missing.values / max(len(data), 1)
        ) * 100
    })

    duplicate_count = int(data.duplicated().sum())

    constant_columns = [
        str(column)
        for column in data.columns
        if data[column].nunique(dropna=False) <= 1
    ]

    total_cells = data.shape[0] * data.shape[1]

    missing_rate = (
        data.isna().sum().sum() / total_cells
        if total_cells else 0
    )

    duplicate_rate = (
        duplicate_count / max(len(data), 1)
    )

    score = max(
        0,
        100 - (
            missing_rate * 70
            + duplicate_rate * 30
        ) * 100
    )

    return {
        "missing": missing_report,
        "duplicates": duplicate_count,
        "constant_columns": constant_columns,
        "quality_score": round(score, 2)
    }


# =========================================================
# STATISTICAL REPORT
# =========================================================

def build_statistical_report(data):

    numeric = data.select_dtypes(
        include="number"
    )

    if numeric.empty:
        return pd.DataFrame()

    result = numeric.describe().T.reset_index()

    result = result.rename(
        columns={"index": "Column"}
    )

    return result


# =========================================================
# CATEGORICAL REPORT
# =========================================================

def build_categorical_report(data):

    categorical = data.select_dtypes(
        include=["object", "string", "category", "bool"]
    )

    rows = []

    for column in categorical.columns:

        mode_values = categorical[column].mode()

        most_frequent = (
            str(mode_values.iloc[0])
            if not mode_values.empty
            else "N/A"
        )

        rows.append({
            "Column": str(column),
            "Unique Values": int(
                categorical[column].nunique(dropna=True)
            ),
            "Most Frequent": most_frequent,
            "Missing Values": int(
                categorical[column].isna().sum()
            )
        })

    return pd.DataFrame(rows)


# =========================================================
# COMPLETE DATASET REPORT
# =========================================================

def build_dataset_report(data, dataset_name):

    statistics = get_dataset_statistics(data)

    quality = build_quality_report(data)

    statistical_report = build_statistical_report(data)

    categorical_report = build_categorical_report(data)

    return {
        "name": dataset_name,
        "created_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "statistics": statistics,
        "quality": quality,
        "statistical": statistical_report,
        "categorical": categorical_report,
        "columns": [
            str(column)
            for column in data.columns
        ]
    }


# =========================================================
# EXECUTIVE SUMMARY
# =========================================================

def build_executive_summary(report):

    stats = report["statistics"]

    quality = report["quality"]

    if quality["quality_score"] >= 90:
        quality_label = "Strong"

    elif quality["quality_score"] >= 70:
        quality_label = "Moderate"

    else:
        quality_label = "Needs Attention"

    return (
        f"The dataset '{report['name']}' contains "
        f"{stats['rows']:,} records and "
        f"{stats['columns']:,} columns. "
        f"It includes {stats['numeric_columns']} numerical "
        f"columns and {stats['categorical_columns']} categorical "
        f"columns. The dataset has {stats['missing_cells']:,} "
        f"missing cells and {stats['duplicate_rows']:,} duplicate "
        f"rows. Its preliminary data quality score is "
        f"{quality['quality_score']:.2f}%, classified as "
        f"{quality_label}."
    )


# =========================================================
# REPORT OVERVIEW
# =========================================================

def render_report_overview(report):

    stats = report["statistics"]

    quality = report["quality"]

    render_section_heading(
        "Report Overview",
        "Key information about the selected dataset."
    )

    columns = st.columns(4)

    metrics = [
        ("Records", f"{stats['rows']:,}"),
        ("Columns", stats["columns"]),
        ("Missing Cells", f"{stats['missing_cells']:,}"),
        ("Quality Score", f"{quality['quality_score']:.1f}%")
    ]

    for column, item in zip(columns, metrics):

        column.metric(
            item[0],
            item[1]
        )

    st.subheader("Executive Summary")

    st.info(
        build_executive_summary(report)
    )


# =========================================================
# DATA QUALITY PREVIEW
# =========================================================

def render_report_quality(report):

    render_section_heading(
        "Data Quality Report",
        "Review missing values, duplicates and constant columns."
    )

    quality = report["quality"]

    first, second, third = st.columns(3)

    first.metric(
        "Quality Score",
        f"{quality['quality_score']:.2f}%"
    )

    second.metric(
        "Duplicate Rows",
        quality["duplicates"]
    )

    third.metric(
        "Constant Columns",
        len(quality["constant_columns"])
    )

    st.dataframe(
        quality["missing"],
        use_container_width=True,
        hide_index=True
    )

    if quality["constant_columns"]:

        st.warning(
            "Constant columns: "
            + ", ".join(quality["constant_columns"])
        )

    st.caption(
        "The quality score is a preliminary heuristic based "
        "on missing values and duplicate rows. It does not "
        "measure accuracy, fairness or overall fitness for use."
    )


# =========================================================
# STATISTICAL PREVIEW
# =========================================================

def render_report_statistics(report, data):

    render_section_heading(
        "Statistical Report",
        "Descriptive statistics for numerical columns."
    )

    statistical = report["statistical"]

    if statistical.empty:

        st.info(
            "No numerical columns are available."
        )

        return

    st.dataframe(
        statistical,
        use_container_width=True,
        hide_index=True
    )

    numeric_columns = report["statistics"]["numeric"]

    selected_column = st.selectbox(
        "Select a numerical variable",
        numeric_columns,
        key="jak_report_numeric_column"
    )

    chart_data = pd.to_numeric(
        data[selected_column],
        errors="coerce"
    ).dropna()

    if chart_data.empty:

        st.warning(
            "No valid numerical values are available for this chart."
        )

        return

    import plotly.express as px

    fig = px.histogram(
        x=chart_data,
        title=f"Distribution of {selected_column}",
        labels={"x": selected_column}
    )

    fig.update_layout(
        template="plotly_white",
        height=400
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =========================================================
# CATEGORICAL PREVIEW
# =========================================================

def render_report_categorical(report):

    render_section_heading(
        "Categorical Report",
        "Explore the structure of categorical variables."
    )

    categorical = report["categorical"]

    if categorical.empty:

        st.info(
            "No categorical columns are available."
        )

        return

    st.dataframe(
        categorical,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# PDF HELPER FUNCTIONS
# =========================================================

def safe_pdf_text(value):

    return html.escape(
        str(value)
    ).replace(
        "\n",
        "<br/>"
    )


def pdf_table(data, styles):

    if data is None or data.empty:

        return [
            Paragraph(
                "No data available.",
                styles["Normal"]
            )
        ]

    headers = [
        safe_pdf_text(column)
        for column in data.columns
    ]

    rows = [headers]

    for row in data.head(100).itertuples(
        index=False,
        name=None
    ):

        rows.append([
            safe_pdf_text(value)
            for value in row
        ])

    table = Table(
        rows,
        repeatRows=1
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#101828")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.HexColor("#D0D5DD")
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#F8FAFC")
                ]
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
        ])
    )

    return [table]


# =========================================================
# PDF REPORT GENERATION
# =========================================================

def generate_pdf_report(report, selected_sections):

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=17 * mm,
        leftMargin=17 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="JAKTitle",
            parent=styles["Title"],
            textColor=colors.HexColor("#101828"),
            fontSize=23,
            leading=28,
            spaceAfter=12
        )
    )

    styles.add(
        ParagraphStyle(
            name="JAKHeading",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#2563EB"),
            spaceBefore=15,
            spaceAfter=8
        )
    )

    story = []

    story.append(
        Paragraph(
            "JAK DATA ANALYTICS",
            styles["JAKTitle"]
        )
    )

    story.append(
        Paragraph(
            "Professional Analytical Report",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            f"Dataset: {safe_pdf_text(report['name'])}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            f"Generated: {safe_pdf_text(report['created_at'])}",
            styles["Normal"]
        )
    )

    story.append(
        Spacer(1, 12)
    )

    if "Executive Summary" in selected_sections:

        story.append(
            Paragraph(
                "Executive Summary",
                styles["JAKHeading"]
            )
        )

        story.append(
            Paragraph(
                safe_pdf_text(
                    build_executive_summary(report)
                ),
                styles["BodyText"]
            )
        )

    if "Dataset Overview" in selected_sections:

        story.append(
            Paragraph(
                "Dataset Overview",
                styles["JAKHeading"]
            )
        )

        overview = pd.DataFrame({
            "Metric": [
                "Rows",
                "Columns",
                "Numerical Columns",
                "Categorical Columns",
                "Missing Cells",
                "Duplicate Rows",
                "Memory Usage (MB)"
            ],
            "Value": [
                report["statistics"]["rows"],
                report["statistics"]["columns"],
                report["statistics"]["numeric_columns"],
                report["statistics"]["categorical_columns"],
                report["statistics"]["missing_cells"],
                report["statistics"]["duplicate_rows"],
                report["statistics"]["memory_mb"]
            ]
        })

        story.extend(
            pdf_table(
                overview,
                styles
            )
        )

    if "Data Quality" in selected_sections:

        story.append(
            Paragraph(
                "Data Quality",
                styles["JAKHeading"]
            )
        )

        story.append(
            Paragraph(
                f"Preliminary quality score: "
                f"{report['quality']['quality_score']:.2f}%",
                styles["Normal"]
            )
        )

        story.extend(
            pdf_table(
                report["quality"]["missing"],
                styles
            )
        )

        story.append(
            Paragraph(
                f"Duplicate rows: {report['quality']['duplicates']}",
                styles["Normal"]
            )
        )

        if report["quality"]["constant_columns"]:

            story.append(
                Paragraph(
                    "Constant columns: "
                    + safe_pdf_text(
                        ", ".join(
                            report["quality"]["constant_columns"]
                        )
                    ),
                    styles["Normal"]
                )
            )

        story.append(
            Paragraph(
                "Quality score is a preliminary heuristic, "
                "not a complete measure of data reliability.",
                styles["Italic"]
            )
        )

    if "Statistical Analysis" in selected_sections:

        story.append(
            Paragraph(
                "Statistical Analysis",
                styles["JAKHeading"]
            )
        )

        story.extend(
            pdf_table(
                report["statistical"],
                styles
            )
        )

    if "Categorical Analysis" in selected_sections:

        story.append(
            Paragraph(
                "Categorical Analysis",
                styles["JAKHeading"]
            )
        )

        story.extend(
            pdf_table(
                report["categorical"],
                styles
            )
        )

    story.append(
        Spacer(1, 15)
    )

    story.append(
        Paragraph(
            "Prepared by JAK Data Analytics. "
            "Analytical results should be interpreted "
            "in the context of the source data and "
            "the limitations of the selected methods.",
            styles["Italic"]
        )
    )

    document.build(story)

    buffer.seek(0)

    return buffer.getvalue()


# =========================================================
# CSV REPORT GENERATION
# =========================================================

def generate_csv_report(report):

    frames = []

    statistics = report["statistics"]

    overview = pd.DataFrame({
        "Metric": [
            "Dataset",
            "Rows",
            "Columns",
            "Numerical Columns",
            "Categorical Columns",
            "Missing Cells",
            "Duplicate Rows",
            "Quality Score (%)"
        ],
        "Value": [
            report["name"],
            statistics["rows"],
            statistics["columns"],
            statistics["numeric_columns"],
            statistics["categorical_columns"],
            statistics["missing_cells"],
            statistics["duplicate_rows"],
            report["quality"]["quality_score"]
        ]
    })

    frames.append(
        "DATASET OVERVIEW\n"
        + overview.to_csv(index=False)
    )

    frames.append(
        "\nDATA QUALITY\n"
        + report["quality"]["missing"].to_csv(index=False)
    )

    if not report["statistical"].empty:

        frames.append(
            "\nSTATISTICAL ANALYSIS\n"
            + report["statistical"].to_csv(index=False)
        )

    if not report["categorical"].empty:

        frames.append(
            "\nCATEGORICAL ANALYSIS\n"
            + report["categorical"].to_csv(index=False)
        )

    return "\n".join(frames).encode("utf-8-sig")


# =========================================================
# REPORT HISTORY
# =========================================================

def save_report_history(report):

    history = st.session_state.get(
        "jak_report_history",
        []
    )

    history.insert(
        0,
        {
            "name": report["name"],
            "created_at": report["created_at"],
            "rows": report["statistics"]["rows"],
            "columns": report["statistics"]["columns"],
            "quality_score": report["quality"]["quality_score"]
        }
    )

    st.session_state["jak_report_history"] = history[:50]


def render_report_history():

    render_section_heading(
        "Report History",
        "Review reports generated during this session."
    )

    history = st.session_state.get(
        "jak_report_history",
        []
    )

    if not history:

        st.info(
            "No reports have been generated yet."
        )

        return

    st.dataframe(
        pd.DataFrame(history),
        use_container_width=True,
        hide_index=True
    )

    if st.button(
        "Clear Report History",
        key="jak_clear_report_history"
    ):

        st.session_state["jak_report_history"] = []

        st.success(
            "Report history cleared."
        )

        st.rerun()


# =========================================================
# REPORT FILE NAMES
# =========================================================

def make_report_filename(dataset_name):

    safe_name = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        str(dataset_name)
    ).strip("_")

    if not safe_name:
        safe_name = "dataset"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"jak_{safe_name}_report_{timestamp}"


# =========================================================
# MAIN REPORT PAGE
# =========================================================

def render_reports_page():

    initialize_report_state()

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
        "Reports Centre",
        "Generate, customise and download professional analytical reports."
    )

    render_reports_hero()

    render_report_information()

    datasets = st.session_state.get(
        "jak_datasets",
        []
    )

    valid_datasets = {}

    for index, item in enumerate(datasets):

        if not isinstance(item, dict):
            continue

        data = item.get("data")

        if not isinstance(data, pd.DataFrame):
            continue

        original_name = str(
            item.get("name", f"Dataset {index + 1}")
        )

        display_name = original_name

        if display_name in valid_datasets:
            display_name = f"{original_name} ({index + 1})"

        valid_datasets[display_name] = data

    if not valid_datasets:

        st.warning(
            "Upload a valid dataset before generating reports."
        )

        show_footer()

        return

    selected_name = st.selectbox(
        "Select Dataset",
        list(valid_datasets.keys()),
        key="jak_report_dataset_selector"
    )

    data = valid_datasets[selected_name]

    if data.empty:

        st.warning(
            "The selected dataset is empty."
        )

        show_footer()

        return

    signature = (
        selected_name,
        len(data),
        len(data.columns),
        tuple(map(str, data.columns)),
        int(data.isna().sum().sum()),
        int(data.duplicated().sum())
    )

    if signature != st.session_state["jak_report_signature"]:

        st.session_state["jak_generated_report"] = None

        st.session_state["jak_report_signature"] = signature

    st.session_state["jak_report_selected_data"] = data

    report = build_dataset_report(
        data,
        selected_name
    )

    st.divider()

    tab1, tab2, tab3 = st.tabs([
        "Report Preview",
        "Generate Report",
        "Report History"
    ])

    # -----------------------------------------------------
    # REPORT PREVIEW
    # -----------------------------------------------------

    with tab1:

        render_report_overview(report)

        st.divider()

        render_report_quality(report)

        st.divider()

        render_report_statistics(
            report,
            data
        )

        st.divider()

        render_report_categorical(report)

    # -----------------------------------------------------
    # REPORT GENERATION
    # -----------------------------------------------------

    with tab2:

        render_section_heading(
            "Customise Your Report",
            "Select the sections to include in your PDF report."
        )

        selected_sections = st.multiselect(
            "Report Sections",
            [
                "Executive Summary",
                "Dataset Overview",
                "Data Quality",
                "Statistical Analysis",
                "Categorical Analysis"
            ],
            default=[
                "Executive Summary",
                "Dataset Overview",
                "Data Quality",
                "Statistical Analysis",
                "Categorical Analysis"
            ],
            key="jak_report_sections"
        )

        if st.button(
            "Generate Professional Report",
            type="primary",
            use_container_width=True,
            key="jak_generate_professional_report"
        ):

            if not selected_sections:

                st.error(
                    "Select at least one report section."
                )

            else:

                st.session_state["jak_generated_report"] = {
                    "report": report,
                    "sections": list(selected_sections)
                }

                save_report_history(report)

                st.success(
                    "Your report has been generated successfully."
                )

        generated = st.session_state.get(
            "jak_generated_report"
        )

        if generated:

            st.divider()

            st.subheader("Download Your Report")

            try:

                generated_report = generated["report"]

                filename = make_report_filename(
                    generated_report["name"]
                )

                pdf_data = generate_pdf_report(
                    generated_report,
                    generated["sections"]
                )

                csv_data = generate_csv_report(
                    generated_report
                )

                first, second = st.columns(2)

                with first:

                    st.download_button(
                        "Download PDF Report",
                        data=pdf_data,
                        file_name=f"{filename}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

                with second:

                    st.download_button(
                        "Download CSV Report",
                        data=csv_data,
                        file_name=f"{filename}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

            except Exception as error:

                st.error(
                    f"Could not generate report: {error}"
                )

    # -----------------------------------------------------
    # REPORT HISTORY
    # -----------------------------------------------------

    with tab3:

        render_report_history()

    st.divider()

    with st.container(border=True):

        st.subheader("Report Limitations")

        st.write(
            "This version generates reports from the selected "
            "dataset and its available statistical information."
        )

        st.write(
            "It does not yet combine every machine learning, "
            "forecasting or anomaly detection result into one "
            "unified report. Those integrations can be added "
            "as the remaining modules are connected."
        )

        st.caption(
            "Reports and report history are currently held "
            "in the active Streamlit session."
        )

    show_footer()


# =========================================================
# COMPATIBILITY ALIASES
# =========================================================

render_reports_page = render_reports_page
render_reports = render_reports_page
