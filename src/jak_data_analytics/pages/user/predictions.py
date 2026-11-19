"""
JAK Data Analytics
Predictions Module

Features:
- Crop information lookup by crop name.
- Display N, P, K, temperature, humidity, pH and rainfall.
- Crop profile averages and median values.
- Downloadable crop profiles.
- Retrieve previously trained ML models.
- Classification and regression predictions.
- Classification probabilities.
- Prediction history.
- Download prediction history.

Models and prediction history are currently retained
in Streamlit session state.

Permanent model storage will be implemented later.
"""

import streamlit as st
import pandas as pd
import numpy as np

from ...ui.layout import (
    render_topbar,
    render_page_intro,
    render_section_heading,
)

from ...ui.theme import show_footer


# =========================================================
# CONSTANTS
# =========================================================

CROP_FEATURES = {
    "N": "Nitrogen (N)",
    "P": "Phosphorus (P)",
    "K": "Potassium (K)",
    "temperature": "Temperature",
    "humidity": "Humidity",
    "ph": "Soil pH",
    "rainfall": "Rainfall",
}


# =========================================================
# SESSION STATE
# =========================================================

def initialize_prediction_state():
    """Initialize prediction-related session state."""

    defaults = {
        "jak_prediction_history": [],
        "jak_latest_prediction": None,
        "jak_crop_name_search": "",
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


# =========================================================
# DATASET RETRIEVAL
# =========================================================

def get_all_datasets():
    """Retrieve uploaded datasets from session state."""

    datasets = st.session_state.get(
        "jak_datasets",
        []
    )

    if not isinstance(datasets, list):
        return []

    valid_datasets = []

    for dataset in datasets:

        if not isinstance(dataset, dict):
            continue

        data = dataset.get("data")

        if isinstance(data, pd.DataFrame):

            valid_datasets.append(dataset)

    return valid_datasets


def get_training_dataset(dataset_name):
    """Retrieve the original dataset used for training."""

    for dataset in get_all_datasets():

        if dataset.get("name") == dataset_name:

            return dataset.get("data")

    return None


# =========================================================
# CROP DATASET DETECTION
# =========================================================

def get_crop_datasets():
    """
    Find uploaded datasets that contain crop information.

    A dataset must contain a 'label' column.
    At least one recognized crop feature must also exist.
    """

    crop_datasets = []

    for dataset in get_all_datasets():

        data = dataset.get("data")

        if data is None:
            continue

        columns = data.columns.tolist()

        has_crop_name = (
            "label" in columns
        )

        has_crop_features = any(
            feature in columns
            for feature in CROP_FEATURES
        )

        if has_crop_name and has_crop_features:

            crop_datasets.append(dataset)

    return crop_datasets


# =========================================================
# MODEL RETRIEVAL
# =========================================================

def get_trained_model():
    """Retrieve the latest trained classification or regression model."""

    saved = st.session_state.get(
        "jak_ml_results"
    )

    if not isinstance(saved, dict):
        return None

    if saved.get("task") not in [
        "Classification",
        "Regression",
    ]:
        return None

    results = saved.get(
        "results",
        {}
    )

    if not isinstance(results, dict):
        return None

    pipeline = results.get(
        "pipeline"
    )

    if pipeline is None:
        return None

    return saved


# =========================================================
# PREDICTION HERO
# =========================================================

def render_prediction_hero():
    """Display the prediction introduction."""

    with st.container(border=True):

        st.caption(
            "JAK ANALYTICS INTELLIGENCE"
        )

        st.subheader(
            "🔮 Prediction Studio"
        )

        st.write(
            """
            Explore crop information, use trained machine
            learning models and generate predictions from
            new information.

            JAK helps transform your datasets into useful
            information for better decisions.
            """
        )


# =========================================================
# CROP INFORMATION LOOKUP
# =========================================================

def render_crop_profile_lookup():
    """
    Allow users to search for a crop by name
    and display its available soil and weather characteristics.

    This feature works independently of model training.
    """

    st.divider()

    render_section_heading(
        "🌱 Crop Information Lookup",
        "Search for a crop to view its soil and weather characteristics."
    )

    crop_datasets = get_crop_datasets()

    if not crop_datasets:

        st.info(
            """
            No suitable crop dataset was found.

            Upload a crop dataset containing a column named
            'label' and columns such as N, P, K, temperature,
            humidity, ph and rainfall.
            """
        )

        return

    # -----------------------------------------------------
    # SELECT CROP DATASET
    # -----------------------------------------------------

    dataset_options = {}

    for index, dataset in enumerate(crop_datasets):

        name = dataset.get(
            "name",
            f"Crop Dataset {index + 1}"
        )

        dataset_options[
            f"{name} ({len(dataset['data']):,} records)"
        ] = dataset

    selected_dataset_name = st.selectbox(
        "Select crop dataset",
        list(dataset_options.keys()),
        key="jak_crop_profile_dataset"
    )

    selected_dataset = dataset_options[
        selected_dataset_name
    ]

    data = selected_dataset["data"]

    # -----------------------------------------------------
    # CROP NAME SEARCH
    # -----------------------------------------------------

    crop_names = (
        data["label"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    crop_names = [
        name
        for name in crop_names.unique().tolist()
        if name
    ]

    crop_names = sorted(
        crop_names,
        key=str.lower
    )

    if not crop_names:

        st.warning(
            "No crop names were found in this dataset."
        )

        return

    crop_name = st.text_input(
        "Enter crop name",
        placeholder="Example: Rice, Maize, Tomato...",
        key="jak_crop_name_search"
    )

    if not crop_name.strip():

        st.info(
            "Type a crop name to view its information."
        )

        with st.expander("View available crop names"):

            st.write(
                ", ".join(crop_names)
            )

        return

    # -----------------------------------------------------
    # FIND MATCHING CROP
    # -----------------------------------------------------

    matching_data = data[
        data["label"]
        .astype(str)
        .str.strip()
        .str.lower()
        == crop_name.strip().lower()
    ].copy()

    if matching_data.empty:

        st.warning(
            f"No information was found for '{crop_name}'."
        )

        st.caption(
            "Check the spelling or select one of the available crops."
        )

        with st.expander("Available crops"):

            st.write(
                ", ".join(crop_names)
            )

        return

    # -----------------------------------------------------
    # CALCULATE CROP VALUES
    # -----------------------------------------------------

    crop_values = {}

    for column, display_name in CROP_FEATURES.items():

        if column not in matching_data.columns:
            continue

        values = pd.to_numeric(
            matching_data[column],
            errors="coerce"
        )

        values = values.replace(
            [np.inf, -np.inf],
            np.nan
        ).dropna()

        if values.empty:
            continue

        crop_values[display_name] = {
            "median": float(values.median()),
            "mean": float(values.mean()),
            "minimum": float(values.min()),
            "maximum": float(values.max()),
        }

    if not crop_values:

        st.warning(
            "No numeric crop information was found."
        )

        return

    # -----------------------------------------------------
    # CROP PROFILE HEADER
    # -----------------------------------------------------

    st.success(
        f"Crop information found: {crop_name.strip().title()}"
    )

    st.caption(
        f"Dataset: {selected_dataset.get('name', 'Unknown')} "
        f"| Matching records: {len(matching_data):,}"
    )

    st.subheader(
        f"🌿 {crop_name.strip().title()} — Crop Profile"
    )

    # -----------------------------------------------------
    # DISPLAY METRIC CARDS
    # -----------------------------------------------------

    items = list(
        crop_values.items()
    )

    for start in range(0, len(items), 3):

        row_items = items[start:start + 3]

        columns = st.columns(3)

        for index, (name, values) in enumerate(row_items):

            with columns[index]:

                st.metric(
                    label=name,
                    value=f"{values['median']:.2f}",
                )

    # -----------------------------------------------------
    # DETAILED CROP TABLE
    # -----------------------------------------------------

    render_section_heading(
        "Detailed Crop Information",
        "Statistical summary of the matching crop records."
    )

    profile_records = []

    for name, values in crop_values.items():

        profile_records.append({
            "Parameter": name,
            "Median": round(
                values["median"],
                3
            ),
            "Average": round(
                values["mean"],
                3
            ),
            "Minimum": round(
                values["minimum"],
                3
            ),
            "Maximum": round(
                values["maximum"],
                3
            ),
        })

    profile_df = pd.DataFrame(
        profile_records
    )

    st.dataframe(
        profile_df,
        use_container_width=True,
        hide_index=True
    )

    # -----------------------------------------------------
    # DOWNLOAD CROP PROFILE
    # -----------------------------------------------------

    csv_data = profile_df.to_csv(
        index=False
    ).encode("utf-8")

    filename = (
        crop_name.strip()
        .lower()
        .replace(" ", "_")
        + "_crop_profile.csv"
    )

    st.download_button(
        "⬇️ Download Crop Information",
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        key="jak_download_crop_profile"
    )

    # -----------------------------------------------------
    # DISCLAIMER
    # -----------------------------------------------------

    st.caption(
        """
        Important: These values are calculated from your uploaded
        dataset. They describe the records in that dataset and are
        not guaranteed planting requirements for every location.
        Soil testing and local agricultural advice may be necessary
        before making planting or fertilizer decisions.
        """
    )


# =========================================================
# MODEL INFORMATION
# =========================================================

def render_model_information(saved):
    """Display information about the selected model."""

    render_section_heading(
        "Selected Machine Learning Model",
        "Review the model that will generate your predictions."
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Machine Learning Task",
        saved.get("task", "Unknown")
    )

    col2.metric(
        "Algorithm",
        saved.get("model_name", "Unknown")
    )

    col3.metric(
        "Training Dataset",
        saved.get("dataset_name", "Unknown")
    )

    results = saved.get(
        "results",
        {}
    )

    metrics = results.get(
        "metrics",
        {}
    )

    if metrics:

        st.subheader(
            "Model Performance"
        )

        valid_metrics = []

        for name, value in metrics.items():

            try:

                numeric_value = float(value)

                if np.isfinite(numeric_value):

                    valid_metrics.append(
                        (name, numeric_value)
                    )

            except (
                ValueError,
                TypeError,
            ):

                continue

        if valid_metrics:

            columns = st.columns(
                min(len(valid_metrics), 4)
            )

            for index, (name, value) in enumerate(valid_metrics):

                with columns[index % len(columns)]:

                    st.metric(
                        name,
                        f"{value:.4f}"
                    )


# =========================================================
# MODEL FEATURE INFORMATION
# =========================================================

def get_prediction_features(pipeline):
    """Get the exact feature order expected by the trained pipeline."""

    features = getattr(
        pipeline,
        "feature_names_in_",
        None
    )

    if features is None:

        raise ValueError(
            "The trained model does not contain feature information. "
            "Train a new model using a pandas DataFrame."
        )

    return list(features)


# =========================================================
# NUMERIC INPUT DEFAULT
# =========================================================

def get_default_numeric_value(series):
    """Get a safe numeric default from a training column."""

    values = pd.to_numeric(
        series,
        errors="coerce"
    )

    values = values.replace(
        [np.inf, -np.inf],
        np.nan
    )

    median = values.median()

    if pd.isna(median):
        return 0.0

    return float(median)


# =========================================================
# INPUT FIELD GENERATION
# =========================================================

def render_input_fields(data, features):
    """Generate input fields for a new prediction."""

    input_values = {}

    render_section_heading(
        "Enter New Information",
        "Provide values for the input features used during model training."
    )

    st.info(
        "Use the same type of information and measurement units "
        "as the original training dataset."
    )

    with st.form("jak_prediction_form"):

        columns = st.columns(2)

        for index, feature in enumerate(features):

            series = data[feature]

            with columns[index % 2]:

                # Boolean columns first.
                if pd.api.types.is_bool_dtype(series):

                    value = st.selectbox(
                        feature,
                        [True, False],
                        key=f"jak_prediction_boolean_{index}",
                    )

                    input_values[feature] = value

                elif pd.api.types.is_numeric_dtype(series):

                    default_value = get_default_numeric_value(
                        series
                    )

                    value = st.number_input(
                        feature,
                        value=default_value,
                        key=f"jak_prediction_numeric_{index}",
                    )

                    input_values[feature] = value

                else:

                    categories = (
                        series.dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    )

                    categories = sorted(
                        categories
                    )

                    if categories:

                        value = st.selectbox(
                            feature,
                            categories,
                            key=f"jak_prediction_category_{index}",
                        )

                    else:

                        value = st.text_input(
                            feature,
                            key=f"jak_prediction_text_{index}",
                        )

                    input_values[feature] = value

        submitted = st.form_submit_button(
            "🔮 Generate Prediction",
            use_container_width=True,
            type="primary",
        )

    return submitted, input_values


# =========================================================
# PREDICTION ENGINE
# =========================================================

def generate_prediction(saved, input_values):
    """Generate a prediction using the trained pipeline."""

    pipeline = saved["results"]["pipeline"]

    features = get_prediction_features(
        pipeline
    )

    if not features:

        raise ValueError(
            "The trained model has no input features."
        )

    missing_values = [
        feature
        for feature in features
        if feature not in input_values
    ]

    if missing_values:

        raise ValueError(
            "Missing prediction inputs: "
            + ", ".join(missing_values)
        )

    input_data = pd.DataFrame(
        [
            {
                feature: input_values[feature]
                for feature in features
            }
        ],
        columns=features,
    )

    predictions = pipeline.predict(
        input_data
    )

    if len(predictions) == 0:

        raise ValueError(
            "The model did not return a prediction."
        )

    prediction = predictions[0]

    probability = None

    if saved["task"] == "Classification":

        if hasattr(pipeline, "predict_proba"):

            try:

                probabilities = pipeline.predict_proba(
                    input_data
                )[0]

                classes = pipeline.classes_

                probability = {
                    str(label): float(score)
                    for label, score in zip(
                        classes,
                        probabilities,
                    )
                }

            except (
                ValueError,
                AttributeError,
                TypeError,
            ):

                probability = None

    return prediction, probability


# =========================================================
# PREDICTION RESULT
# =========================================================

def render_prediction_result(
    prediction,
    probability,
    task,
):
    """Display the generated prediction."""

    st.divider()

    render_section_heading(
        "Prediction Result",
        "JAK has processed your input using the trained model."
    )

    with st.container(border=True):

        st.success(
            "Prediction generated successfully!"
        )

        st.subheader(
            "Predicted Outcome"
        )

        st.title(
            str(prediction)
        )

        st.caption(
            f"Prediction type: {task}"
        )

    if task == "Classification" and probability:

        render_section_heading(
            "Class Probabilities",
            "Estimated probability for each possible class."
        )

        probability_data = pd.DataFrame({
            "Class": list(probability.keys()),
            "Probability": list(probability.values()),
        })

        probability_data["Percentage"] = (
            probability_data["Probability"] * 100
        )

        probability_data = probability_data.sort_values(
            "Percentage",
            ascending=False,
        )

        st.dataframe(
            probability_data[
                ["Class", "Percentage"]
            ],
            use_container_width=True,
            hide_index=True,
        )

        for _, row in probability_data.iterrows():

            st.write(
                f"**{row['Class']}** — "
                f"{row['Percentage']:.2f}%"
            )

            st.progress(
                min(
                    max(
                        float(row["Probability"]),
                        0.0
                    ),
                    1.0
                )
            )

        st.caption(
            "These probabilities are model estimates and may not "
            "be well calibrated."
        )

    elif task == "Regression":

        st.info(
            "This is a numerical prediction generated by the "
            "trained regression model."
        )


# =========================================================
# PREDICTION HISTORY
# =========================================================

def save_prediction_history(
    saved,
    input_values,
    prediction,
    probability,
):
    """Save a prediction in session-based history."""

    history = st.session_state.setdefault(
        "jak_prediction_history",
        [],
    )

    record = {
        "dataset": saved.get("dataset_name"),
        "model": saved.get("model_name"),
        "task": saved.get("task"),
        "input": input_values.copy(),
        "prediction": str(prediction),
        "probability": probability,
        "created_at": pd.Timestamp.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    }

    history.insert(
        0,
        record
    )

    st.session_state["jak_prediction_history"] = history[:100]

    st.session_state["jak_latest_prediction"] = record


# =========================================================
# PREDICTION HISTORY DISPLAY
# =========================================================

def render_prediction_history():
    """Display previous predictions."""

    history = st.session_state.get(
        "jak_prediction_history",
        [],
    )

    render_section_heading(
        "Prediction History",
        "Review predictions generated during this session."
    )

    if not history:

        st.info(
            "No predictions have been generated yet."
        )

        return

    records = []

    for item in history:

        records.append({
            "Date": item.get("created_at", ""),
            "Dataset": item.get("dataset", ""),
            "Model": item.get("model", ""),
            "Task": item.get("task", ""),
            "Prediction": item.get("prediction", ""),
        })

    history_df = pd.DataFrame(
        records
    )

    st.dataframe(
        history_df,
        use_container_width=True,
        hide_index=True,
    )

    csv_data = history_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "⬇️ Download Prediction History",
        data=csv_data,
        file_name="jak_prediction_history.csv",
        mime="text/csv",
        key="jak_download_prediction_history",
    )

    if st.button(
        "Clear Prediction History",
        key="jak_clear_prediction_history",
    ):

        st.session_state["jak_prediction_history"] = []

        st.session_state["jak_latest_prediction"] = None

        st.success(
            "Prediction history cleared."
        )

        st.rerun()


# =========================================================
# PREDICTION GUIDANCE
# =========================================================

def render_prediction_guidance():
    """Display prediction limitations and guidance."""

    st.divider()

    with st.container(border=True):

        st.warning(
            """
            Important Prediction Notice

            Predictions are estimates based on patterns learned
            from training data. They are not guarantees of future
            outcomes.

            Review model performance, data quality and possible
            bias before using predictions to make important decisions.
            """
        )


# =========================================================
# MAIN PREDICTIONS PAGE
# =========================================================

def render_predictions_page():
    """Main predictions page renderer."""

    initialize_prediction_state()

    username = (
        st.session_state.get("jak_user_name")
        or "Guest"
    )

    role = (
        st.session_state.get("jak_user_role")
        or "User"
    )

    render_topbar(
        username=username,
        role=role,
    )

    render_page_intro(
        "Predictions",
        "Explore crop information and generate predictions using trained machine learning models.",
    )

    render_prediction_hero()

    # =====================================================
    # CROP LOOKUP
    # =====================================================

    # This section is available even when no model is trained.
    render_crop_profile_lookup()

    # =====================================================
    # MACHINE LEARNING PREDICTIONS
    # =====================================================

    st.divider()

    render_section_heading(
        "🤖 Machine Learning Predictions",
        "Generate predictions using a previously trained model."
    )

    saved = get_trained_model()

    if saved is None:

        st.warning(
            "No trained classification or regression model is available."
        )

        st.info(
            """
            To generate machine learning predictions:

            1. Open Machine Learning.
            2. Select a dataset.
            3. Train a classification or regression model.
            4. Return here to generate predictions.

            The crop information lookup above can still be used
            without training a machine learning model.
            """
        )

        render_prediction_history()

        show_footer()

        return

    render_model_information(
        saved
    )

    data = get_training_dataset(
        saved.get("dataset_name")
    )

    if data is None:

        st.error(
            "The original training dataset is no longer available "
            "in this session."
        )

        render_prediction_history()

        show_footer()

        return

    pipeline = saved["results"]["pipeline"]

    try:

        features = get_prediction_features(
            pipeline
        )

    except ValueError as error:

        st.error(
            str(error)
        )

        render_prediction_history()

        show_footer()

        return

    missing_features = [
        feature
        for feature in features
        if feature not in data.columns
    ]

    if missing_features:

        st.error(
            "Some required training features are missing from "
            "the original dataset."
        )

        st.write(
            missing_features
        )

        render_prediction_history()

        show_footer()

        return

    st.divider()

    submitted, input_values = render_input_fields(
        data,
        features,
    )

    if submitted:

        try:

            with st.spinner(
                "JAK is generating your prediction..."
            ):

                prediction, probability = generate_prediction(
                    saved,
                    input_values,
                )

                save_prediction_history(
                    saved,
                    input_values,
                    prediction,
                    probability,
                )

            st.success(
                "Your prediction has been generated."
            )

        except Exception as error:

            st.error(
                f"Prediction failed: {error}"
            )

    latest = st.session_state.get(
        "jak_latest_prediction"
    )

    if (
        isinstance(latest, dict)
        and latest.get("dataset") == saved.get("dataset_name")
        and latest.get("model") == saved.get("model_name")
    ):

        render_prediction_result(
            prediction=latest["prediction"],
            probability=latest.get("probability"),
            task=latest.get("task"),
        )

    render_prediction_guidance()

    st.divider()

    render_prediction_history()

    show_footer()


# =========================================================
# NAVIGATION COMPATIBILITY
# =========================================================

render_predictions = render_predictions_page