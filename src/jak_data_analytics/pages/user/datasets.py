"""
JAK Data Analytics
Dataset Management Page

Allows users to upload, explore, search and manage datasets.
"""

import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime

from ...ui.layout import (
    render_topbar,
    render_page_intro,
    render_section_heading,
)

from ...ui.components.upload_forms import render_upload_form
from ...ui.theme import show_footer


def initialize_datasets():
    """Initialize dataset storage."""

    if "jak_datasets" not in st.session_state:
        st.session_state["jak_datasets"] = []


def dataset_fingerprint(data):
    """Generate a fingerprint to prevent duplicate uploads."""

    content = pd.util.hash_pandas_object(
        data,
        index=True
    ).values.tobytes()

    return hashlib.sha256(content).hexdigest()


def save_dataset(data):
    """Save an uploaded dataset to the current session."""

    if data is None or data.empty:
        return

    fingerprint = dataset_fingerprint(data)

    existing = [
        item for item in st.session_state["jak_datasets"]
        if item["fingerprint"] == fingerprint
    ]

    if existing:
        return

    dataset = {
        "id": len(st.session_state["jak_datasets"]) + 1,
        "name": f"Dataset {len(st.session_state['jak_datasets']) + 1}",
        "data": data.copy(),
        "rows": len(data),
        "columns": len(data.columns),
        "fingerprint": fingerprint,
        "uploaded_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        ),
    }

    st.session_state["jak_datasets"].append(dataset)

    st.session_state["jak_recent_activities"] = (
        st.session_state.get("jak_recent_activities", []) +
        [{
            "title": "Dataset Uploaded",
            "description": (
                f"{dataset['name']} uploaded successfully."
            )
        }]
    )


def render_dataset_header():
    """Display dataset page introduction."""

    st.markdown(
        """
        <div style="
            background:linear-gradient(120deg,#101828,#1D4ED8);
            padding:30px;
            border-radius:18px;
            margin-bottom:25px;
            color:white;
        ">
            <h2 style="color:white;">
                Your Data Workspace
            </h2>

            <p style="color:#DCE7FF;">
                Upload, organize, explore and prepare your
                datasets for powerful analytics.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_dataset_metrics():
    """Display dataset statistics."""

    datasets = st.session_state["jak_datasets"]

    total_datasets = len(datasets)

    total_rows = sum(
        item["rows"] for item in datasets
    )

    total_columns = sum(
        item["columns"] for item in datasets
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Datasets",
        total_datasets
    )

    col2.metric(
        "Total Rows",
        f"{total_rows:,}"
    )

    col3.metric(
        "Total Columns",
        f"{total_columns:,}"
    )


def render_upload_section():
    """Display the dataset upload component."""

    render_section_heading(
        "Upload Dataset",
        "Import your data into JAK Data Analytics."
    )

    uploaded_data = render_upload_form()

    if uploaded_data is not None:
        save_dataset(uploaded_data)


def render_dataset_list():
    """Display all uploaded datasets."""

    render_section_heading(
        "My Datasets",
        "View and manage your uploaded datasets."
    )

    datasets = st.session_state["jak_datasets"]

    if not datasets:
        st.info(
            "No datasets available yet. "
            "Upload your first dataset to get started."
        )
        return

    for dataset in datasets:

        with st.container(border=True):

            col1, col2 = st.columns([4, 1])

            with col1:
                st.subheader(f"📁 {dataset['name']}")

                st.caption(
                    f"{dataset['rows']:,} rows | "
                    f"{dataset['columns']:,} columns"
                )

                st.caption(
                    f"Uploaded: {dataset['uploaded_at']}"
                )

            with col2:
                if st.button(
                    "Delete",
                    key=f"delete_dataset_{dataset['id']}"
                ):
                    st.session_state["jak_datasets"] = [
                        item for item in datasets
                        if item["id"] != dataset["id"]
                    ]

                    st.rerun()


def render_dataset_explorer():
    """Allow users to explore their selected dataset."""

    render_section_heading(
        "Dataset Explorer",
        "Search, filter, inspect and download your data."
    )

    datasets = st.session_state["jak_datasets"]

    if not datasets:
        st.info("Upload a dataset before using the explorer.")
        return

    dataset_options = {
        item["name"]: item["id"]
        for item in datasets
    }

    selected_name = st.selectbox(
        "Select Dataset",
        list(dataset_options.keys())
    )

    selected_id = dataset_options[selected_name]

    selected_dataset = next(
        item for item in datasets
        if item["id"] == selected_id
    )

    data = selected_dataset["data"]

    st.markdown("### Dataset Information")

    col1, col2, col3 = st.columns(3)

    col1.metric("Rows", f"{len(data):,}")
    col2.metric("Columns", len(data.columns))
    col3.metric("Missing Values", f"{data.isna().sum().sum():,}")

    st.markdown("### Search Dataset")

    search = st.text_input(
        "Search across all columns",
        placeholder="Enter a value to search..."
    )

    filtered_data = data.copy()

    if search.strip():

        mask = filtered_data.astype(
            str
        ).apply(
            lambda column: column.str.contains(
                search,
                case=False,
                na=False,
                regex=False
            )
        ).any(axis=1)

        filtered_data = filtered_data[mask]

    st.markdown("### Filter by Column")

    filter_column = st.selectbox(
        "Choose a column",
        ["None"] + list(data.columns)
    )

    if filter_column != "None":

        unique_values = (
            data[filter_column]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        if unique_values:

            selected_values = st.multiselect(
                "Select values",
                unique_values
            )

            if selected_values:

                filtered_data = filtered_data[
                    filtered_data[filter_column]
                    .astype(str)
                    .isin(selected_values)
                ]

    st.markdown("### Data Preview")

    st.caption(
        f"Showing {len(filtered_data):,} matching rows."
    )

    st.dataframe(
        filtered_data,
        use_container_width=True,
        height=400
    )

    st.markdown("### Download Dataset")

    csv_data = filtered_data.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="⬇️ Download as CSV",
        data=csv_data,
        file_name=f"{selected_name.replace(' ', '_')}.csv",
        mime="text/csv",
        use_container_width=True
    )


def render_datasets_page():
    """Main dataset management page."""

    initialize_datasets()

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
        "Dataset Management",
        "Import, organize and explore your data."
    )

    render_dataset_header()

    render_dataset_metrics()

    st.divider()

    render_upload_section()

    st.divider()

    render_dataset_list()

    st.divider()

    render_dataset_explorer()

    show_footer()


render_user_datasets = render_datasets_page