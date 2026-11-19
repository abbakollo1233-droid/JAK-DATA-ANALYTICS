"""
JAK Data Analytics
Data Cleaning Module

Provides tools for cleaning and preparing datasets.
Uses native Streamlit components only.
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

from ...ui.theme import show_footer


# ==========================================
# DATASET MANAGEMENT
# ==========================================

def get_datasets():
    """Retrieve available datasets."""
    return st.session_state.get("jak_datasets", [])


def render_cleaning_hero():
    """Display the cleaning page introduction."""

    with st.container(border=True):
        st.subheader("🧹 Intelligent Data Cleaning")

        st.write(
            "Improve your data quality by identifying missing "
            "values, removing duplicates, correcting data types "
            "and standardizing inconsistent records."
        )


def render_dataset_selector():
    """Allow users to select a dataset."""

    datasets = get_datasets()

    if not datasets:
        st.warning("No datasets available. Upload a dataset first.")
        return None, None

    options = {
        item["name"]: item
        for item in datasets
        if isinstance(item, dict)
        and isinstance(item.get("data"), pd.DataFrame)
    }

    if not options:
        st.warning("No valid datasets are available for cleaning.")
        return None, None

    selected_name = st.selectbox(
        "Select Dataset to Clean",
        list(options.keys()),
        key="jak_cleaning_dataset"
    )

    return options[selected_name], selected_name


# ==========================================
# CLEANING OVERVIEW
# ==========================================

def render_cleaning_overview(data):
    """Display dataset cleaning statistics."""

    missing = int(data.isna().sum().sum())
    duplicates = int(data.duplicated().sum())

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Rows", f"{len(data):,}")
    col2.metric("Total Columns", f"{len(data.columns):,}")
    col3.metric("Missing Values", f"{missing:,}")
    col4.metric("Duplicate Rows", f"{duplicates:,}")


# ==========================================
# MISSING VALUE OPTIONS
# ==========================================

def render_missing_value_options(data):
    """Configure missing value treatment."""

    render_section_heading(
        "Missing Values Treatment",
        "Choose how JAK should handle missing values."
    )

    missing_columns = [
        column
        for column in data.columns
        if data[column].isna().any()
    ]

    if not missing_columns:
        st.success("No missing values were detected.")
        return {}

    options = {}

    for column in missing_columns:

        with st.expander(
            f"{column} — {data[column].isna().sum()} missing values"
        ):

            method = st.selectbox(
                "Treatment method",
                [
                    "Keep unchanged",
                    "Remove rows with missing values",
                    "Fill with mean",
                    "Fill with median",
                    "Fill with mode",
                    "Fill with a custom value"
                ],
                key=f"jak_missing_method_{column}"
            )

            custom_value = None

            if method == "Fill with a custom value":

                custom_value = st.text_input(
                    "Custom replacement value",
                    key=f"jak_missing_custom_{column}"
                )

            options[column] = {
                "method": method,
                "custom_value": custom_value
            }

    return options


# ==========================================
# DUPLICATE OPTIONS
# ==========================================

def render_duplicate_options():
    """Configure duplicate removal."""

    render_section_heading(
        "Duplicate Records",
        "Choose how duplicate records should be handled."
    )

    return st.checkbox(
        "Remove duplicate rows",
        value=False,
        key="jak_remove_duplicates"
    )


# ==========================================
# TEXT CLEANING OPTIONS
# ==========================================

def render_text_cleaning_options(data):
    """Configure text standardization."""

    render_section_heading(
        "Text Standardization",
        "Clean unwanted spaces and inconsistent text formatting."
    )

    text_columns = data.select_dtypes(
        include=["object", "string"]
    ).columns.tolist()

    if not text_columns:
        st.info("No text columns were detected.")
        return {}

    options = {}

    for column in text_columns:

        with st.expander(f"Clean {column}"):

            trim_spaces = st.checkbox(
                "Remove leading and trailing spaces",
                value=True,
                key=f"jak_trim_{column}"
            )

            standardize_case = st.selectbox(
                "Text format",
                [
                    "Keep original case",
                    "Lowercase",
                    "UPPERCASE",
                    "Title Case"
                ],
                key=f"jak_case_{column}"
            )

            options[column] = {
                "trim": trim_spaces,
                "case": standardize_case
            }

    return options


# ==========================================
# DATA TYPE OPTIONS
# ==========================================

def render_data_type_options(data):
    """Allow users to select column data types."""

    render_section_heading(
        "Data Type Correction",
        "Convert columns into appropriate data types."
    )

    options = {}

    for column in data.columns:

        with st.expander(
            f"{column} — Current type: {data[column].dtype}"
        ):

            target_type = st.selectbox(
                "Convert to",
                [
                    "Keep original type",
                    "Text",
                    "Integer",
                    "Decimal",
                    "Date/Time"
                ],
                key=f"jak_datatype_{column}"
            )

            options[column] = target_type

    return options


# ==========================================
# APPLY MISSING VALUE CLEANING
# ==========================================

def apply_missing_value_cleaning(data, options):
    """Apply missing value treatment."""

    cleaned = data.copy()

    for column, settings in options.items():

        if column not in cleaned.columns:
            continue

        method = settings["method"]

        if method == "Keep unchanged":
            continue

        if method == "Remove rows with missing values":

            cleaned = cleaned.dropna(subset=[column])

        elif method == "Fill with mean":

            if pd.api.types.is_numeric_dtype(cleaned[column]):

                value = cleaned[column].mean()

                cleaned[column] = cleaned[column].fillna(value)

        elif method == "Fill with median":

            if pd.api.types.is_numeric_dtype(cleaned[column]):

                value = cleaned[column].median()

                cleaned[column] = cleaned[column].fillna(value)

        elif method == "Fill with mode":

            mode_values = cleaned[column].mode(dropna=True)

            if not mode_values.empty:

                cleaned[column] = cleaned[column].fillna(
                    mode_values.iloc[0]
                )

        elif method == "Fill with a custom value":

            value = settings.get("custom_value")

            if value is not None and value.strip():

                cleaned[column] = cleaned[column].fillna(value)

    return cleaned


# ==========================================
# APPLY DUPLICATE CLEANING
# ==========================================

def apply_duplicate_cleaning(data, remove_duplicates):
    """Remove duplicate rows when requested."""

    if remove_duplicates:
        return data.drop_duplicates().copy()

    return data.copy()


# ==========================================
# APPLY TEXT CLEANING
# ==========================================

def apply_text_cleaning(data, options):
    """Apply text formatting corrections."""

    cleaned = data.copy()

    for column, settings in options.items():

        if column not in cleaned.columns:
            continue

        if not (
            pd.api.types.is_object_dtype(cleaned[column])
            or pd.api.types.is_string_dtype(cleaned[column])
        ):
            continue

        if settings["trim"]:

            cleaned[column] = cleaned[column].map(
                lambda value: value.strip()
                if isinstance(value, str)
                else value
            )

        case_method = settings["case"]

        if case_method == "Lowercase":

            cleaned[column] = cleaned[column].map(
                lambda value: value.lower()
                if isinstance(value, str)
                else value
            )

        elif case_method == "UPPERCASE":

            cleaned[column] = cleaned[column].map(
                lambda value: value.upper()
                if isinstance(value, str)
                else value
            )

        elif case_method == "Title Case":

            cleaned[column] = cleaned[column].map(
                lambda value: value.title()
                if isinstance(value, str)
                else value
            )

    return cleaned


# ==========================================
# APPLY DATA TYPE CLEANING
# ==========================================

def apply_data_type_cleaning(data, options):
    """Convert columns into selected data types."""

    cleaned = data.copy()
    conversion_errors = []

    for column, target_type in options.items():

        if column not in cleaned.columns:
            continue

        if target_type == "Keep original type":
            continue

        try:

            if target_type == "Text":

                converted = cleaned[column].astype("string")

            elif target_type == "Integer":

                numeric = pd.to_numeric(
                    cleaned[column],
                    errors="raise"
                )

                converted = numeric.astype("Int64")

            elif target_type == "Decimal":

                converted = pd.to_numeric(
                    cleaned[column],
                    errors="raise"
                )

            elif target_type == "Date/Time":

                converted = pd.to_datetime(
                    cleaned[column],
                    errors="raise"
                )

            else:
                continue

            cleaned[column] = converted

        except (ValueError, TypeError, OverflowError) as error:

            conversion_errors.append(
                f"{column}: {error}"
            )

    return cleaned, conversion_errors


# ==========================================
# SAVE CLEANED DATASET
# ==========================================

def create_cleaned_dataset(data, original_name):
    """Save cleaned data as a separate dataset."""

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

    dataset = {
        "id": max(
            [
                item.get("id", 0)
                for item in datasets
                if isinstance(item, dict)
            ],
            default=0
        ) + 1,

        "name": f"{original_name}_Cleaned",

        "data": data.copy(),

        "rows": len(data),

        "columns": len(data.columns),

        "fingerprint": fingerprint,

        "uploaded_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        )
    }

    datasets.append(dataset)

    activities = st.session_state.setdefault(
        "jak_recent_activities",
        []
    )

    activities.append({
        "title": "Dataset Cleaned",
        "description": (
            f"Created a cleaned copy of {original_name}."
        )
    })

    return dataset


# ==========================================
# CLEANING RESULTS
# ==========================================

def render_cleaning_preview(original, cleaned):
    """Compare original and cleaned datasets."""

    render_section_heading(
        "Cleaning Results",
        "Compare your original and cleaned dataset."
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Original Rows",
        f"{len(original):,}"
    )

    col2.metric(
        "Cleaned Rows",
        f"{len(cleaned):,}",
        delta=len(cleaned) - len(original)
    )

    original_missing = int(original.isna().sum().sum())
    cleaned_missing = int(cleaned.isna().sum().sum())

    col3.metric(
        "Remaining Missing Values",
        f"{cleaned_missing:,}",
        delta=cleaned_missing - original_missing
    )

    st.subheader("Cleaned Data Preview")

    st.dataframe(
        cleaned.head(100),
        use_container_width=True
    )

    csv_data = cleaned.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "⬇️ Download Cleaned CSV",
        data=csv_data,
        file_name="jak_cleaned_dataset.csv",
        mime="text/csv",
        use_container_width=True
    )

    # Excel download
    import io

    excel_buffer = io.BytesIO()

    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl"
    ) as writer:

        cleaned.to_excel(
            writer,
            index=False,
            sheet_name="Cleaned Data"
        )

    st.download_button(
        "⬇️ Download Cleaned Excel",
        data=excel_buffer.getvalue(),
        file_name="jak_cleaned_dataset.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )


# ==========================================
# MAIN DATA CLEANING PAGE
# ==========================================

def render_data_cleaning_page():
    """Main data cleaning page."""

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
        "Data Cleaning",
        "Identify, correct and prepare your data for analysis."
    )

    render_cleaning_hero()

    selected_dataset, dataset_name = render_dataset_selector()

    if selected_dataset is None:
        show_footer()
        return

    original_data = selected_dataset["data"].copy()

    if original_data.empty:
        st.warning("The selected dataset is empty.")
        show_footer()
        return

    st.divider()

    render_cleaning_overview(original_data)

    st.divider()

    missing_options = render_missing_value_options(
        original_data
    )

    st.divider()

    remove_duplicates = render_duplicate_options()

    st.divider()

    text_options = render_text_cleaning_options(
        original_data
    )

    st.divider()

    datatype_options = render_data_type_options(
        original_data
    )

    st.divider()

    render_section_heading(
        "Apply Cleaning Operations",
        "Your original dataset will remain unchanged."
    )

    with st.container(border=True):
        st.info(
            "JAK will create a separate cleaned copy. "
            "Your original dataset will not be overwritten."
        )

        clean_clicked = st.button(
            "🧹 Clean Dataset",
            use_container_width=True,
            type="primary",
            key="jak_run_cleaning"
        )

    if clean_clicked:

        cleaned = original_data.copy()

        cleaned = apply_missing_value_cleaning(
            cleaned,
            missing_options
        )

        cleaned = apply_duplicate_cleaning(
            cleaned,
            remove_duplicates
        )

        cleaned = apply_text_cleaning(
            cleaned,
            text_options
        )

        cleaned, errors = apply_data_type_cleaning(
            cleaned,
            datatype_options
        )

        st.session_state["jak_cleaning_preview"] = {
            "original_name": dataset_name,
            "original": original_data,
            "cleaned": cleaned,
            "errors": errors
        }

    preview = st.session_state.get(
        "jak_cleaning_preview"
    )

    if (
        preview is not None
        and preview["original_name"] == dataset_name
    ):

        st.divider()

        render_cleaning_preview(
            preview["original"],
            preview["cleaned"]
        )

        if preview["errors"]:

            st.warning(
                "Some data type conversions could not be completed."
            )

            for error in preview["errors"]:
                st.write(f"• {error}")

        if st.button(
            "💾 Save Cleaned Dataset to My Datasets",
            use_container_width=True,
            type="primary",
            key="jak_save_cleaned_dataset"
        ):

            new_dataset = create_cleaned_dataset(
                preview["cleaned"],
                dataset_name
            )

            st.session_state.pop(
                "jak_cleaning_preview",
                None
            )

            st.success(
                f"Saved {new_dataset['name']} successfully!"
            )

            st.rerun()

    show_footer()


# ==========================================
# COMPATIBILITY ALIAS
# ==========================================

render_data_cleaning = render_data_cleaning_page