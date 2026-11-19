"""
JAK Data Analytics
Dataset Management Page

Modern dataset upload, management, search, filtering, preview and export.
"""

from io import BytesIO
import hashlib
from datetime import datetime

import pandas as pd
import streamlit as st

from ...ui.components.upload_forms import render_upload_form


# ============================================================
# DATASET STORAGE
# ============================================================

def initialize_datasets():
    """Initialize dataset and activity storage."""
    if "jak_datasets" not in st.session_state:
        st.session_state["jak_datasets"] = []

    if "jak_recent_activities" not in st.session_state:
        st.session_state["jak_recent_activities"] = []


def dataset_fingerprint(data):
    """Generate a stable fingerprint to prevent duplicate uploads."""
    content = pd.util.hash_pandas_object(
        data, index=True
    ).values.tobytes()

    # Include column names and dtypes so structurally different data
    # does not accidentally share a fingerprint.
    metadata = repr(
        (list(data.columns), [str(dtype) for dtype in data.dtypes])
    ).encode("utf-8")

    return hashlib.sha256(metadata + content).hexdigest()


def save_dataset(data):
    """Save an uploaded DataFrame once in the current Streamlit session."""
    if not isinstance(data, pd.DataFrame) or data.empty:
        if isinstance(data, pd.DataFrame) and data.empty:
            st.warning("The uploaded dataset is empty. Please choose a file containing data.")
        return False

    fingerprint = dataset_fingerprint(data)

    for item in st.session_state["jak_datasets"]:
        if item.get("fingerprint") == fingerprint:
            st.info("This dataset is already in your workspace.")
            return False

    next_id = max(
        (int(item.get("id", 0)) for item in st.session_state["jak_datasets"]),
        default=0,
    ) + 1

    dataset = {
        "id": next_id,
        "name": f"Dataset {next_id}",
        "data": data.copy(),
        "rows": int(len(data)),
        "columns": int(len(data.columns)),
        "fingerprint": fingerprint,
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    st.session_state["jak_datasets"].append(dataset)

    activities = st.session_state.get("jak_recent_activities", [])
    activities.append({
        "title": "Dataset Uploaded",
        "description": f"{dataset['name']} uploaded successfully.",
    })
    st.session_state["jak_recent_activities"] = activities[-20:]

    return True


def delete_dataset(dataset_id):
    """Delete a dataset by its unique session ID."""
    st.session_state["jak_datasets"] = [
        item for item in st.session_state["jak_datasets"]
        if item.get("id") != dataset_id
    ]


# ============================================================
# PAGE STYLING
# ============================================================

def render_dataset_styles():
    """Apply page-specific styles. No raw HTML is used for page content."""
    st.markdown(
        """
        <style>
        .jak-dataset-kicker {
            color: #BFDBFE;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 1.5px;
            text-transform: uppercase;
        }
        .jak-dataset-note {
            color: #64748B;
            font-size: 13px;
            line-height: 1.65;
        }
        .jak-dataset-section {
            margin-top: 8px;
        }
        [data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 16px;
        }
        [data-testid="stFileUploader"] {
            background: #F8FAFC;
            border: 1px dashed #93A4BD;
            border-radius: 14px;
            padding: 12px;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 15px;
        }
        @media (max-width: 640px) {
            [data-testid="stHorizontalBlock"] {
                flex-wrap: wrap;
                gap: .65rem;
            }
            [data-testid="stHorizontalBlock"] > [data-testid="column"] {
                min-width: 100% !important;
                width: 100% !important;
                flex: 1 1 100% !important;
            }
            [data-testid="stMetric"] {
                padding: 12px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# PAGE HEADER AND OVERVIEW
# ============================================================

def render_dataset_header():
    """Display a modern page introduction using native Streamlit widgets."""
    with st.container(border=True):
        st.caption("JAK DATA INTELLIGENCE PLATFORM")
        st.title("📊 Dataset Management")
        st.write(
            "Bring your data into one workspace. Upload files, inspect their "
            "contents, search records, filter columns and export the results."
        )


def render_dataset_metrics():
    """Display workspace dataset statistics."""
    datasets = st.session_state["jak_datasets"]

    total_datasets = len(datasets)
    total_rows = sum(int(item.get("rows", 0) or 0) for item in datasets)
    total_columns = sum(int(item.get("columns", 0) or 0) for item in datasets)
    total_missing = sum(
        int(item["data"].isna().sum().sum())
        for item in datasets
        if isinstance(item.get("data"), pd.DataFrame)
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📁 Datasets", f"{total_datasets:,}")
    col2.metric("📊 Total Rows", f"{total_rows:,}")
    col3.metric("📋 Total Columns", f"{total_columns:,}")
    col4.metric("⚠️ Missing Values", f"{total_missing:,}")


# ============================================================
# UPLOAD
# ============================================================

def render_upload_section():
    """Render the upload control and save returned DataFrame."""
    st.subheader("⬆️ Upload a Dataset")
    st.caption(
        "Choose a supported CSV or Excel file. The upload component validates "
        "and reads the file before it is added to this session."
    )

    uploaded_data = render_upload_form()

    if isinstance(uploaded_data, pd.DataFrame):
        if uploaded_data.empty:
            st.warning("The selected file contains no data rows.")
        else:
            saved = save_dataset(uploaded_data)
            if saved:
                st.success(
                    f"Dataset saved successfully — {len(uploaded_data):,} rows "
                    f"and {len(uploaded_data.columns):,} columns."
                )
                st.rerun()


# ============================================================
# DATASET LIBRARY
# ============================================================

def render_dataset_list():
    """Display uploaded datasets with safe delete actions."""
    st.subheader("🗂️ My Datasets")
    st.caption("Datasets currently available in this browser session.")

    datasets = st.session_state["jak_datasets"]

    if not datasets:
        st.info("Your dataset library is empty. Upload a file to get started.")
        return

    for dataset in datasets:
        with st.container(border=True):
            info_col, action_col = st.columns([5, 1])

            with info_col:
                st.markdown(f"**📄 {dataset.get('name', 'Unnamed dataset')}**")
                st.caption(
                    f"{int(dataset.get('rows', 0)):,} rows  ·  "
                    f"{int(dataset.get('columns', 0)):,} columns"
                )
                st.caption(f"Uploaded: {dataset.get('uploaded_at', 'Unknown')}")

            with action_col:
                if st.button(
                    "🗑️ Delete",
                    key=f"delete_dataset_{dataset['id']}",
                    use_container_width=True,
                ):
                    delete_dataset(dataset["id"])
                    st.success("Dataset deleted from this session.")
                    st.rerun()


# ============================================================
# DATASET EXPLORER
# ============================================================

def render_dataset_explorer():
    """Search, filter, preview and download a selected dataset."""
    st.subheader("🔎 Dataset Explorer")
    st.caption("Inspect your data and narrow it down before exporting.")

    datasets = st.session_state["jak_datasets"]

    if not datasets:
        st.info("Upload a dataset before using the explorer.")
        return

    # Use IDs as widget values so duplicate display names remain unambiguous.
    dataset_by_id = {item["id"]: item for item in datasets}
    selected_id = st.selectbox(
        "Select dataset",
        options=list(dataset_by_id.keys()),
        format_func=lambda value: dataset_by_id[value].get("name", f"Dataset {value}"),
        key="dataset_explorer_selection",
    )

    selected_dataset = dataset_by_id[selected_id]
    data = selected_dataset["data"]

    if not isinstance(data, pd.DataFrame):
        st.error("The selected dataset is not available as a table.")
        return

    missing_count = int(data.isna().sum().sum())
    duplicate_count = int(data.duplicated().sum())

    info1, info2, info3, info4 = st.columns(4)
    info1.metric("Rows", f"{len(data):,}")
    info2.metric("Columns", f"{len(data.columns):,}")
    info3.metric("Missing", f"{missing_count:,}")
    info4.metric("Duplicates", f"{duplicate_count:,}")

    st.markdown("#### Search records")
    search = st.text_input(
        "Search across all columns",
        placeholder="Type a word, number or value...",
        key=f"dataset_search_{selected_id}",
    )

    filtered_data = data.copy()

    if search.strip():
        search_mask = filtered_data.astype("string").apply(
            lambda column: column.str.contains(
                search.strip(),
                case=False,
                na=False,
                regex=False,
            )
        ).any(axis=1)
        filtered_data = filtered_data.loc[search_mask]

    st.markdown("#### Filter by column")
    filter_col1, filter_col2 = st.columns([2, 3])

    with filter_col1:
        filter_column = st.selectbox(
            "Column",
            options=["No column filter"] + list(data.columns),
            key=f"dataset_filter_column_{selected_id}",
        )

    if filter_column != "No column filter":
        values = (
            data[filter_column]
            .dropna()
            .astype(str)
            .drop_duplicates()
            .tolist()
        )

        with filter_col2:
            selected_values = st.multiselect(
                "Values to include",
                options=values,
                key=f"dataset_filter_values_{selected_id}_{filter_column}",
                placeholder="Choose one or more values",
            )

        if selected_values:
            filtered_data = filtered_data[
                filtered_data[filter_column].astype(str).isin(selected_values)
            ]
    else:
        with filter_col2:
            st.caption("Choose a column to filter the records.")

    st.markdown("#### Data preview")
    st.caption(
        f"Showing {len(filtered_data):,} of {len(data):,} rows."
    )
    st.dataframe(
        filtered_data,
        use_container_width=True,
        height=420,
        hide_index=True,
    )

    st.markdown("#### Export filtered data")
    csv_bytes = filtered_data.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="⬇️ Download filtered data (CSV)",
        data=csv_bytes,
        file_name=f"{selected_dataset.get('name', 'dataset').replace(' ', '_')}_filtered.csv",
        mime="text/csv",
        use_container_width=True,
        key=f"download_dataset_{selected_id}",
    )


# ============================================================
# MAIN PAGE
# ============================================================

def render_datasets_page():
    """Main dataset management page."""
    initialize_datasets()
    render_dataset_styles()

    username = st.session_state.get("jak_user_name", "Guest")
    role = st.session_state.get("jak_user_role", "User")

    # Native Streamlit components avoid showing literal HTML tags.
    st.caption(f"Signed in as {username} · {role}")
    render_dataset_header()
    render_dataset_metrics()

    st.divider()

    upload_tab, library_tab, explorer_tab = st.tabs(
        ["⬆️ Upload Dataset", "🗂️ My Datasets", "🔎 Explore Data"]
    )

    with upload_tab:
        render_upload_section()

    with library_tab:
        render_dataset_list()

    with explorer_tab:
        render_dataset_explorer()

    st.divider()
    st.caption("© 2026 JAK Data Analytics · Your data workspace")


# Backwards-compatible page function name.
render_user_datasets = render_datasets_page