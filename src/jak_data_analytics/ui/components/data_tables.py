"""
JAK Data Analytics
Data Tables Component

Displays and explores datasets.
"""

import streamlit as st
import pandas as pd


# =====================================
# DATASET INFORMATION
# =====================================

def render_dataset_summary(data):

    """
    Display basic dataset information.
    """

    if data is None or data.empty:
        st.warning("No dataset available.")
        return

    rows, columns = data.shape

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Rows", f"{rows:,}")
    col2.metric("Total Columns", f"{columns:,}")
    col3.metric("Missing Values", f"{data.isna().sum().sum():,}")


# =====================================
# DATA TABLE
# =====================================

def render_data_table(
    data,
    height=450,
    use_container_width=True
):

    """
    Display a dataset in an interactive table.
    """

    if data is None or data.empty:
        st.info("No data available to display.")
        return

    st.dataframe(
        data,
        height=height,
        use_container_width=use_container_width,
        hide_index=True
    )


# =====================================
# DATA SEARCH
# =====================================

def search_dataset(data):

    """
    Search across dataset records.
    """

    if data is None or data.empty:
        return data

    search_text = st.text_input(
        "🔍 Search dataset",
        placeholder="Enter a value to search..."
    )

    if not search_text:
        return data

    try:
        mask = data.astype(str).apply(
            lambda column: column.str.contains(
                search_text,
                case=False,
                na=False,
                regex=False
            )
        ).any(axis=1)

        return data.loc[mask]

    except Exception as error:

        st.error(f"Search failed: {error}")

        return data


# =====================================
# COLUMN FILTER
# =====================================

def filter_dataset(data):

    """
    Filter a dataset by a selected column value.
    """

    if data is None or data.empty:
        return data

    selected_column = st.selectbox(
        "Select column to filter",
        options=["None"] + list(data.columns)
    )

    if selected_column == "None":
        return data

    values = data[selected_column].dropna().unique().tolist()

    if not values:
        st.info("This column has no values to filter.")
        return data

    selected_values = st.multiselect(
        f"Select {selected_column} values",
        options=values
    )

    if not selected_values:
        return data

    return data[
        data[selected_column].isin(selected_values)
    ]


# =====================================
# DATA DOWNLOAD
# =====================================

def download_dataset(data, filename="jak_dataset.csv"):

    """
    Provide a CSV download button.
    """

    if data is None or data.empty:
        return

    csv_data = data.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇️ Download CSV",
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        use_container_width=True
    )


# =====================================
# COMPLETE DATA EXPLORER
# =====================================

def render_data_explorer(data):

    """
    Display the complete dataset exploration interface.
    """

    if data is None or data.empty:

        st.info("Upload a dataset to begin exploring your data.")

        return

    st.subheader("Dataset Overview")

    render_dataset_summary(data)

    st.divider()

    st.subheader("Explore Your Data")

    search_column, filter_column = st.columns(2)

    with search_column:

        search_text = st.text_input(
            "Search records",
            placeholder="Enter a search term..."
        )

    with filter_column:

        selected_column = st.selectbox(
            "Filter by column",
            options=["None"] + list(data.columns)
        )

    filtered_data = data.copy()

    if search_text:

        mask = filtered_data.astype(str).apply(
            lambda column: column.str.contains(
                search_text,
                case=False,
                na=False,
                regex=False
            )
        ).any(axis=1)

        filtered_data = filtered_data.loc[mask]

    if selected_column != "None":

        values = filtered_data[selected_column].dropna().unique().tolist()

        selected_values = st.multiselect(
            "Select filter values",
            options=values
        )

        if selected_values:

            filtered_data = filtered_data[
                filtered_data[selected_column].isin(selected_values)
            ]

    st.caption(
        f"Showing {len(filtered_data):,} of {len(data):,} records"
    )

    render_data_table(filtered_data)

    download_dataset(
        filtered_data,
        filename="jak_filtered_dataset.csv"
    )