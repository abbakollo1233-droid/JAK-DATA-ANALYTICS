"""
JAK Data Analytics
Advanced Data Transformation Studio

Features:
- Editable spreadsheet-style table
- Add and delete rows directly in the editor
- Edit cell values
- Add, rename and delete columns
- Create calculated columns
- Sort, filter and remove duplicates
- Handle missing values
- Text formatting and data type conversion
- Group and summarize data
- Undo to original dataset
- Preview, save as a new dataset and export CSV/Excel
"""

from datetime import datetime
import hashlib
import io

import numpy as np
import pandas as pd
import streamlit as st

from ...ui.layout import (
    render_topbar,
    render_page_intro,
    render_section_heading,
)
from ...ui.theme import show_footer


# ---------------------------------------------------------
# STYLING
# ---------------------------------------------------------

def inject_transformation_styles():
    st.markdown(
        """
        <style>
        .jak-transform-hero {
            padding: 24px 26px;
            border: 1px solid rgba(99, 102, 241, .18);
            border-radius: 18px;
            background: linear-gradient(120deg, #eff6ff 0%, #f0fdfa 100%);
            margin: 8px 0 20px 0;
        }
        .jak-transform-hero h3 { color: #102a43; margin: 0 0 7px 0; }
        .jak-transform-hero p { color: #486581; margin: 0; }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e5eaf1;
            border-radius: 14px;
            padding: 13px 15px;
        }
        div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {
            border: 1px solid #e5eaf1;
            border-radius: 12px;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_transformation_hero():
    st.markdown(
        """
        <div class="jak-transform-hero">
          <h3>Transformation Studio</h3>
          <p>Edit your data like a spreadsheet. Change individual cells,
          add or remove records and columns, clean values, calculate new
          fields, and save your transformed dataset.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# DATASET HELPERS
# ---------------------------------------------------------

def get_datasets():
    return st.session_state.get("jak_datasets", [])


def render_dataset_selector():
    datasets = get_datasets()
    valid = {
        str(item.get("name", f"Dataset {i + 1}")): item
        for i, item in enumerate(datasets)
        if isinstance(item, dict) and isinstance(item.get("data"), pd.DataFrame)
    }

    if not valid:
        st.warning("No datasets are available. Upload a CSV or Excel dataset first.")
        return None, None

    names = list(valid.keys())
    current = st.session_state.get("jak_transformation_dataset")
    index = names.index(current) if current in names else 0
    selected = st.selectbox(
        "Choose a dataset to transform",
        names,
        index=index,
        key="jak_transformation_dataset",
    )
    return valid[selected], selected


def dataset_fingerprint(data):
    try:
        raw = pd.util.hash_pandas_object(data, index=True).values.tobytes()
    except Exception:
        raw = data.astype("string").fillna("").to_csv(index=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def render_dataset_overview(data):
    numeric = len(data.select_dtypes(include="number").columns)
    text_cols = len(data.select_dtypes(include=["object", "string"]).columns)
    missing = int(data.isna().sum().sum())
    duplicates = int(data.duplicated().sum())

    cols = st.columns(5)
    cols[0].metric("Rows", f"{len(data):,}")
    cols[1].metric("Columns", f"{len(data.columns):,}")
    cols[2].metric("Numeric", f"{numeric:,}")
    cols[3].metric("Missing cells", f"{missing:,}")
    cols[4].metric("Duplicate rows", f"{duplicates:,}")


def render_editor(data, dataset_name):
    render_section_heading(
        "Spreadsheet editor",
        "Click any cell to edit it. Use the table controls to add or delete rows.",
    )

    st.caption(
        "Changes in this editor are a draft until you click Apply table edits. "
        "The original uploaded dataset remains unchanged."
    )

    edited = st.data_editor(
        data,
        key=f"jak_transform_editor_{hashlib.md5(dataset_name.encode()).hexdigest()}",
        use_container_width=True,
        height=480,
        hide_index=False,
        num_rows="dynamic",
        column_config={
            col: st.column_config.Column(
                help=f"Edit values in {col}",
            )
            for col in data.columns
        },
    )

    left, right = st.columns([1, 1])
    apply_clicked = left.button(
        "Apply table edits",
        type="primary",
        use_container_width=True,
        key="jak_apply_table_edits",
    )
    reset_clicked = right.button(
        "Reset editor to source",
        use_container_width=True,
        key="jak_reset_table_editor",
    )

    return edited, apply_clicked, reset_clicked


# ---------------------------------------------------------
# COLUMN OPERATIONS
# ---------------------------------------------------------

def render_column_tools(data):
    render_section_heading("Column tools", "Add, rename, duplicate or remove columns.")
    tab_add, tab_rename, tab_remove, tab_duplicate = st.tabs(
        ["Add column", "Rename", "Delete", "Duplicate"]
    )
    action = None

    with tab_add:
        mode = st.radio(
            "How do you want to create the column?",
            ["Blank column", "Constant value", "Calculated column"],
            horizontal=True,
            key="jak_col_add_mode",
        )
        new_name = st.text_input("New column name", key="jak_new_col_name")
        if mode == "Constant value":
            value = st.text_input("Value for every row", key="jak_new_col_value")
        elif mode == "Calculated column":
            numeric = data.select_dtypes(include="number").columns.tolist()
            if numeric:
                a, op, b = st.columns(3)
                first = a.selectbox("First numeric column", numeric, key="jak_calc_first")
                operator = op.selectbox("Operation", ["+", "-", "*", "/"], key="jak_calc_operator")
                second = b.selectbox("Second numeric column", numeric, key="jak_calc_second")
            else:
                st.info("A calculated column requires numeric columns.")
                first = operator = second = None
        if st.button("Create column", type="primary", key="jak_create_new_column"):
            name = new_name.strip()
            if not name:
                st.error("Enter a column name.")
            elif name in data.columns:
                st.error("That column already exists.")
            elif mode == "Calculated column" and first is None:
                st.error("No numeric columns are available.")
            else:
                action = {"type": "add_column", "name": name, "mode": mode}
                if mode == "Constant value":
                    action["value"] = value
                if mode == "Calculated column":
                    action.update({"first": first, "operator": operator, "second": second})

    with tab_rename:
        old = st.selectbox("Column to rename", data.columns.tolist(), key="jak_rename_old")
        new = st.text_input("New column name", key="jak_rename_new")
        if st.button("Rename column", key="jak_rename_apply"):
            name = new.strip()
            if not name:
                st.error("Enter the new name.")
            elif name != old and name in data.columns:
                st.error("A column with that name already exists.")
            elif name == old:
                st.info("The column already has that name.")
            else:
                action = {"type": "rename_column", "old": old, "new": name}

    with tab_remove:
        remove = st.multiselect(
            "Select one or more columns to delete",
            data.columns.tolist(),
            key="jak_columns_to_remove",
        )
        confirm = st.checkbox("I understand these columns will be removed from the draft.")
        if st.button("Delete selected columns", key="jak_delete_columns"):
            if not remove:
                st.warning("Select at least one column.")
            elif len(remove) >= len(data.columns):
                st.error("At least one column must remain.")
            elif not confirm:
                st.warning("Confirm the deletion first.")
            else:
                action = {"type": "remove_columns", "columns": remove}

    with tab_duplicate:
        source = st.selectbox("Column to duplicate", data.columns.tolist(), key="jak_dup_source")
        duplicate_name = st.text_input("Name for copied column", key="jak_dup_name")
        if st.button("Duplicate column", key="jak_duplicate_column"):
            name = duplicate_name.strip()
            if not name:
                st.error("Enter a name for the copied column.")
            elif name in data.columns:
                st.error("That column name already exists.")
            else:
                action = {"type": "duplicate_column", "source": source, "name": name}

    return action


# ---------------------------------------------------------
# DATA CLEANING AND TRANSFORMATIONS
# ---------------------------------------------------------

def render_cleaning_tools(data):
    render_section_heading("Data cleaning", "Remove duplicates and handle missing values.")
    tab_missing, tab_duplicates = st.tabs(["Missing values", "Duplicates"])
    action = None

    with tab_missing:
        missing_columns = data.columns[data.isna().any()].tolist()
        st.write(f"Missing cells: **{int(data.isna().sum().sum()):,}**")
        if missing_columns:
            column = st.selectbox("Column", ["All columns"] + missing_columns, key="jak_missing_col")
            method = st.selectbox(
                "Action",
                ["Drop rows with missing values", "Fill with a value", "Fill numeric with mean",
                 "Fill numeric with median", "Fill text with mode"],
                key="jak_missing_method",
            )
            fill_value = st.text_input("Replacement value (for Fill with a value)", key="jak_fill_value")
            if st.button("Apply missing-value action", key="jak_missing_apply"):
                action = {
                    "type": "missing",
                    "column": column,
                    "method": method,
                    "value": fill_value,
                }
        else:
            st.success("No missing values detected.")

    with tab_duplicates:
        count = int(data.duplicated().sum())
        st.write(f"Duplicate rows: **{count:,}**")
        keep = st.selectbox("Which duplicate record should be kept?", ["First", "Last", "None"])
        if st.button("Remove duplicate rows", key="jak_remove_duplicates"):
            action = {"type": "duplicates", "keep": {"First": "first", "Last": "last", "None": False}[keep]}

    return action


def render_sort_filter_tools(data):
    render_section_heading("Sort and filter", "Arrange records or keep only rows matching your conditions.")
    tab_sort, tab_filter, tab_sample = st.tabs(["Sort", "Filter", "Sample"])
    action = None

    with tab_sort:
        col = st.selectbox("Sort by", data.columns.tolist(), key="jak_sort_column")
        direction = st.radio("Direction", ["Ascending", "Descending"], horizontal=True, key="jak_sort_direction")
        nulls = st.selectbox("Missing values", ["Last", "First"], key="jak_sort_nulls")
        if st.button("Sort rows", key="jak_sort_apply"):
            action = {"type": "sort", "column": col, "ascending": direction == "Ascending",
                      "na_position": "last" if nulls == "Last" else "first"}

    with tab_filter:
        col = st.selectbox("Filter column", data.columns.tolist(), key="jak_filter_column")
        series = data[col]
        if pd.api.types.is_numeric_dtype(series):
            low = float(series.min()) if series.notna().any() else 0.0
            high = float(series.max()) if series.notna().any() else 0.0
            minimum, maximum = st.slider("Keep values between", min_value=low, max_value=high,
                                         value=(low, high), key="jak_numeric_filter")
            if st.button("Apply numeric filter", key="jak_filter_numeric_apply"):
                action = {"type": "numeric_filter", "column": col, "minimum": minimum, "maximum": maximum}
        else:
            values = sorted(series.dropna().astype(str).unique().tolist())
            selected = st.multiselect("Keep selected values", values, default=values, key="jak_text_filter_values")
            include_missing = st.checkbox("Include blank values", value=True, key="jak_filter_missing")
            if st.button("Apply value filter", key="jak_filter_text_apply"):
                action = {"type": "value_filter", "column": col, "values": selected,
                          "include_missing": include_missing}

    with tab_sample:
        amount = st.number_input("Number of rows to keep", min_value=1, max_value=max(1, len(data)),
                                 value=min(100, max(1, len(data))), key="jak_sample_amount")
        random_state = st.number_input("Random seed", min_value=0, value=42, key="jak_sample_seed")
        if st.button("Create random sample", key="jak_sample_apply"):
            action = {"type": "sample", "n": int(amount), "seed": int(random_state)}

    return action


def render_text_type_tools(data):
    render_section_heading("Text and data types", "Standardize text or convert columns to useful data types.")
    tab_text, tab_type = st.tabs(["Text formatting", "Convert data type"])
    action = None

    with tab_text:
        text_columns = data.select_dtypes(include=["object", "string"]).columns.tolist()
        if text_columns:
            col = st.selectbox("Text column", text_columns, key="jak_text_col")
            operation = st.selectbox(
                "Formatting",
                ["Uppercase", "Lowercase", "Title case", "Trim spaces", "Remove extra spaces"],
                key="jak_text_operation",
            )
            if st.button("Format text", key="jak_text_apply"):
                action = {"type": "text", "column": col, "operation": operation}
        else:
            st.info("No text columns are available.")

    with tab_type:
        col = st.selectbox("Column to convert", data.columns.tolist(), key="jak_dtype_col")
        dtype = st.selectbox("New type", ["Text", "Integer", "Decimal", "Date", "Boolean"],
                             key="jak_dtype_target")
        errors = st.selectbox("Invalid values", ["Convert to blank", "Stop and show error"],
                              key="jak_dtype_errors")
        if st.button("Convert data type", key="jak_dtype_apply"):
            action = {"type": "dtype", "column": col, "dtype": dtype,
                      "errors": "coerce" if errors == "Convert to blank" else "raise"}

    return action


def render_group_tools(data):
    render_section_heading("Group and summarize", "Create a summary table from your records.")
    numeric = data.select_dtypes(include="number").columns.tolist()
    if not numeric:
        st.info("Grouping requires at least one numeric column.")
        return None
    group_col = st.selectbox("Group records by", data.columns.tolist(), key="jak_group_column")
    value_col = st.selectbox("Value column", numeric, key="jak_group_value")
    operation = st.selectbox("Calculation", ["Sum", "Mean", "Median", "Minimum", "Maximum", "Count"],
                             key="jak_group_operation")
    if st.button("Create summary table", key="jak_group_apply"):
        return {"type": "group", "group_column": group_col, "value_column": value_col,
                "operation": operation}
    return None


# ---------------------------------------------------------
# APPLY ACTIONS
# ---------------------------------------------------------

def apply_action(data, action):
    result = data.copy()
    kind = action["type"]

    if kind == "add_column":
        if action["mode"] == "Blank column":
            result[action["name"]] = pd.NA
        elif action["mode"] == "Constant value":
            result[action["name"]] = action["value"]
        else:
            a = pd.to_numeric(result[action["first"]], errors="coerce")
            b = pd.to_numeric(result[action["second"]], errors="coerce")
            op = action["operator"]
            if op == "+": values = a + b
            elif op == "-": values = a - b
            elif op == "*": values = a * b
            else: values = a / b.replace(0, np.nan)
            result[action["name"]] = values

    elif kind == "rename_column":
        result = result.rename(columns={action["old"]: action["new"]})
    elif kind == "remove_columns":
        result = result.drop(columns=action["columns"])
    elif kind == "duplicate_column":
        result[action["name"]] = result[action["source"]].copy()
    elif kind == "sort":
        result = result.sort_values(by=action["column"], ascending=action["ascending"],
                                    na_position=action["na_position"], kind="stable").reset_index(drop=True)
    elif kind == "numeric_filter":
        values = pd.to_numeric(result[action["column"]], errors="coerce")
        result = result[values.between(action["minimum"], action["maximum"])].copy().reset_index(drop=True)
    elif kind == "value_filter":
        mask = result[action["column"]].astype("string").isin(action["values"])
        if action["include_missing"]:
            mask |= result[action["column"]].isna()
        result = result[mask].copy().reset_index(drop=True)
    elif kind == "sample":
        result = result.sample(n=min(action["n"], len(result)), random_state=action["seed"]).reset_index(drop=True)
    elif kind == "duplicates":
        result = result.drop_duplicates(keep=action["keep"]).reset_index(drop=True)
    elif kind == "missing":
        col = action["column"]
        subset = None if col == "All columns" else [col]
        method = action["method"]
        if method == "Drop rows with missing values":
            result = result.dropna(subset=subset).reset_index(drop=True)
        else:
            columns = result.columns if col == "All columns" else [col]
            for name in columns:
                if method == "Fill with a value":
                    result[name] = result[name].fillna(action["value"])
                elif method == "Fill numeric with mean" and pd.api.types.is_numeric_dtype(result[name]):
                    result[name] = result[name].fillna(result[name].mean())
                elif method == "Fill numeric with median" and pd.api.types.is_numeric_dtype(result[name]):
                    result[name] = result[name].fillna(result[name].median())
                elif method == "Fill text with mode":
                    modes = result[name].mode(dropna=True)
                    if not modes.empty:
                        result[name] = result[name].fillna(modes.iloc[0])
    elif kind == "text":
        col, op = action["column"], action["operation"]
        values = result[col].astype("string")
        if op == "Uppercase": result[col] = values.str.upper()
        elif op == "Lowercase": result[col] = values.str.lower()
        elif op == "Title case": result[col] = values.str.title()
        elif op == "Trim spaces": result[col] = values.str.strip()
        elif op == "Remove extra spaces":
            result[col] = values.str.replace(r"\s+", " ", regex=True).str.strip()
    elif kind == "dtype":
        col, dtype, errors = action["column"], action["dtype"], action["errors"]
        if dtype == "Text": result[col] = result[col].astype("string")
        elif dtype == "Integer": result[col] = pd.to_numeric(result[col], errors=errors).astype("Int64")
        elif dtype == "Decimal": result[col] = pd.to_numeric(result[col], errors=errors)
        elif dtype == "Date": result[col] = pd.to_datetime(result[col], errors=errors)
        elif dtype == "Boolean":
            mapping = {"true": True, "false": False, "yes": True, "no": False, "1": True, "0": False}
            converted = result[col].astype("string").str.lower().map(mapping)
            if errors == "raise" and (result[col].notna() & converted.isna()).any():
                raise ValueError("Some values cannot be converted to Boolean.")
            result[col] = converted.astype("boolean")
    elif kind == "group":
        functions = {"Sum": "sum", "Mean": "mean", "Median": "median",
                     "Minimum": "min", "Maximum": "max", "Count": "count"}
        result = (result.groupby(action["group_column"], dropna=False)[action["value_column"]]
                  .agg(functions[action["operation"]]).reset_index())
    else:
        raise ValueError("Unknown transformation.")

    return result


# ---------------------------------------------------------
# PREVIEW, SAVE AND EXPORT
# ---------------------------------------------------------

def render_transformation_preview(original, transformed):
    render_section_heading("Transformation preview", "Review the result before saving it.")
    cols = st.columns(4)
    cols[0].metric("Rows", f"{len(transformed):,}", delta=f"{len(transformed) - len(original):+,}")
    cols[1].metric("Columns", f"{len(transformed.columns):,}", delta=f"{len(transformed.columns) - len(original.columns):+,}")
    cols[2].metric("Missing cells", f"{int(transformed.isna().sum().sum()):,}")
    cols[3].metric("Duplicate rows", f"{int(transformed.duplicated().sum()):,}")
    st.dataframe(transformed.head(500), use_container_width=True, height=400)

    csv_bytes = transformed.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Download CSV", csv_bytes, "jak_transformed_dataset.csv",
                       "text/csv", use_container_width=True)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        transformed.to_excel(writer, index=False, sheet_name="Transformed Data")
    st.download_button(
        "Download Excel",
        buffer.getvalue(),
        "jak_transformed_dataset.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )


def save_transformed_dataset(data, original_name):
    datasets = st.session_state.setdefault("jak_datasets", [])
    next_id = max(
        [item.get("id", 0) for item in datasets if isinstance(item, dict)],
        default=0,
    ) + 1
    new_dataset = {
        "id": next_id,
        "name": f"{original_name}_Transformed",
        "data": data.copy(),
        "rows": len(data),
        "columns": len(data.columns),
        "fingerprint": dataset_fingerprint(data),
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    datasets.append(new_dataset)
    st.session_state.setdefault("jak_recent_activities", []).append({
        "title": "Dataset Transformed",
        "description": f"Saved a transformed copy of {original_name}.",
    })
    return new_dataset


# ---------------------------------------------------------
# MAIN PAGE
# ---------------------------------------------------------

def render_transformations_page():
    inject_transformation_styles()
    username = st.session_state.get("jak_user_name", "Guest")
    role = st.session_state.get("jak_user_role", "User")
    render_topbar(username=username, role=role)
    render_page_intro(
        "Data Transformations",
        "Edit, clean, reshape and prepare your datasets for analysis.",
    )
    render_transformation_hero()

    selected, dataset_name = render_dataset_selector()
    if selected is None:
        show_footer()
        return

    source = selected["data"].copy()
    if source.empty or len(source.columns) == 0:
        st.warning("The selected dataset has no rows or columns to edit.")
        show_footer()
        return

    render_dataset_overview(source)

    # A working copy is retained in the session while the user edits.
    work_key = "jak_transformation_working_data"
    name_key = "jak_transformation_working_name"
    if name_key not in st.session_state or st.session_state[name_key] != dataset_name:
        st.session_state[work_key] = source.copy()
        st.session_state[name_key] = dataset_name
        st.session_state.pop("jak_transformation_preview", None)

    working = st.session_state[work_key].copy()

    with st.expander("Edit the entire table", expanded=True):
        edited, apply_clicked, reset_clicked = render_editor(working, dataset_name)
        if apply_clicked:
            st.session_state[work_key] = edited.copy()
            st.session_state["jak_transformation_preview"] = edited.copy()
            st.success("Your cell and row edits have been applied to the working copy.")
            st.rerun()
        if reset_clicked:
            st.session_state[work_key] = source.copy()
            st.session_state.pop("jak_transformation_preview", None)
            st.success("The editor has been reset to the original uploaded dataset.")
            st.rerun()

    working = st.session_state[work_key].copy()
    st.divider()

    tabs = st.tabs([
        "Columns",
        "Clean data",
        "Sort & filter",
        "Text & types",
        "Group & summarize",
    ])

    actions = []
    with tabs[0]:
        actions.append(render_column_tools(working))
    with tabs[1]:
        actions.append(render_cleaning_tools(working))
    with tabs[2]:
        actions.append(render_sort_filter_tools(working))
    with tabs[3]:
        actions.append(render_text_type_tools(working))
    with tabs[4]:
        actions.append(render_group_tools(working))

    action = next((item for item in actions if item is not None), None)
    if action:
        try:
            updated = apply_action(working, action)
            st.session_state[work_key] = updated.copy()
            st.session_state["jak_transformation_preview"] = updated.copy()
            st.success("Transformation applied to your working copy.")
            st.rerun()
        except Exception as exc:
            st.error(f"Could not apply transformation: {exc}")

    current = st.session_state[work_key].copy()
    st.divider()
    render_transformation_preview(source, current)

    left, middle, right = st.columns(3)
    with left:
        if st.button("Save as new dataset", type="primary", use_container_width=True,
                     key="jak_save_transformation"):
            saved = save_transformed_dataset(current, dataset_name)
            st.session_state.pop(work_key, None)
            st.session_state.pop(name_key, None)
            st.success(f"{saved['name']} has been saved to your dataset library.")
            st.rerun()
    with middle:
        if st.button("Discard edits", use_container_width=True, key="jak_discard_transform"):
            st.session_state[work_key] = source.copy()
            st.session_state.pop("jak_transformation_preview", None)
            st.rerun()
    with right:
        st.caption("Your uploaded source dataset is not overwritten.")

    show_footer()


# Backward-compatible page function names.
render_transformations = render_transformations_page