
"""
JAK Data Analytics
Modern Responsive Dataset Upload Component

Features:
- Modern dataset upload interface
- CSV, Excel, JSON and Parquet support
- File validation
- File size validation
- Automatic dataset reading
- Dataset preview
- Responsive statistics
- Improved error handling

Compatible with Streamlit.
"""

import streamlit as st
import pandas as pd

from ...config.constants import (
    SUPPORTED_FILE_FORMATS,
    MAX_UPLOAD_SIZE_MB
)


# =====================================================
# FILE VALIDATION
# =====================================================

def validate_uploaded_file(uploaded_file):
    """Validate an uploaded dataset."""

    if uploaded_file is None:
        return False, "No file was selected."

    filename = uploaded_file.name.lower()

    if not any(
        filename.endswith(extension)
        for extension in SUPPORTED_FILE_FORMATS
    ):
        return False, "This file format is not supported."

    max_size = MAX_UPLOAD_SIZE_MB * 1024 * 1024

    if uploaded_file.size > max_size:
        return False, (
            f"File is too large. Maximum allowed size is "
            f"{MAX_UPLOAD_SIZE_MB} MB."
        )

    if uploaded_file.size == 0:
        return False, "The selected file is empty."

    return True, "File validation successful."


# =====================================================
# READ CSV FILE
# =====================================================

def read_csv_file(uploaded_file):
    """Read CSV files with common encoding support."""

    uploaded_file.seek(0)

    try:
        return pd.read_csv(
            uploaded_file,
            encoding="utf-8-sig"
        )

    except UnicodeDecodeError:

        uploaded_file.seek(0)

        return pd.read_csv(
            uploaded_file,
            encoding="latin-1"
        )


# =====================================================
# READ EXCEL FILE
# =====================================================

def read_excel_file(uploaded_file):
    """Read Excel workbooks."""

    uploaded_file.seek(0)

    return pd.read_excel(uploaded_file)


# =====================================================
# READ JSON FILE
# =====================================================

def read_json_file(uploaded_file):
    """Read JSON datasets."""

    uploaded_file.seek(0)

    return pd.read_json(uploaded_file)


# =====================================================
# READ PARQUET FILE
# =====================================================

def read_parquet_file(uploaded_file):
    """Read Parquet datasets."""

    uploaded_file.seek(0)

    return pd.read_parquet(uploaded_file)


# =====================================================
# DATASET READER
# =====================================================

def read_uploaded_dataset(uploaded_file):
    """Automatically detect and read uploaded datasets."""

    filename = uploaded_file.name.lower()

    try:

        if filename.endswith(".csv"):

            data = read_csv_file(uploaded_file)

        elif filename.endswith((".xlsx", ".xls")):

            data = read_excel_file(uploaded_file)

        elif filename.endswith(".json"):

            data = read_json_file(uploaded_file)

        elif filename.endswith(".parquet"):

            data = read_parquet_file(uploaded_file)

        else:

            raise ValueError(
                "Unsupported file format."
            )

        if data.empty:
            raise ValueError(
                "The uploaded dataset is empty."
            )

        return data

    except Exception as error:

        raise ValueError(
            f"Unable to read the uploaded dataset: {error}"
        ) from error


# =====================================================
# UPLOAD INFORMATION
# =====================================================

def render_upload_information():

    with st.container(border=True):

        st.markdown("### 📂 Upload your dataset")

        st.write(
            "Bring your data into JAK Data Analytics "
            "to clean, explore, visualize and analyse it."
        )

        formats = [
            extension.replace(".", "").upper()
            for extension in SUPPORTED_FILE_FORMATS
        ]

        st.caption(
            "Supported formats: "
            + " • ".join(formats)
        )

        st.caption(
            f"Maximum upload size: {MAX_UPLOAD_SIZE_MB} MB"
        )


# =====================================================
# DATASET STATISTICS
# =====================================================

def render_dataset_statistics(data):

    rows, columns = data.shape

    missing = int(
        data.isna().sum().sum()
    )

    duplicate = int(
        data.duplicated().sum()
    )

    stat_columns = st.columns(2)

    with stat_columns[0]:

        with st.container(border=True):

            st.caption("TOTAL ROWS")

            st.metric(
                "Rows",
                f"{rows:,}"
            )

    with stat_columns[1]:

        with st.container(border=True):

            st.caption("TOTAL COLUMNS")

            st.metric(
                "Columns",
                f"{columns:,}"
            )

    stat_columns = st.columns(2)

    with stat_columns[0]:

        with st.container(border=True):

            st.caption("MISSING VALUES")

            st.metric(
                "Missing",
                f"{missing:,}"
            )

    with stat_columns[1]:

        with st.container(border=True):

            st.caption("DUPLICATE ROWS")

            st.metric(
                "Duplicates",
                f"{duplicate:,}"
            )


# =====================================================
# DATASET PREVIEW
# =====================================================

def render_dataset_preview(data):

    st.markdown("### 👁️ Dataset Preview")

    st.caption(
        "Review the first 10 records in your dataset."
    )

    st.dataframe(
        data.head(10),
        use_container_width=True,
        hide_index=True
    )

    with st.expander("View column information"):

        column_information = pd.DataFrame({
            "Column": data.columns.astype(str),
            "Data Type": data.dtypes.astype(str).values,
            "Missing Values": data.isna().sum().values,
            "Unique Values": data.nunique().values
        })

        st.dataframe(
            column_information,
            use_container_width=True,
            hide_index=True
        )


# =====================================================
# DATASET UPLOAD FORM
# =====================================================

def render_upload_form():
    """
    Display the modern responsive dataset upload interface.

    Returns:
        pandas.DataFrame or None
    """

    st.subheader("Import Dataset")

    st.caption(
        "Upload a dataset to activate the JAK "
        "data analytics workspace."
    )

    render_upload_information()

    uploaded_file = st.file_uploader(
        "Select your dataset",
        type=[
            extension.replace(".", "")
            for extension in SUPPORTED_FILE_FORMATS
        ],
        accept_multiple_files=False,
        help=(
            f"Maximum file size: {MAX_UPLOAD_SIZE_MB} MB"
        ),
        key="jak_responsive_dataset_upload"
    )

    if uploaded_file is None:

        st.info(
            "Choose a CSV, Excel, JSON or Parquet file "
            "to get started."
        )

        return None

    # -------------------------------------------------
    # VALIDATION
    # -------------------------------------------------

    is_valid, message = validate_uploaded_file(
        uploaded_file
    )

    if not is_valid:

        st.error(message)

        return None

    st.success(
        f"Selected: {uploaded_file.name}"
    )

    file_size = (
        uploaded_file.size / (1024 * 1024)
    )

    st.caption(
        f"File size: {file_size:.2f} MB"
    )

    # -------------------------------------------------
    # READ DATASET
    # -------------------------------------------------

    try:

        with st.spinner(
            "Importing and analysing dataset structure..."
        ):

            data = read_uploaded_dataset(
                uploaded_file
            )

        st.success(
            "Your dataset has been imported successfully!"
        )

        # Dataset statistics
        render_dataset_statistics(data)

        # Dataset preview
        render_dataset_preview(data)

        st.divider()

        st.success(
            "Your dataset is ready for further analysis."
        )

        return data

    except Exception as error:

        st.error(
            f"Dataset import failed: {error}"
        )

        return None


# =====================================================
# END OF UPLOAD COMPONENT
# =====================================================
