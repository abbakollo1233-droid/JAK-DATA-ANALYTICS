
"""
JAK Data Analytics
Anomaly Detection Module

Features:
- Statistical anomaly detection
- Z-Score detection
- IQR detection
- Isolation Forest
- Local Outlier Factor
- One-Class SVM
- Anomaly visualisation
- Anomaly summaries
- Downloadable detection results

An anomaly is an unusual observation, not automatically
an error or fraudulent record.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM

from ...ui.layout import (
    render_topbar,
    render_page_intro,
    render_section_heading,
)

from ...ui.theme import show_footer


# =========================================================
# SESSION STATE
# =========================================================

def initialize_anomaly_state():

    defaults = {
        "jak_anomaly_results": None,
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


# =========================================================
# DATASET RETRIEVAL
# =========================================================

def get_datasets():

    datasets = st.session_state.get(
        "jak_datasets",
        []
    )

    if not isinstance(datasets, list):
        return []

    valid_datasets = []

    for item in datasets:

        if not isinstance(item, dict):
            continue

        data = item.get("data")

        if not isinstance(data, pd.DataFrame):
            continue

        if data.empty:
            continue

        valid_datasets.append(item)

    return valid_datasets


def render_dataset_selector():

    datasets = get_datasets()

    if not datasets:

        st.warning(
            "No valid datasets available. Upload a dataset first."
        )

        return None, None

    options = {}

    for index, item in enumerate(datasets):

        name = str(
            item.get(
                "name",
                f"Dataset {index + 1}"
            )
        )

        display_name = name

        if display_name in options:
            display_name = f"{name} ({index + 1})"

        options[display_name] = item

    selected_name = st.selectbox(
        "Select Dataset",
        list(options.keys()),
        key="jak_anomaly_dataset",
    )

    return options[selected_name], selected_name


# =========================================================
# HERO
# =========================================================

def render_anomaly_hero():

    with st.container(border=True):

        st.caption("JAK ANALYTICS INTELLIGENCE")

        st.subheader(
            "🔎 Anomaly Detection Intelligence"
        )

        st.write(
            """
            Discover unusual observations, identify unexpected
            patterns and investigate records that differ
            significantly from normal data behaviour.
            """
        )


# =========================================================
# DATASET OVERVIEW
# =========================================================

def render_dataset_overview(data):

    numeric_columns = data.select_dtypes(
        include="number"
    ).columns.tolist()

    categorical_columns = data.select_dtypes(
        include=["object", "string", "category", "bool"]
    ).columns.tolist()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Records",
        f"{len(data):,}"
    )

    col2.metric(
        "Total Features",
        len(data.columns)
    )

    col3.metric(
        "Numeric Features",
        len(numeric_columns)
    )

    col4.metric(
        "Categorical Features",
        len(categorical_columns)
    )


# =========================================================
# FEATURE PREPARATION
# =========================================================

def get_usable_features(data):

    numeric_columns = data.select_dtypes(
        include="number"
    ).columns.tolist()

    categorical_columns = data.select_dtypes(
        include=["object", "string", "category", "bool"]
    ).columns.tolist()

    return numeric_columns + categorical_columns


def prepare_anomaly_data(data, features):

    if not features:

        raise ValueError(
            "Select at least one feature."
        )

    missing_features = [
        feature
        for feature in features
        if feature not in data.columns
    ]

    if missing_features:

        raise ValueError(
            "Some selected features do not exist in the dataset."
        )

    working = data[features].copy()

    # Replace infinite numeric values with missing values.
    working = working.replace(
        [np.inf, -np.inf],
        np.nan
    )

    # Remove columns containing no usable observations.
    working = working.dropna(
        axis=1,
        how="all"
    )

    if working.empty or working.shape[1] == 0:

        raise ValueError(
            "The selected features do not contain usable data."
        )

    usable_features = get_usable_features(
        working
    )

    if not usable_features:

        raise ValueError(
            "Select numerical or categorical features. "
            "Datetime and unsupported columns cannot be analysed directly."
        )

    working = working[usable_features]

    return working


# =========================================================
# PREPROCESSING
# =========================================================

def get_anomaly_preprocessor(data):

    numeric_columns = data.select_dtypes(
        include="number"
    ).columns.tolist()

    categorical_columns = data.select_dtypes(
        include=["object", "string", "category", "bool"]
    ).columns.tolist()

    transformers = []

    if numeric_columns:

        numeric_pipeline = Pipeline([
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                )
            ),
            (
                "scaler",
                StandardScaler()
            )
        ])

        transformers.append(
            (
                "numeric",
                numeric_pipeline,
                numeric_columns
            )
        )

    if categorical_columns:

        categorical_pipeline = Pipeline([
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                )
            ),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore"
                )
            )
        ])

        transformers.append(
            (
                "categorical",
                categorical_pipeline,
                categorical_columns
            )
        )

    if not transformers:

        raise ValueError(
            "No usable numerical or categorical features were found."
        )

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop"
    )


def transform_anomaly_data(data):

    preprocessor = get_anomaly_preprocessor(
        data
    )

    prepared = preprocessor.fit_transform(
        data
    )

    if hasattr(prepared, "toarray"):

        # Avoid unexpectedly large memory usage when
        # categorical encoding creates a sparse matrix.
        required_cells = (
            prepared.shape[0] * prepared.shape[1]
        )

        if required_cells > 2_000_000:

            raise ValueError(
                "The encoded dataset is too large for safe dense "
                "processing. Reduce the selected features or "
                "categorical complexity."
            )

        prepared = prepared.toarray()

    prepared = np.asarray(
        prepared,
        dtype=float
    )

    if prepared.ndim != 2 or prepared.shape[1] == 0:

        raise ValueError(
            "Preprocessing did not produce usable features."
        )

    if not np.isfinite(prepared).all():

        raise ValueError(
            "Preprocessing produced invalid numerical values."
        )

    return prepared, preprocessor


# =========================================================
# Z-SCORE DETECTION
# =========================================================

def detect_zscore_anomalies(data, threshold):

    numeric = data.select_dtypes(
        include="number"
    )

    if numeric.shape[1] == 0:

        raise ValueError(
            "Z-Score detection requires numerical columns."
        )

    numeric = numeric.replace(
        [np.inf, -np.inf],
        np.nan
    )

    means = numeric.mean()

    standard_deviations = numeric.std(
        ddof=0
    )

    valid_columns = standard_deviations[
        standard_deviations > 0
    ].index.tolist()

    if not valid_columns:

        raise ValueError(
            "Z-Score detection requires at least one numerical "
            "column with variation."
        )

    numeric = numeric[valid_columns]

    scores = (
        numeric - means[valid_columns]
    ) / standard_deviations[valid_columns]

    scores = scores.replace(
        [np.inf, -np.inf],
        np.nan
    )

    feature_mask = (
        scores.abs() > threshold
    ).fillna(False)

    row_anomalies = feature_mask.any(
        axis=1
    )

    maximum_scores = scores.abs().max(
        axis=1
    ).fillna(0)

    return {
        "mask": row_anomalies,
        "scores": maximum_scores,
        "feature_mask": feature_mask,
        "method": "Z-Score",
        "score_description": "Maximum absolute Z-Score",
    }


# =========================================================
# IQR DETECTION
# =========================================================

def detect_iqr_anomalies(data, multiplier):

    numeric = data.select_dtypes(
        include="number"
    )

    if numeric.shape[1] == 0:

        raise ValueError(
            "IQR detection requires numerical columns."
        )

    numeric = numeric.replace(
        [np.inf, -np.inf],
        np.nan
    )

    q1 = numeric.quantile(
        0.25
    )

    q3 = numeric.quantile(
        0.75
    )

    iqr = q3 - q1

    valid_columns = iqr[
        iqr > 0
    ].index.tolist()

    if not valid_columns:

        raise ValueError(
            "IQR detection requires at least one numerical "
            "column with variation."
        )

    numeric = numeric[valid_columns]

    lower = (
        q1[valid_columns]
        - multiplier * iqr[valid_columns]
    )

    upper = (
        q3[valid_columns]
        + multiplier * iqr[valid_columns]
    )

    feature_mask = (
        (numeric < lower)
        |
        (numeric > upper)
    ).fillna(False)

    row_anomalies = feature_mask.any(
        axis=1
    )

    anomaly_scores = feature_mask.sum(
        axis=1
    )

    return {
        "mask": row_anomalies,
        "scores": anomaly_scores,
        "feature_mask": feature_mask,
        "method": "IQR",
        "score_description": "Number of anomalous features",
    }


# =========================================================
# ISOLATION FOREST
# =========================================================

def detect_isolation_forest(
    data,
    contamination,
    random_state,
):

    prepared, preprocessor = transform_anomaly_data(
        data
    )

    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )

    predictions = model.fit_predict(
        prepared
    )

    scores = model.decision_function(
        prepared
    )

    return {
        "mask": predictions == -1,
        "scores": scores,
        "model": model,
        "preprocessor": preprocessor,
        "method": "Isolation Forest",
        "score_description": "Isolation Forest decision function",
    }


# =========================================================
# LOCAL OUTLIER FACTOR
# =========================================================

def detect_local_outliers(
    data,
    contamination,
    neighbors,
):

    if len(data) <= neighbors:

        raise ValueError(
            "The number of records must exceed the selected "
            "number of neighbors."
        )

    prepared, preprocessor = transform_anomaly_data(
        data
    )

    model = LocalOutlierFactor(
        n_neighbors=neighbors,
        contamination=contamination,
        novelty=False,
        n_jobs=-1,
    )

    predictions = model.fit_predict(
        prepared
    )

    scores = model.negative_outlier_factor_

    return {
        "mask": predictions == -1,
        "scores": scores,
        "model": model,
        "preprocessor": preprocessor,
        "method": "Local Outlier Factor",
        "score_description": "Negative outlier factor",
    }


# =========================================================
# ONE-CLASS SVM
# =========================================================

def detect_one_class_svm(
    data,
    nu_value,
):

    prepared, preprocessor = transform_anomaly_data(
        data
    )

    model = OneClassSVM(
        kernel="rbf",
        gamma="scale",
        nu=nu_value,
    )

    predictions = model.fit_predict(
        prepared
    )

    scores = model.decision_function(
        prepared
    )

    return {
        "mask": predictions == -1,
        "scores": scores,
        "model": model,
        "preprocessor": preprocessor,
        "method": "One-Class SVM",
        "score_description": "One-Class SVM decision function",
    }


# =========================================================
# DETECTION CONFIGURATION
# =========================================================

def render_detection_configuration(data):

    render_section_heading(
        "Detection Configuration",
        "Choose an anomaly detection technique."
    )

    method = st.selectbox(
        "Detection Algorithm",
        [
            "Z-Score",
            "IQR",
            "Isolation Forest",
            "Local Outlier Factor",
            "One-Class SVM",
        ],
        key="jak_anomaly_method",
    )

    settings = {}

    if method == "Z-Score":

        settings["threshold"] = st.slider(
            "Z-Score Threshold",
            min_value=1.5,
            max_value=5.0,
            value=3.0,
            step=0.5,
            key="jak_anomaly_zscore_threshold",
        )

    elif method == "IQR":

        settings["multiplier"] = st.slider(
            "IQR Multiplier",
            min_value=1.0,
            max_value=4.0,
            value=1.5,
            step=0.5,
            key="jak_anomaly_iqr_multiplier",
        )

    elif method in [
        "Isolation Forest",
        "Local Outlier Factor",
        "One-Class SVM",
    ]:

        settings["contamination"] = st.slider(
            "Expected Anomaly Proportion",
            min_value=0.01,
            max_value=0.30,
            value=0.05,
            step=0.01,
            key="jak_anomaly_contamination",
        )

        if method == "Isolation Forest":

            settings["random_state"] = st.number_input(
                "Random State",
                min_value=0,
                max_value=10000,
                value=42,
                key="jak_anomaly_random_state",
            )

        elif method == "Local Outlier Factor":

            if len(data) < 4:

                st.error(
                    "Local Outlier Factor requires at least "
                    "4 records for the available settings."
                )

                return method, settings

            maximum_neighbors = min(
                50,
                len(data) - 1,
            )

            settings["neighbors"] = st.slider(
                "Number of Neighbors",
                min_value=2,
                max_value=maximum_neighbors,
                value=min(20, maximum_neighbors),
                key="jak_anomaly_neighbors",
            )

        elif method == "One-Class SVM":

            settings["nu_value"] = settings["contamination"]

    return method, settings


# =========================================================
# DETECTION ROUTER
# =========================================================

def run_anomaly_detection(
    data,
    method,
    settings,
):

    if method == "Z-Score":

        return detect_zscore_anomalies(
            data,
            settings["threshold"],
        )

    if method == "IQR":

        return detect_iqr_anomalies(
            data,
            settings["multiplier"],
        )

    if method == "Isolation Forest":

        return detect_isolation_forest(
            data,
            settings["contamination"],
            settings["random_state"],
        )

    if method == "Local Outlier Factor":

        return detect_local_outliers(
            data,
            settings["contamination"],
            settings["neighbors"],
        )

    if method == "One-Class SVM":

        return detect_one_class_svm(
            data,
            settings["nu_value"],
        )

    raise ValueError(
        "Unsupported anomaly detection method."
    )


# =========================================================
# RESULT PREPARATION
# =========================================================

def build_anomaly_results(
    original_data,
    detection,
):

    results = original_data.copy()

    mask = pd.Series(
        detection["mask"],
        index=original_data.index,
    ).fillna(False).astype(bool)

    scores = pd.Series(
        detection["scores"],
        index=original_data.index,
    )

    results["JAK_Anomaly_Status"] = np.where(
        mask,
        "Anomaly",
        "Normal",
    )

    results["JAK_Anomaly_Score"] = scores

    return results


# =========================================================
# ANOMALY METRICS
# =========================================================

def render_anomaly_metrics(results):

    anomaly_count = (
        results["JAK_Anomaly_Status"] == "Anomaly"
    ).sum()

    normal_count = (
        results["JAK_Anomaly_Status"] == "Normal"
    ).sum()

    total = len(results)

    percentage = (
        anomaly_count / total * 100
        if total else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Records",
        f"{total:,}",
    )

    col2.metric(
        "Anomalies Found",
        f"{anomaly_count:,}",
    )

    col3.metric(
        "Normal Records",
        f"{normal_count:,}",
    )

    col4.metric(
        "Anomaly Percentage",
        f"{percentage:.2f}%",
    )


# =========================================================
# ANOMALY DISTRIBUTION
# =========================================================

def render_anomaly_distribution(results):

    render_section_heading(
        "Anomaly Distribution",
        "Compare normal records with detected anomalies."
    )

    counts = (
        results["JAK_Anomaly_Status"]
        .value_counts()
        .reset_index()
    )

    counts.columns = [
        "Status",
        "Records",
    ]

    fig = px.pie(
        counts,
        names="Status",
        values="Records",
        hole=0.55,
        title="Normal Records vs Anomalies",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# =========================================================
# ANOMALY SCORE CHART
# =========================================================

def render_anomaly_score_chart(results):

    render_section_heading(
        "Anomaly Score Distribution",
        "Explore the scores assigned to individual records."
    )

    chart_data = results[
        [
            "JAK_Anomaly_Score",
            "JAK_Anomaly_Status",
        ]
    ].copy()

    fig = px.histogram(
        chart_data,
        x="JAK_Anomaly_Score",
        color="JAK_Anomaly_Status",
        nbins=40,
        title="Distribution of Anomaly Scores",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.caption(
        "Score direction differs by algorithm. For Z-Score and IQR, "
        "larger values generally indicate more unusual records. "
        "For Isolation Forest, Local Outlier Factor and One-Class SVM, "
        "lower decision scores generally indicate greater abnormality."
    )


# =========================================================
# NUMERICAL SCATTER PLOT
# =========================================================

def render_numeric_anomaly_scatter(
    results,
    features,
):

    numeric_features = [
        feature
        for feature in features
        if feature in results.columns
        and pd.api.types.is_numeric_dtype(
            results[feature]
        )
    ]

    if len(numeric_features) < 2:
        return

    render_section_heading(
        "Anomaly Visualisation",
        "Visualise unusual records across two numerical variables."
    )

    col1, col2 = st.columns(2)

    with col1:

        x_column = st.selectbox(
            "Horizontal Axis",
            numeric_features,
            key="jak_anomaly_x",
        )

    with col2:

        y_options = [
            column
            for column in numeric_features
            if column != x_column
        ]

        y_column = st.selectbox(
            "Vertical Axis",
            y_options,
            key="jak_anomaly_y",
        )

    fig = px.scatter(
        results,
        x=x_column,
        y=y_column,
        color="JAK_Anomaly_Status",
        hover_data=[
            "JAK_Anomaly_Score",
        ],
        title="Normal Observations and Anomalies",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# =========================================================
# ANOMALY TABLE
# =========================================================

def render_anomaly_table(results):

    render_section_heading(
        "Detected Anomaly Records",
        "Inspect records identified as unusual."
    )

    anomalies = results[
        results["JAK_Anomaly_Status"] == "Anomaly"
    ]

    if anomalies.empty:

        st.success(
            "No anomalies were detected using the selected method."
        )

    else:

        st.warning(
            f"{len(anomalies):,} unusual records were detected."
        )

        st.dataframe(
            anomalies,
            use_container_width=True,
        )

    with st.expander("View All Analysed Records"):

        st.dataframe(
            results,
            use_container_width=True,
        )

    csv_data = results.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "⬇️ Download Anomaly Detection Results",
        data=csv_data,
        file_name="jak_anomaly_detection_results.csv",
        mime="text/csv",
        key="jak_download_anomaly_results",
    )


# =========================================================
# COMPLETE RESULT DISPLAY
# =========================================================

def render_anomaly_results(
    results,
    features,
):

    render_anomaly_metrics(results)

    st.divider()

    render_anomaly_distribution(results)

    st.divider()

    render_anomaly_score_chart(results)

    st.divider()

    render_numeric_anomaly_scatter(
        results,
        features,
    )

    st.divider()

    render_anomaly_table(results)


# =========================================================
# ANOMALY GUIDANCE
# =========================================================

def render_anomaly_guidance():

    with st.container(border=True):

        st.warning(
            """
            Important Notice

            An anomaly is not automatically an error, fraud
            or suspicious activity.

            Unusual records should be investigated using relevant
            business or operational context before taking action.

            Do not automatically delete records because they
            have been identified as anomalies.
            """
        )


# =========================================================
# MAIN ANOMALY DETECTION PAGE
# =========================================================

def render_anomaly_detection_page():

    initialize_anomaly_state()

    username = st.session_state.get(
        "jak_user_name",
        "Guest",
    )

    role = st.session_state.get(
        "jak_user_role",
        "User",
    )

    render_topbar(
        username=username,
        role=role,
    )

    render_page_intro(
        "Anomaly Detection",
        "Identify unusual observations and unexpected data patterns.",
    )

    render_anomaly_hero()

    selected_dataset, dataset_name = render_dataset_selector()

    if selected_dataset is None:

        show_footer()
        return

    original_data = selected_dataset["data"].copy()

    if original_data.empty:

        st.warning(
            "The selected dataset is empty."
        )

        show_footer()
        return

    st.divider()

    render_dataset_overview(
        original_data
    )

    st.divider()

    render_section_heading(
        "Feature Selection",
        "Choose the columns JAK should analyse for unusual patterns."
    )

    available_features = get_usable_features(
        original_data
    )

    if not available_features:

        st.error(
            "This dataset does not contain supported numerical "
            "or categorical features."
        )

        show_footer()
        return

    selected_features = st.multiselect(
        "Select Analysis Features",
        available_features,
        default=available_features,
        key="jak_anomaly_features",
    )

    if not selected_features:

        st.warning(
            "Select at least one feature."
        )

        show_footer()
        return

    try:

        analysis_data = prepare_anomaly_data(
            original_data,
            selected_features,
        )

    except Exception as error:

        st.error(str(error))

        show_footer()
        return

    st.caption(
        f"{len(analysis_data):,} records and "
        f"{len(analysis_data.columns):,} usable features "
        "will be analysed."
    )

    st.divider()

    method, settings = render_detection_configuration(
        analysis_data
    )

    render_anomaly_guidance()

    if st.button(
        "🔍 Detect Anomalies",
        use_container_width=True,
        type="primary",
        key="jak_detect_anomalies",
    ):

        try:

            with st.spinner(
                "JAK is analysing your dataset..."
            ):

                detection = run_anomaly_detection(
                    analysis_data,
                    method,
                    settings,
                )

                results = build_anomaly_results(
                    original_data,
                    detection,
                )

                st.session_state["jak_anomaly_results"] = {
                    "dataset": dataset_name,
                    "method": method,
                    "features": selected_features.copy(),
                    "settings": settings.copy(),
                    "results": results,
                    "score_description": detection.get(
                        "score_description",
                        "Anomaly score",
                    ),
                }

            st.success(
                "Anomaly detection completed successfully!"
            )

        except Exception as error:

            st.error(
                f"Anomaly detection failed: {error}"
            )

    saved = st.session_state.get(
        "jak_anomaly_results"
    )

    # Display results only when all relevant settings match.
    if isinstance(saved, dict):

        same_configuration = (
            saved.get("dataset") == dataset_name
            and saved.get("features") == selected_features
            and saved.get("method") == method
            and saved.get("settings") == settings
        )

        if same_configuration:

            st.divider()

            st.subheader(
                f"Detection Method: {saved['method']}"
            )

            st.caption(
                saved.get("score_description", "Anomaly score")
            )

            render_anomaly_results(
                saved["results"],
                saved["features"],
            )

    show_footer()


# =========================================================
# NAVIGATION COMPATIBILITY
# =========================================================

render_anomaly_detection = render_anomaly_detection_page
