"""
JAK Data Analytics
Data Transformation Module

Provides tools for transforming datasets.
Uses native Streamlit components only.
"""

import streamlit as st
import pandas as pd
import numpy as np
import hashlib

from datetime import datetime

from ...ui.layout import (
    render_topbar,
    render_page_intro,
    render_section_heading,
)

from ...ui.theme import show_footer


# ==========================================
# DATASET MANAGEMENT
# ==========================================

def get_datasets():
    """Retrieve available datasets."""

    return st.session_state.get("jak_datasets", [])


def render_transformation_hero():
    """Display the transformation page introduction."""

    with st.container(border=True):
        st.subheader("🔄 Data Transformation Studio")

        st.write(
            "Reshape, modify, calculate, combine and organize "
            "your datasets. Prepare your information for "
            "deeper analysis and visualization."
        )


def render_dataset_selector():
    """Allow users to select a dataset."""

    datasets = get_datasets()

    if not datasets:
        st.warning("No datasets available. Upload a dataset first.")
        return None, None

    dataset_options = {
        item["name"]: item
        for item in datasets
        if isinstance(item, dict)
        and isinstance(item.get("data"), pd.DataFrame)
    }

    if not dataset_options:
        st.warning("No valid datasets are available.")
        return None, None

    selected_name = st.selectbox(
        "Select Dataset",
        list(dataset_options.keys()),
        key="jak_transformation_dataset"
    )

    return dataset_options[selected_name], selected_name


# ==========================================
# DATASET OVERVIEW
# ==========================================

def render_dataset_overview(data):
    """Display dataset information."""

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Rows", f"{len(data):,}")

    col2.metric("Total Columns", f"{len(data.columns):,}")

    col3.metric(
        "Numeric Columns",
        len(data.select_dtypes(include="number").columns)
    )

    col4.metric(
        "Text Columns",
        len(data.select_dtypes(include=["object", "string"]).columns)
    )


# ==========================================
# CREATE NEW COLUMN
# ==========================================

def render_column_creation(data):
    """Configure calculated column creation."""

    render_section_heading(
        "Create New Column",
        "Create a calculated column using existing numeric columns."
    )

    numeric_columns = data.select_dtypes(
        include="number"
    ).columns.tolist()

    if not numeric_columns:
        st.info("This dataset has no numeric columns.")
        return None

    with st.form("jak_create_column_form"):

        new_column_name = st.text_input(
            "New Column Name",
            placeholder="Example: Total Amount"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            first_column = st.selectbox(
                "First Column",
                numeric_columns
            )

        with col2:
            operation = st.selectbox(
                "Operation",
                ["+", "-", "*", "/"]
            )

        with col3:
            second_column = st.selectbox(
                "Second Column",
                numeric_columns
            )

        submitted = st.form_submit_button(
            "Create Column",
            use_container_width=True
        )

    if submitted:

        name = new_column_name.strip()

        if not name:
            st.error("Enter a column name.")
            return None

        if name in data.columns:
            st.error("A column with this name already exists.")
            return None

        return {
            "action": "create_column",
            "name": name,
            "first": first_column,
            "second": second_column,
            "operation": operation
        }

    return None


# ==========================================
# COLUMN MANAGEMENT
# ==========================================

def render_column_management(data):
    """Configure column renaming and removal."""

    render_section_heading(
        "Column Management",
        "Rename or remove columns."
    )

    tab1, tab2 = st.tabs([
        "Rename Column",
        "Remove Column"
    ])

    action = None

    with tab1:

        with st.form("jak_rename_column_form"):

            old_name = st.selectbox(
                "Select Column",
                data.columns.tolist()
            )

            new_name = st.text_input(
                "New Column Name"
            )

            submitted = st.form_submit_button(
                "Rename Column",
                use_container_width=True
            )

        if submitted:

            new_name = new_name.strip()

            if not new_name:
                st.error("Enter the new column name.")

            elif (
                new_name in data.columns
                and new_name != old_name
            ):
                st.error("That column name already exists.")

            elif new_name == old_name:
                st.warning("The new name is the same as the current name.")

            else:
                action = {
                    "action": "rename_column",
                    "old": old_name,
                    "new": new_name
                }

    with tab2:

        selected_column = st.selectbox(
            "Column to Remove",
            data.columns.tolist(),
            key="jak_remove_column"
        )

        confirm = st.checkbox(
            "I confirm that I want to remove this column.",
            key="jak_confirm_remove_column"
        )

        if st.button(
            "Remove Column",
            key="jak_remove_column_button"
        ):

            if confirm:

                action = {
                    "action": "remove_column",
                    "column": selected_column
                }

            else:
                st.warning("Please confirm this operation.")

    return action


# ==========================================
# SORTING
# ==========================================

def render_sorting_options(data):
    """Configure dataset sorting."""

    render_section_heading(
        "Sort Dataset",
        "Arrange records in ascending or descending order."
    )

    with st.form("jak_sort_form"):

        column = st.selectbox(
            "Sort By Column",
            data.columns.tolist()
        )

        direction = st.selectbox(
            "Sort Direction",
            ["Ascending", "Descending"]
        )

        submitted = st.form_submit_button(
            "Sort Dataset",
            use_container_width=True
        )

    if submitted:

        return {
            "action": "sort",
            "column": column,
            "ascending": direction == "Ascending"
        }

    return None


# ==========================================
# GROUPING AND SUMMARIZATION
# ==========================================

def render_grouping_options(data):
    """Configure grouping and aggregation."""

    render_section_heading(
        "Group and Summarize",
        "Group records and calculate summary statistics."
    )

    numeric_columns = data.select_dtypes(
        include="number"
    ).columns.tolist()

    if not numeric_columns:
        st.info("Grouping requires at least one numeric column.")
        return None

    with st.form("jak_group_form"):

        group_column = st.selectbox(
            "Group By",
            data.columns.tolist()
        )

        value_column = st.selectbox(
            "Numeric Column",
            numeric_columns
        )

        aggregation = st.selectbox(
            "Calculation",
            [
                "Sum",
                "Mean",
                "Median",
                "Minimum",
                "Maximum",
                "Count"
            ]
        )

        submitted = st.form_submit_button(
            "Group Dataset",
            use_container_width=True
        )

    if submitted:

        return {
            "action": "group",
            "group_column": group_column,
            "value_column": value_column,
            "aggregation": aggregation
        }

    return None


# ==========================================
# TEXT TRANSFORMATION
# ==========================================

def render_text_transformation(data):
    """Configure text formatting."""

    render_section_heading(
        "Text Transformation",
        "Change the format of text columns."
    )

    text_columns = data.select_dtypes(
        include=["object", "string"]
    ).columns.tolist()

    if not text_columns:
        st.info("No text columns available.")
        return None

    with st.form("jak_text_form"):

        column = st.selectbox(
            "Select Text Column",
            text_columns
        )

        operation = st.selectbox(
            "Transformation",
            [
                "Uppercase",
                "Lowercase",
                "Title Case",
                "Remove Extra Spaces"
            ]
        )

        submitted = st.form_submit_button(
            "Transform Text",
            use_container_width=True
        )

    if submitted:

        return {
            "action": "text",
            "column": column,
            "operation": operation
        }

    return None


# ==========================================
# APPLY TRANSFORMATION
# ==========================================

def apply_transformation(data, action):
    """Apply the selected transformation."""

    transformed = data.copy()

    action_type = action["action"]

    if action_type == "create_column":

        first = pd.to_numeric(
            transformed[action["first"]],
            errors="coerce"
        )

        second = pd.to_numeric(
            transformed[action["second"]],
            errors="coerce"
        )

        operation = action["operation"]

        if operation == "+":
            result = first + second

        elif operation == "-":
            result = first - second

        elif operation == "*":
            result = first * second

        elif operation == "/":
            denominator = second.replace(0, np.nan)
            result = first / denominator

        else:
            raise ValueError("Unsupported calculation operation.")

        transformed[action["name"]] = result

    elif action_type == "rename_column":

        transformed = transformed.rename(
            columns={
                action["old"]: action["new"]
            }
        )

    elif action_type == "remove_column":

        transformed = transformed.drop(
            columns=[action["column"]]
        )

    elif action_type == "sort":

        transformed = transformed.sort_values(
            by=action["column"],
            ascending=action["ascending"],
            na_position="last"
        ).reset_index(drop=True)

    elif action_type == "group":

        aggregations = {
            "Sum": "sum",
            "Mean": "mean",
            "Median": "median",
            "Minimum": "min",
            "Maximum": "max",
            "Count": "count"
        }

        transformed = (
            transformed
            .groupby(
                action["group_column"],
                dropna=False
            )[action["value_column"]]
            .agg(aggregations[action["aggregation"]])
            .reset_index()
        )

    elif action_type == "text":

        column = action["column"]
        operation = action["operation"]

        text_values = transformed[column].astype("string")

        if operation == "Uppercase":

            transformed[column] = text_values.str.upper()

        elif operation == "Lowercase":

            transformed[column] = text_values.str.lower()

        elif operation == "Title Case":

            transformed[column] = text_values.str.title()

        elif operation == "Remove Extra Spaces":

            transformed[column] = (
                text_values
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
            )

    else:
        raise ValueError("Unknown transformation action.")

    return transformed


# ==========================================
# TRANSFORMATION PREVIEW
# ==========================================

def render_transformation_preview(original, transformed):
    """Display the transformed dataset."""

    render_section_heading(
        "Transformation Preview",
        "Review your transformed dataset."
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Original Rows", f"{len(original):,}")

    col2.metric("New Rows", f"{len(transformed):,}")

    col3.metric("Original Columns", f"{len(original.columns):,}")

    col4.metric("New Columns", f"{len(transformed.columns):,}")

    st.subheader("Transformed Data Preview")

    st.dataframe(
        transformed.head(100),
        use_container_width=True
    )

    csv_data = transformed.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "⬇️ Download Transformed CSV",
        data=csv_data,
        file_name="jak_transformed_dataset.csv",
        mime="text/csv",
        use_container_width=True
    )

    import io

    excel_buffer = io.BytesIO()

    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl"
    ) as writer:

        transformed.to_excel(
            writer,
            index=False,
            sheet_name="Transformed Data"
        )

    st.download_button(
        "⬇️ Download Transformed Excel",
        data=excel_buffer.getvalue(),
        file_name="jak_transformed_dataset.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )


# ==========================================
# SAVE TRANSFORMED DATASET
# ==========================================

def save_transformed_dataset(data, original_name):
    """Save transformed data as a separate dataset."""

    datasets = st.session_state.setdefault(
        "jak_datasets",
        []
    )

    content = pd.util.hash_pandas_object(
        data,
        index=True
    ).values.tobytes()

    fingerprint = hashlib.sha256(
        content
    ).hexdigest()

    new_dataset = {
        "id": max(
            [
                item.get("id", 0)
                for item in datasets
                if isinstance(item, dict)
            ],
            default=0
        ) + 1,

        "name": f"{original_name}_Transformed",

        "data": data.copy(),

        "rows": len(data),

        "columns": len(data.columns),

        "fingerprint": fingerprint,

        "uploaded_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        )
    }

    datasets.append(new_dataset)

    activities = st.session_state.setdefault(
        "jak_recent_activities",
        []
    )

    activities.append({
        "title": "Dataset Transformed",
        "description": (
            f"Created a transformed copy of {original_name}."
        )
    })

    return new_dataset


# ==========================================
# MAIN TRANSFORMATION PAGE
# ==========================================

def render_transformations_page():
    """Main data transformation page."""

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
        "Data Transformations",
        "Modify, reshape and prepare datasets for deeper analysis."
    )

    render_transformation_hero()

    selected_dataset, dataset_name = render_dataset_selector()

    if selected_dataset is None:
        show_footer()
        return

    original = selected_dataset["data"].copy()

    if original.empty:
        st.warning("The selected dataset is empty.")
        show_footer()
        return

    st.divider()

    render_dataset_overview(original)

    st.divider()

    st.info(
        "Each transformation starts from the original selected "
        "dataset. Your original dataset will not be overwritten."
    )

    tabs = st.tabs([
        "Create Column",
        "Manage Columns",
        "Sort",
        "Group",
        "Text"
    ])

    # Each tab has its own action variable.
    # This prevents an empty tab from overwriting a submitted action.

    actions = []

    with tabs[0]:
        actions.append(
            render_column_creation(original)
        )

    with tabs[1]:
        actions.append(
            render_column_management(original)
        )

    with tabs[2]:
        actions.append(
            render_sorting_options(original)
        )

    with tabs[3]:
        actions.append(
            render_grouping_options(original)
        )

    with tabs[4]:
        actions.append(
            render_text_transformation(original)
        )

    selected_action = next(
        (item for item in actions if item is not None),
        None
    )

    if selected_action:

        try:

            transformed = apply_transformation(
                original,
                selected_action
            )

            st.session_state["jak_transformation_preview"] = {
                "original_name": dataset_name,
                "data": transformed
            }

        except Exception as error:

            st.error(
                f"Transformation failed: {error}"
            )

    preview = st.session_state.get(
        "jak_transformation_preview"
    )

    if (
        preview is not None
        and preview["original_name"] == dataset_name
    ):

        st.divider()

        render_transformation_preview(
            original,
            preview["data"]
        )

        if st.button(
            "💾 Save as New Dataset",
            use_container_width=True,
            type="primary",
            key="jak_save_transformed_dataset"
        ):

            saved = save_transformed_dataset(
                preview["data"],
                dataset_name
            )

            st.session_state.pop(
                "jak_transformation_preview",
                None
            )

            st.success(
                f"{saved['name']} saved successfully!"
            )

            st.rerun()

    show_footer()


# ==========================================
# COMPATIBILITY ALIAS
# ==========================================

render_transformations = render_transformations_page