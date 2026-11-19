"""
JAK Data Analytics
Dataset Upload Component

Handles dataset uploads, validation and file reading.
"""

import streamlit as st
import pandas as pd

from ...config.constants import (
    SUPPORTED_FILE_FORMATS,
    MAX_UPLOAD_SIZE_MB
)


# =====================================
# FILE VALIDATION
# =====================================

def validate_uploaded_file(uploaded_file):
    """
    Validate an uploaded dataset.
    """

    if uploaded_file is None:
        return False, "No file was selected."

    filename = uploaded_file.name.lower()

    # Check file extension
    if not any(
        filename.endswith(extension)
        for extension in SUPPORTED_FILE_FORMATS
    ):
        return False, "This file format is not supported."

    # Check file size
    max_size = MAX_UPLOAD_SIZE_MB * 1024 * 1024

    if uploaded_file.size > max_size:
        return False, (
            f"File is too large. Maximum allowed size is "
            f"{MAX_UPLOAD_SIZE_MB} MB."
        )

    return True, "File validation successful."


# =====================================
# READ CSV FILE
# =====================================

def read_csv_file(uploaded_file):
    """
    Read CSV files with common encoding support.
    """

    try:
        uploaded_file.seek(0)

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


# =====================================
# READ EXCEL FILE
# =====================================

def read_excel_file(uploaded_file):
    """
    Read Excel workbooks.
    """

    uploaded_file.seek(0)

    return pd.read_excel(uploaded_file)


# =====================================
# READ JSON FILE
# =====================================

def read_json_file(uploaded_file):
    """
    Read JSON datasets.
    """

    uploaded_file.seek(0)

    return pd.read_json(uploaded_file)


# =====================================
# READ PARQUET FILE
# =====================================

def read_parquet_file(uploaded_file):
    """
    Read Parquet datasets.
    """

    uploaded_file.seek(0)

    return pd.read_parquet(uploaded_file)


# =====================================
# DATASET READER
# =====================================

def read_uploaded_dataset(uploaded_file):
    """
    Detect the uploaded file format and read it.
    """

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

            raise ValueError("Unsupported file format.")

        if data.empty:
            raise ValueError("The uploaded dataset is empty.")

        return data

    except Exception as error:

        raise ValueError(
            f"Unable to read the uploaded dataset: {error}"
        ) from error


# =====================================
# DATASET UPLOAD FORM
# =====================================

def render_upload_form():

    """
    Display the dataset upload interface.

    Returns:
        pandas.DataFrame or None
    """

    st.subheader("Upload Your Dataset")

    st.write(
        "Select a dataset from your computer "
        "to begin analysing it with JAK."
    )

    uploaded_file = st.file_uploader(
        "Choose a dataset",
        type=[
            extension.replace(".", "")
            for extension in SUPPORTED_FILE_FORMATS
        ],
        accept_multiple_files=False,
        help=(
            f"Maximum file size: {MAX_UPLOAD_SIZE_MB} MB"
        )
    )

    if uploaded_file is None:

        st.info(
            "Supported formats: CSV, Excel, JSON and Parquet."
        )

        return None

    # Validate uploaded file
    is_valid, message = validate_uploaded_file(
        uploaded_file
    )

    if not is_valid:

        st.error(message)

        return None

    st.success(
        f"File selected: {uploaded_file.name}"
    )

    st.caption(
        f"File size: {uploaded_file.size / (1024 * 1024):.2f} MB"
    )

    # Read dataset
    try:

        with st.spinner("Reading your dataset..."):

            data = read_uploaded_dataset(uploaded_file)

        st.success("Dataset loaded successfully!")

        st.markdown("### Dataset Preview")

        st.dataframe(
            data.head(10),
            use_container_width=True,
            hide_index=True
        )

        st.info(
            f"Dataset contains {data.shape[0]:,} rows "
            f"and {data.shape[1]:,} columns."
        )

        return data

    except Exception as error:

        st.error(str(error))

        return None