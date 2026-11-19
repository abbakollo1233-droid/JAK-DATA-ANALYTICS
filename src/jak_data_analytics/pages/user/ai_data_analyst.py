"""
JAK Data Analytics
AI Data Analyst

Features:
- Natural-language dataset questions
- Automatic question interpretation
- Dataset summaries
- Numerical analysis
- Categorical analysis
- Missing-value analysis
- Duplicate detection
- Correlation analysis
- Group comparisons
- Top and bottom records
- Automatic chart generation
- Analysis history
- Downloadable analysis results

Current version:
Uses a transparent Python-based analytical engine.

Future integration:
An actual AI language model can be connected
through the service layer.
"""

import re

import streamlit as st
import pandas as pd
import plotly.express as px

from ...ui.layout import (
    render_topbar,
    render_page_intro,
    render_section_heading,
    render_empty_state,
)

from ...ui.theme import show_footer


# =========================================================
# INITIALIZATION
# =========================================================

def initialize_ai_state():
    """Initialize AI analyst session-state variables."""

    defaults = {
        "jak_ai_history": [],
        "jak_ai_current_result": None,
        "jak_ai_question": "",
        "jak_ai_selected_dataset_name": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# =========================================================
# DATASET UTILITIES
# =========================================================

def get_datasets():
    """Return valid datasets from the application session."""

    datasets = st.session_state.get("jak_datasets", [])

    if not isinstance(datasets, list):
        return []

    valid_datasets = []

    for item in datasets:
        if (
            isinstance(item, dict)
            and isinstance(item.get("data"), pd.DataFrame)
        ):
            valid_datasets.append(item)

    return valid_datasets


def get_numeric_columns(data):
    """Return numerical columns."""

    return data.select_dtypes(
        include="number"
    ).columns.tolist()


def get_categorical_columns(data):
    """Return categorical columns."""

    return data.select_dtypes(
        include=["object", "string", "category", "bool"]
    ).columns.tolist()


def clean_question(question):
    """Normalize a natural-language question."""

    return re.sub(
        r"\s+",
        " ",
        str(question).lower().strip()
    )


def find_column(question, columns):
    """Find the longest matching column name in a question."""

    normalized_question = clean_question(question)

    matches = []

    for column in columns:

        column_name = str(column).lower().strip()

        if not column_name:
            continue

        pattern = (
            r"(?<!\w)"
            + re.escape(column_name)
            + r"(?!\w)"
        )

        if re.search(pattern, normalized_question):
            matches.append(column)

    if not matches:
        return None

    return max(
        matches,
        key=lambda item: len(str(item))
    )


def extract_number(question, default=10):
    """Extract a requested record count from a question."""

    match = re.search(
        r"\b(?:top|bottom|first|last)\s+(\d+)\b",
        clean_question(question)
    )

    if match:
        return max(
            1,
            min(int(match.group(1)), 100)
        )

    return default


# =========================================================
# QUESTION INTERPRETATION
# =========================================================

def detect_analysis_intent(question):
    """Identify the likely analytical task."""

    question = clean_question(question)

    if any(word in question for word in [
        "missing",
        "null",
        "empty values",
        "incomplete",
        "blank values"
    ]):
        return "missing"

    if any(word in question for word in [
        "duplicate",
        "duplicated",
        "repeated rows"
    ]):
        return "duplicates"

    if any(word in question for word in [
        "correlation",
        "correlated",
        "relationship between",
        "related to"
    ]):
        return "correlation"

    if any(word in question for word in [
        "summary",
        "summarize",
        "describe",
        "overview",
        "tell me about",
        "dataset information"
    ]):
        return "summary"

    # Check ranking before numerical analysis.
    if any(word in question for word in [
        "top",
        "bottom",
        "highest performing",
        "lowest performing",
        "most",
        "least",
        "best",
        "worst"
    ]):
        return "ranking"

    if any(word in question for word in [
        "compare",
        "comparison",
        "by department",
        "by category",
        "by region",
        "group",
        "grouped"
    ]):
        return "group"

    if any(word in question for word in [
        "unique",
        "distinct",
        "different values",
        "categories"
    ]):
        return "unique"

    if any(word in question for word in [
        "average",
        "mean",
        "median",
        "maximum",
        "minimum",
        "highest",
        "lowest",
        "total",
        "sum",
        "count",
        "standard deviation"
    ]):
        return "numeric"

    return "unknown"


# =========================================================
# DATASET SUMMARY
# =========================================================

def build_dataset_summary(data):

    numeric_columns = get_numeric_columns(data)
    categorical_columns = get_categorical_columns(data)

    missing_cells = int(
        data.isna().sum().sum()
    )

    duplicate_rows = int(
        data.duplicated().sum()
    )

    return {
        "rows": len(data),
        "columns": len(data.columns),
        "numeric_columns": len(numeric_columns),
        "categorical_columns": len(categorical_columns),
        "missing_cells": missing_cells,
        "duplicate_rows": duplicate_rows,
        "memory_mb": round(
            data.memory_usage(deep=True).sum() / (1024 ** 2),
            2
        )
    }


def analyze_summary(data):

    summary = build_dataset_summary(data)

    answer = (
        f"Your dataset contains {summary['rows']:,} rows "
        f"and {summary['columns']:,} columns. "
        f"It has {summary['numeric_columns']} numerical columns "
        f"and {summary['categorical_columns']} categorical columns. "
        f"There are {summary['missing_cells']:,} missing cells "
        f"and {summary['duplicate_rows']:,} duplicate rows."
    )

    table = pd.DataFrame({
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
            summary["rows"],
            summary["columns"],
            summary["numeric_columns"],
            summary["categorical_columns"],
            summary["missing_cells"],
            summary["duplicate_rows"],
            summary["memory_mb"]
        ]
    })

    return {
        "answer": answer,
        "table": table,
        "chart": None
    }


# =========================================================
# MISSING VALUE ANALYSIS
# =========================================================

def analyze_missing_values(data):

    missing = data.isna().sum()

    result = pd.DataFrame({
        "Column": missing.index.astype(str),
        "Missing Values": missing.values,
        "Missing Percentage": (
            missing.values / max(len(data), 1)
        ) * 100
    })

    result = result.sort_values(
        "Missing Values",
        ascending=False
    )

    total_missing = int(missing.sum())
    affected_columns = int((missing > 0).sum())

    if total_missing == 0:
        answer = (
            "Your dataset does not contain any missing values."
        )
    else:
        answer = (
            f"Your dataset contains {total_missing:,} missing cells "
            f"across {affected_columns} columns."
        )

    chart_data = result[
        result["Missing Values"] > 0
    ]

    chart = None

    if not chart_data.empty:
        chart = px.bar(
            chart_data,
            x="Column",
            y="Missing Values",
            title="Missing Values by Column"
        )

    return {
        "answer": answer,
        "table": result,
        "chart": chart
    }


# =========================================================
# DUPLICATE ANALYSIS
# =========================================================

def analyze_duplicates(data):

    duplicate_count = int(
        data.duplicated().sum()
    )

    percentage = (
        duplicate_count / max(len(data), 1)
    ) * 100

    if duplicate_count == 0:
        answer = (
            "No duplicate rows were detected in your dataset."
        )
    else:
        answer = (
            f"Your dataset contains {duplicate_count:,} duplicate rows, "
            f"representing {percentage:.2f}% of all records."
        )

    duplicate_preview = data[
        data.duplicated(keep=False)
    ].head(100)

    return {
        "answer": answer,
        "table": duplicate_preview,
        "chart": None
    }


# =========================================================
# NUMERICAL ANALYSIS
# =========================================================

def analyze_numeric(data, question):

    numeric_columns = get_numeric_columns(data)

    if not numeric_columns:
        return {
            "answer": "No numerical columns were found.",
            "table": None,
            "chart": None
        }

    column = find_column(
        question,
        numeric_columns
    )

    if column is None:

        if len(numeric_columns) == 1:
            column = numeric_columns[0]

        else:
            return {
                "answer": (
                    "I could not identify the numerical column. "
                    "Please include its exact column name in your question."
                ),
                "table": None,
                "chart": None
            }

    values = pd.to_numeric(
        data[column],
        errors="coerce"
    ).dropna()

    if values.empty:
        return {
            "answer": (
                f"The column '{column}' has no valid numerical values."
            ),
            "table": None,
            "chart": None
        }

    question_lower = clean_question(question)

    if "average" in question_lower or "mean" in question_lower:
        metric = values.mean()
        label = "Average"

    elif "median" in question_lower:
        metric = values.median()
        label = "Median"

    elif "maximum" in question_lower or "highest" in question_lower:
        metric = values.max()
        label = "Maximum"

    elif "minimum" in question_lower or "lowest" in question_lower:
        metric = values.min()
        label = "Minimum"

    elif "standard deviation" in question_lower:
        metric = values.std()
        label = "Standard Deviation"

    elif "count" in question_lower:
        metric = values.count()
        label = "Count"

    else:
        metric = values.sum()
        label = "Total"

    statistics = pd.DataFrame({
        "Statistic": [
            "Count",
            "Mean",
            "Median",
            "Minimum",
            "Maximum",
            "Standard Deviation",
            "Total"
        ],
        "Value": [
            values.count(),
            values.mean(),
            values.median(),
            values.min(),
            values.max(),
            values.std(),
            values.sum()
        ]
    })

    answer = (
        f"The {label.lower()} of '{column}' is "
        f"{metric:,.2f}."
    )

    chart_data = pd.DataFrame({
        column: values
    })

    chart = px.histogram(
        chart_data,
        x=column,
        title=f"Distribution of {column}"
    )

    return {
        "answer": answer,
        "table": statistics,
        "chart": chart
    }


# =========================================================
# RANKING ANALYSIS
# =========================================================

def analyze_ranking(data, question):

    numeric_columns = get_numeric_columns(data)

    if not numeric_columns:
        return {
            "answer": "No numerical columns are available for ranking.",
            "table": None,
            "chart": None
        }

    column = find_column(
        question,
        numeric_columns
    )

    if column is None:

        if len(numeric_columns) == 1:
            column = numeric_columns[0]

        else:
            return {
                "answer": (
                    "Please specify the numerical column "
                    "you want to rank."
                ),
                "table": None,
                "chart": None
            }

    count = extract_number(question)

    descending = not any(
        word in clean_question(question)
        for word in [
            "bottom",
            "lowest",
            "least",
            "worst"
        ]
    )

    ranking = data.copy()

    ranking[column] = pd.to_numeric(
        ranking[column],
        errors="coerce"
    )

    ranking = ranking.dropna(
        subset=[column]
    )

    ranking = ranking.sort_values(
        column,
        ascending=not descending
    ).head(count)

    if ranking.empty:
        return {
            "answer": "No valid records were found for this ranking.",
            "table": None,
            "chart": None
        }

    label = "highest" if descending else "lowest"

    answer = (
        f"Here are the {len(ranking)} records "
        f"with the {label} values for '{column}'."
    )

    chart_data = ranking.reset_index(drop=True).copy()
    chart_data["Record"] = (
        chart_data.index + 1
    ).astype(str)

    chart = px.bar(
        chart_data,
        x="Record",
        y=column,
        title=f"Ranking by {column}"
    )

    chart.update_layout(
        xaxis_title="Record",
        yaxis_title=column
    )

    return {
        "answer": answer,
        "table": ranking.reset_index(drop=True),
        "chart": chart
    }


# =========================================================
# CORRELATION ANALYSIS
# =========================================================

def analyze_correlation(data, question):

    numeric_columns = get_numeric_columns(data)

    if len(numeric_columns) < 2:
        return {
            "answer": (
                "Correlation analysis requires at least "
                "two numerical columns."
            ),
            "table": None,
            "chart": None
        }

    correlation = data[
        numeric_columns
    ].corr(method="pearson")

    requested_columns = []

    for column in numeric_columns:
        if find_column(question, [column]):
            requested_columns.append(column)

    if len(requested_columns) >= 2:
        result = correlation.loc[
            requested_columns,
            requested_columns
        ]
    else:
        result = correlation

    chart = px.imshow(
        result,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Numerical Correlation Matrix"
    )

    answer = (
        "The correlation matrix shows the strength and direction "
        "of linear relationships between numerical columns. "
        "Values near +1 indicate positive association, values "
        "near -1 indicate negative association, and values near "
        "0 indicate weak linear association. Correlation does not "
        "establish that one variable causes another."
    )

    return {
        "answer": answer,
        "table": result.reset_index(),
        "chart": chart
    }


# =========================================================
# GROUP ANALYSIS
# =========================================================

def analyze_group(data, question):

    numeric_columns = get_numeric_columns(data)
    categorical_columns = get_categorical_columns(data)

    if not numeric_columns or not categorical_columns:
        return {
            "answer": (
                "Group analysis requires at least one numerical "
                "and one categorical column."
            ),
            "table": None,
            "chart": None
        }

    numeric_column = find_column(
        question,
        numeric_columns
    )

    categorical_column = find_column(
        question,
        categorical_columns
    )

    if numeric_column is None and len(numeric_columns) == 1:
        numeric_column = numeric_columns[0]

    if (
        categorical_column is None
        and len(categorical_columns) == 1
    ):
        categorical_column = categorical_columns[0]

    if numeric_column is None or categorical_column is None:
        return {
            "answer": (
                "Please include both a numerical column and "
                "a categorical column in your question."
            ),
            "table": None,
            "chart": None
        }

    working = data[
        [categorical_column, numeric_column]
    ].copy()

    working[numeric_column] = pd.to_numeric(
        working[numeric_column],
        errors="coerce"
    )

    working = working.dropna(
        subset=[categorical_column, numeric_column]
    )

    if working.empty:
        return {
            "answer": (
                "There are no valid records available "
                "for this group comparison."
            ),
            "table": None,
            "chart": None
        }

    grouped = (
        working.groupby(categorical_column)[numeric_column]
        .agg(["count", "mean", "sum", "median"])
        .reset_index()
        .sort_values("mean", ascending=False)
    )

    chart = px.bar(
        grouped,
        x=categorical_column,
        y="mean",
        title=f"Average {numeric_column} by {categorical_column}"
    )

    answer = (
        f"The average '{numeric_column}' has been calculated "
        f"for each '{categorical_column}' group. "
        f"The table is ranked from highest to lowest average."
    )

    return {
        "answer": answer,
        "table": grouped,
        "chart": chart
    }


# =========================================================
# UNIQUE VALUE ANALYSIS
# =========================================================

def analyze_unique(data, question):

    column = find_column(
        question,
        list(data.columns)
    )

    if column is None:
        return {
            "answer": (
                "Please include the exact column name "
                "you want to inspect."
            ),
            "table": None,
            "chart": None
        }

    counts = data[column].value_counts(
        dropna=False
    ).reset_index()

    counts.columns = [
        "Value",
        "Frequency"
    ]

    answer = (
        f"The column '{column}' contains "
        f"{data[column].nunique(dropna=True):,} "
        f"unique non-missing values."
    )

    chart = px.bar(
        counts.head(20),
        x="Value",
        y="Frequency",
        title=f"Value Frequencies: {column}"
    )

    return {
        "answer": answer,
        "table": counts.head(100),
        "chart": chart
    }


# =========================================================
# MAIN ANALYSIS ENGINE
# =========================================================

def analyze_question(data, question):

    if not isinstance(data, pd.DataFrame):
        raise ValueError(
            "The selected dataset is not a valid DataFrame."
        )

    if data.empty:
        raise ValueError(
            "The selected dataset is empty."
        )

    if not question or not str(question).strip():
        raise ValueError(
            "Enter a question before submitting."
        )

    intent = detect_analysis_intent(question)

    # Functions that accept only the dataset.
    single_argument_handlers = {
        "summary": analyze_summary,
        "missing": analyze_missing_values,
        "duplicates": analyze_duplicates,
    }

    # Functions that accept the dataset and question.
    two_argument_handlers = {
        "numeric": analyze_numeric,
        "ranking": analyze_ranking,
        "correlation": analyze_correlation,
        "group": analyze_group,
        "unique": analyze_unique,
    }

    if intent in single_argument_handlers:

        handler = single_argument_handlers[intent]

        result = handler(data)

    elif intent in two_argument_handlers:

        handler = two_argument_handlers[intent]

        result = handler(data, question)

    else:

        return {
            "intent": "unknown",
            "answer": (
                "I could not confidently interpret that question. "
                "Try asking about averages, totals, rankings, "
                "missing values, duplicates, correlations, "
                "unique values or group comparisons."
            ),
            "table": None,
            "chart": None
        }

    result["intent"] = intent

    return result


# =========================================================
# QUESTION SUGGESTIONS
# =========================================================

def render_question_suggestions(data):

    numeric_columns = get_numeric_columns(data)
    categorical_columns = get_categorical_columns(data)

    suggestions = [
        "Give me a summary of this dataset.",
        "Are there any missing values?",
        "How many duplicate rows are present?"
    ]

    if numeric_columns:

        column = numeric_columns[0]

        suggestions.extend([
            f"What is the average {column}?",
            f"What is the total {column}?",
            f"Show me the top 10 records by {column}."
        ])

    if len(numeric_columns) >= 2:
        suggestions.append(
            "Show me the correlation between numerical columns."
        )

    if numeric_columns and categorical_columns:
        suggestions.append(
            f"Compare {numeric_columns[0]} by {categorical_columns[0]}."
        )

    render_section_heading(
        "Suggested Questions",
        "Choose a question to explore your dataset."
    )

    for index, suggestion in enumerate(suggestions):

        if st.button(
            suggestion,
            key=f"jak_ai_suggestion_{index}",
            use_container_width=True
        ):
            st.session_state["jak_ai_question"] = suggestion
            st.rerun()


# =========================================================
# QUESTION FORM
# =========================================================

def render_ai_question_form(data):

    render_section_heading(
        "Ask Your Data",
        "Write a question in ordinary language."
    )

    render_question_suggestions(data)

    question = st.text_area(
        "Your Question",
        key="jak_ai_question",
        height=100,
        placeholder=(
            "Example: What is the average salary "
            "of employees in this dataset?"
        )
    )

    if st.button(
        "Analyse My Question",
        type="primary",
        use_container_width=True,
        key="jak_ai_analyse_button"
    ):

        try:

            with st.spinner(
                "JAK is analysing your question..."
            ):

                result = analyze_question(
                    data,
                    question
                )

                selected_dataset = st.session_state.get(
                    "jak_ai_selected_dataset_name",
                    "Selected Dataset"
                )

                st.session_state["jak_ai_current_result"] = {
                    "question": question,
                    "result": result,
                    "dataset": selected_dataset
                }

                history_item = {
                    "question": question,
                    "answer": result["answer"],
                    "intent": result["intent"],
                    "dataset": selected_dataset
                }

                history = st.session_state.get(
                    "jak_ai_history",
                    []
                )

                history.insert(0, history_item)

                st.session_state["jak_ai_history"] = history[:50]

                st.success(
                    "Your analysis has been completed."
                )

        except Exception as error:
            st.error(
                f"Analysis failed: {error}"
            )


# =========================================================
# ANSWER DISPLAY
# =========================================================

def render_ai_answer():

    saved = st.session_state.get(
        "jak_ai_current_result"
    )

    if not saved:

        render_empty_state(
            "Ready to Analyse",
            "Ask a question about your selected dataset to get started."
        )

        return

    result = saved["result"]

    render_section_heading(
        "Analysis Result",
        "Your question and its analytical response."
    )

    with st.container(border=True):

        st.caption("YOUR QUESTION")
        st.write(saved["question"])

    with st.container(border=True):

        st.subheader("JAK Analysis")
        st.write(result["answer"])

        st.caption(
            "Analysis method: "
            + result["intent"].replace("_", " ").title()
        )

    if result.get("table") is not None:

        st.subheader("Analytical Data")

        st.dataframe(
            result["table"],
            use_container_width=True,
            hide_index=True
        )

        table_csv = result["table"].to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Download Analytical Data",
            data=table_csv,
            file_name="jak_ai_analytical_data.csv",
            mime="text/csv",
            key="jak_ai_download_table"
        )

    if result.get("chart") is not None:

        st.subheader("Visual Analysis")

        st.plotly_chart(
            result["chart"],
            use_container_width=True
        )

    report = pd.DataFrame({
        "Question": [saved["question"]],
        "Answer": [result["answer"]],
        "Analysis Type": [result["intent"]],
        "Dataset": [saved["dataset"]]
    })

    st.download_button(
        "Download Analysis Summary",
        data=report.to_csv(index=False).encode("utf-8"),
        file_name="jak_ai_analysis_summary.csv",
        mime="text/csv",
        use_container_width=True,
        key="jak_ai_download_summary"
    )


# =========================================================
# ANALYSIS HISTORY
# =========================================================

def render_ai_history():

    render_section_heading(
        "Analysis History",
        "Review your recent questions and analytical responses."
    )

    history = st.session_state.get(
        "jak_ai_history",
        []
    )

    if not history:
        st.info(
            "Your analysis history will appear here."
        )
        return

    for index, item in enumerate(history):

        dataset_name = item.get(
            "dataset",
            "Unknown dataset"
        )

        with st.expander(
            item.get("question", "Previous question"),
            expanded=False
        ):

            st.caption(
                f"Dataset: {dataset_name}"
            )

            st.write(
                item.get("answer", "")
            )

            st.caption(
                "Analysis type: "
                + item.get("intent", "unknown").replace("_", " ").title()
            )

    if st.button(
        "Clear Analysis History",
        use_container_width=True,
        key="jak_ai_clear_history"
    ):

        st.session_state["jak_ai_history"] = []

        st.success(
            "Analysis history cleared."
        )

        st.rerun()


# =========================================================
# AI CAPABILITY INFORMATION
# =========================================================

def render_ai_capability_notice():

    st.divider()

    with st.container(border=True):

        st.subheader("About the Current AI Analyst")

        st.write(
            "This version uses a Python-based question interpreter "
            "and predefined analytical methods. It is not yet connected "
            "to a generative AI model."
        )

        st.write(
            "Questions that cannot be confidently interpreted receive "
            "a clarification message rather than an invented answer."
        )

        st.info(
            "Always verify analytical results before making important decisions."
        )


# =========================================================
# MAIN PAGE
# =========================================================

def render_ai_data_analyst_page():

    initialize_ai_state()

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
        "AI Data Analyst",
        "Ask questions about your data and discover useful analytical insights."
    )

    with st.container(border=True):

        st.title("JAK AI Data Analyst")

        st.write(
            "Explore your datasets using natural-language questions. "
            "Discover patterns, calculate statistics, inspect data quality "
            "and generate analytical charts."
        )

    datasets = get_datasets()

    if not datasets:

        st.warning(
            "Upload a dataset before using the AI Data Analyst."
        )

        show_footer()
        return

    # Build safe dataset options.
    dataset_options = {}

    for index, item in enumerate(datasets):

        name = str(
            item.get("name", f"Dataset {index + 1}")
        )

        display_name = name

        if display_name in dataset_options:
            display_name = f"{name} ({index + 1})"

        dataset_options[display_name] = item

    selected_name = st.selectbox(
        "Select Dataset",
        list(dataset_options.keys()),
        key="jak_ai_dataset_selector"
    )

    selected_dataset = dataset_options[selected_name]

    data = selected_dataset["data"]

    previous_dataset = st.session_state.get(
        "jak_ai_selected_dataset_name"
    )

    if previous_dataset != selected_name:

        st.session_state["jak_ai_selected_dataset_name"] = selected_name

        # Do not display a previous dataset's result
        # after switching to another dataset.
        st.session_state["jak_ai_current_result"] = None

    if data.empty:

        st.warning(
            "The selected dataset is empty."
        )

        show_footer()
        return

    summary = build_dataset_summary(data)

    first, second, third, fourth = st.columns(4)

    first.metric(
        "Records",
        f"{summary['rows']:,}"
    )

    second.metric(
        "Columns",
        f"{summary['columns']:,}"
    )

    third.metric(
        "Missing Cells",
        f"{summary['missing_cells']:,}"
    )

    fourth.metric(
        "Duplicates",
        f"{summary['duplicate_rows']:,}"
    )

    st.divider()

    tab1, tab2 = st.tabs([
        "Ask Your Data",
        "Analysis History"
    ])

    with tab1:

        render_ai_question_form(data)

        st.divider()

        render_ai_answer()

    with tab2:

        render_ai_history()

    render_ai_capability_notice()

    show_footer()


# =========================================================
# COMPATIBILITY ALIASES
# =========================================================

render_ai_data_analyst = render_ai_data_analyst_page
