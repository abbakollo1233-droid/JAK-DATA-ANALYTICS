"""
JAK Data Analytics
JAK Health Intelligence

Main healthcare interface.

Features:
- Modern healthcare dashboard
- Healthcare overview
- Disease directory
- Medical dataset upload and library
- Medical data validation
- General experimental disease model training
- Symptom-only disease model training
- Yes / No / Not sure symptom questionnaire
- Automatic symptom counting
- Top-five ranked disease suggestions
- Prediction charts
- Related-condition and complication information
- Emergency warning flags
- Prediction history
- Downloadable prediction reports

IMPORTANT:
This application provides experimental medical data analysis.
It does not provide confirmed medical diagnoses.
"""

import streamlit as st
import pandas as pd
import numpy as np

from datetime import datetime
import html

from ...ui.layout import (
    render_topbar,
    render_page_intro,
    render_section_heading,
)

from ...ui.theme import show_footer

from ...domain_modules.healthcare import (
    DISEASE_REGISTRY,
    MEDICAL_DISCLAIMER,
    get_disease_categories,
    get_diseases_by_category,
    search_diseases,
    get_registered_disease_count,
    validate_medical_dataset,
    generate_validation_report,
    train_disease_model,
    predict_disease_model,
    get_model_information,
    get_medical_model_safety_status,
    SUPPORTED_ALGORITHMS,
)

# Symptom prediction engine
from ...domain_modules.healthcare.symptom_prediction_engine import (
    SYMPTOM_LABELS,
    SYMPTOM_COLUMNS,
    MEDICAL_DISCLAIMER as SYMPTOM_DISCLAIMER,
    get_symptom_questions,
    count_symptoms,
    train_symptom_model,
    predict_from_symptoms,
    get_urgent_warning_flags,
)


# ==========================================
# CONSTANTS
# ==========================================

SYMPTOM_MODEL_STATE_KEY = (
    "jak_healthcare_symptom_model"
)

SYMPTOM_RESULT_STATE_KEY = (
    "jak_healthcare_symptom_result"
)

SYMPTOM_HISTORY_STATE_KEY = (
    "jak_healthcare_symptom_history"
)

SYMPTOM_MODEL_NAME = (
    "JAK Symptom-Based Disease Model"
)


# ==========================================
# MODERN HEALTHCARE DESIGN
# ==========================================

def apply_healthcare_design():

    st.markdown("""
    <style>

    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .block-container {
        max-width: 1450px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    [data-testid="stAppViewContainer"] {
        background: #f5f7fb;
    }

    [data-testid="stSidebar"] {
        background: #101828;
    }

    [data-testid="stSidebar"] * {
        color: #ffffff;
    }

    [data-testid="stMetric"] {
        background: #ffffff;
        padding: 22px;
        border: 1px solid #e8edf5;
        border-radius: 16px;
        box-shadow: 0 4px 15px rgba(16, 24, 40, 0.04);
    }

    [data-testid="stMetricLabel"] {
        color: #667085;
        font-weight: 600;
    }

    [data-testid="stMetricValue"] {
        color: #101828;
        font-weight: 800;
    }

    div[data-testid="stTabs"] button {
        font-weight: 600;
        padding: 12px 18px;
    }

    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #087f3f;
        border-bottom: 3px solid #16a34a;
    }

    div.stButton > button {
        border-radius: 10px;
        min-height: 42px;
        font-weight: 600;
        border: 1px solid #d0d5dd;
        transition: 0.2s ease;
    }

    div.stButton > button[kind="primary"] {
        background: #087f3f;
        color: white;
        border: none;
    }

    div.stButton > button[kind="primary"]:hover {
        background: #064e2b;
        color: white;
    }

    div[data-testid="stFileUploader"] {
        background: #ffffff;
        padding: 18px;
        border: 1px dashed #98a2b3;
        border-radius: 14px;
    }

    div[data-testid="stExpander"] {
        background: #ffffff;
        border: 1px solid #e8edf5;
        border-radius: 12px;
    }

    .jak-healthcare-banner {
        background: linear-gradient(
            120deg,
            #064e2b,
            #087f3f
        );
        padding: 30px;
        border-radius: 18px;
        color: white;
        margin-bottom: 22px;
    }

    .jak-healthcare-banner h2 {
        color: white;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .jak-healthcare-banner p {
        color: #dcfce7;
        margin-bottom: 0;
    }

    .jak-dataset-card {
        background: white;
        border: 1px solid #e8edf5;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 12px;
    }

    .jak-muted {
        color: #667085;
        font-size: 13px;
    }

    .jak-prediction-card {
        background: #ffffff;
        border: 1px solid #e8edf5;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 12px;
    }

    .jak-prediction-number {
        color: #087f3f;
        font-size: 13px;
        font-weight: 700;
    }

    .jak-prediction-title {
        color: #101828;
        font-size: 21px;
        font-weight: 800;
        margin-top: 5px;
    }

    .jak-safety-note {
        background: #fff7ed;
        border-left: 4px solid #f59e0b;
        padding: 14px;
        border-radius: 8px;
        margin: 12px 0;
    }

    .jak-success-note {
        background: #ecfdf3;
        border-left: 4px solid #16a34a;
        padding: 14px;
        border-radius: 8px;
        margin: 12px 0;
    }

    </style>
    """, unsafe_allow_html=True)


# ==========================================
# SESSION STATE
# ==========================================


def initialize_healthcare_state():
    defaults = {
        "jak_healthcare_models": {},
        "jak_healthcare_validation": None,
        "jak_healthcare_dataset": None,
        "jak_healthcare_predictions": None,
        "jak_healthcare_prediction_history": [],
        "jak_healthcare_selected_disease": "diabetes",
        "jak_healthcare_uploaded_datasets": {},
        "jak_healthcare_delete_confirmation": None,
        SYMPTOM_MODEL_STATE_KEY: None,
        SYMPTOM_RESULT_STATE_KEY: None,
        SYMPTOM_HISTORY_STATE_KEY: [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Restore saved general models when this Streamlit session starts.
    if not st.session_state.get("jak_healthcare_models"):
        st.session_state["jak_healthcare_models"] = (
            load_persisted_healthcare_models()
        )


def get_healthcare_datasets():

    datasets = st.session_state.get(
        "jak_datasets",
        {},
    )

    if not isinstance(datasets, dict):
        return {}

    return {
        name: dataframe
        for name, dataframe in datasets.items()
        if isinstance(dataframe, pd.DataFrame)
    }


def get_uploaded_healthcare_datasets():

    datasets = st.session_state.get(
        "jak_healthcare_uploaded_datasets",
        {},
    )

    if not isinstance(datasets, dict):
        return {}

    return datasets


def get_dataset_fingerprint(dataframe):

    import hashlib

    try:

        values = pd.util.hash_pandas_object(
            dataframe,
            index=True,
        ).values.tobytes()

        return hashlib.sha256(
            values
        ).hexdigest()

    except Exception:

        return hashlib.sha256(
            dataframe.to_csv(index=True).encode("utf-8")
        ).hexdigest()


def store_healthcare_dataset(dataframe, name):

    dataframe = dataframe.copy()

    fingerprint = get_dataset_fingerprint(
        dataframe
    )

    current = get_current_healthcare_dataset()

    if (
        current
        and current.get("name") == name
        and current.get("fingerprint") == fingerprint
    ):
        return

    st.session_state[
        "jak_healthcare_dataset"
    ] = {
        "name": name,
        "data": dataframe,
        "fingerprint": fingerprint,
    }

    st.session_state[
        "jak_healthcare_validation"
    ] = None

    st.session_state[
        "jak_healthcare_predictions"
    ] = None

    st.session_state[
        SYMPTOM_RESULT_STATE_KEY
    ] = None


def register_uploaded_healthcare_dataset(dataframe, name):

    datasets = get_uploaded_healthcare_datasets()

    fingerprint = get_dataset_fingerprint(
        dataframe
    )

    existing = datasets.get(name)

    if (
        isinstance(existing, dict)
        and existing.get("fingerprint") == fingerprint
    ):
        store_healthcare_dataset(
            dataframe,
            name,
        )
        return

    datasets[name] = {
        "name": name,
        "data": dataframe.copy(),
        "fingerprint": fingerprint,
        "source": "healthcare_upload",
    }

    st.session_state[
        "jak_healthcare_uploaded_datasets"
    ] = datasets

    store_healthcare_dataset(
        dataframe,
        name,
    )


def get_current_healthcare_dataset():

    saved = st.session_state.get(
        "jak_healthcare_dataset"
    )

    if not isinstance(saved, dict):
        return None

    dataframe = saved.get("data")

    if not isinstance(dataframe, pd.DataFrame):
        return None

    return saved


# ==========================================
# MODEL HELPERS
# ==========================================

def get_model_key(
    disease_code,
    dataset_name,
    fingerprint,
    target,
):

    return (
        f"{disease_code}::"
        f"{dataset_name}::"
        f"{fingerprint}::"
        f"{target}"
    )



def get_model_library_path():
    """Return the local file used to persist general healthcare models."""
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[4]
    model_directory = project_root / "data" / "healthcare_models"
    model_directory.mkdir(parents=True, exist_ok=True)
    return model_directory / "general_models.joblib"


def load_persisted_healthcare_models():
    """Load previously trained general models without overwriting live models."""
    import joblib

    path = get_model_library_path()
    if not path.exists():
        return {}

    try:
        saved = joblib.load(path)
        return saved if isinstance(saved, dict) else {}
    except Exception as error:
        st.warning(
            "The saved general model library could not be loaded. "
            f"Details: {error}"
        )
        return {}


def persist_healthcare_models(models):
    """Persist the general model dictionary to the project's data folder."""
    import joblib

    path = get_model_library_path()
    temporary_path = path.with_suffix(".tmp")
    joblib.dump(models, temporary_path)
    temporary_path.replace(path)


def save_healthcare_model(key, model_bundle):
    """Save a general model in session state and on disk."""
    if not isinstance(model_bundle, dict):
        raise TypeError("The trained model bundle must be a dictionary.")

    if not isinstance(model_bundle.get("metadata"), dict):
        model_bundle["metadata"] = {}

    models = get_healthcare_models()
    models[str(key)] = model_bundle

    st.session_state["jak_healthcare_models"] = models
    persist_healthcare_models(models)


def get_healthcare_models():
    """Return the shared general model library, restoring it from disk if needed."""
    models = st.session_state.get("jak_healthcare_models")

    if not isinstance(models, dict):
        models = {}

    if not models:
        models = load_persisted_healthcare_models()

    # Also recover from an older in-session backup key if one exists.
    legacy_models = st.session_state.get("jak_healthcare_model_library", {})
    if isinstance(legacy_models, dict):
        for key, bundle in legacy_models.items():
            models.setdefault(key, bundle)

    st.session_state["jak_healthcare_models"] = models
    return models


def delete_healthcare_dataset(dataset_name, source):

    if source == "healthcare_upload":

        datasets = get_uploaded_healthcare_datasets()

        datasets.pop(
            dataset_name,
            None,
        )

        st.session_state[
            "jak_healthcare_uploaded_datasets"
        ] = datasets

    elif source == "jak_dataset":

        datasets = st.session_state.get(
            "jak_datasets",
            {},
        )

        if isinstance(datasets, dict):

            datasets.pop(
                dataset_name,
                None,
            )

            st.session_state[
                "jak_datasets"
            ] = datasets

    saved = get_current_healthcare_dataset()

    if saved and saved.get("name") == dataset_name:

        st.session_state[
            "jak_healthcare_dataset"
        ] = None

        st.session_state[
            "jak_healthcare_validation"
        ] = None

        st.session_state[
            "jak_healthcare_predictions"
        ] = None

        st.session_state[
            "jak_healthcare_prediction_history"
        ] = []

        st.session_state[
            SYMPTOM_MODEL_STATE_KEY
        ] = None

        st.session_state[
            SYMPTOM_RESULT_STATE_KEY
        ] = None

        st.session_state[
            SYMPTOM_HISTORY_STATE_KEY
        ] = []

        st.session_state.pop(
            "jak_healthcare_last_trained_model",
            None,
        )

    models = get_healthcare_models()

    remaining_models = {}

    for key, bundle in models.items():

        parts = key.split("::")

        model_dataset_name = (
            parts[1]
            if len(parts) > 1
            else None
        )

        if model_dataset_name != dataset_name:
            remaining_models[key] = bundle

    st.session_state[
        "jak_healthcare_models"
    ] = remaining_models

    try:
        persist_healthcare_models(remaining_models)
    except Exception as error:
        st.warning(f"Updated model library could not be saved: {error}")


# ==========================================
# PAGE HEADER
# ==========================================

def render_healthcare_header():

    render_topbar(
        username="Healthcare Workspace",
        role="Medical Analytics",
    )

    st.markdown("""
    <div class="jak-healthcare-banner">

        <h2>JAK Health Intelligence</h2>

        <p>
            Healthcare data analysis, machine learning,
            symptom-based disease classification and medical insights.
        </p>

    </div>
    """, unsafe_allow_html=True)

    st.warning(
        "Medical safety notice: This is an experimental "
        "machine-learning application. Its predictions are not "
        "confirmed diagnoses and must not replace professional "
        "medical assessment."
    )


# ==========================================
# OVERVIEW
# ==========================================

def render_healthcare_overview():

    saved_dataset = get_current_healthcare_dataset()

    if not saved_dataset:
        return

    render_section_heading(
        "Healthcare Overview",
        "Your medical analytics workspace.",
    )

    models = get_healthcare_models()

    dataframe = saved_dataset["data"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Dataset Records",
            f"{len(dataframe):,}",
        )

    with col2:

        st.metric(
            "Dataset Columns",
            len(dataframe.columns),
        )

    with col3:

        st.metric(
            "Trained Models",
            len(models)
            + int(
                st.session_state.get(
                    SYMPTOM_MODEL_STATE_KEY
                ) is not None
            ),
        )

    with col4:

        st.metric(
            "Registered Conditions",
            get_registered_disease_count(),
        )

    st.divider()

    st.subheader("Active Medical Dataset")

    st.write(
        f"**Dataset name:** {saved_dataset['name']}"
    )

    st.write(
        f"**Total records:** {len(dataframe):,}"
    )

    st.write(
        f"**Total columns:** {len(dataframe.columns):,}"
    )

    st.write("**Available columns:**")

    st.write(
        ", ".join(map(str, dataframe.columns))
    )

    missing = int(
        dataframe.isna().sum().sum()
    )

    st.metric(
        "Missing Cells",
        missing,
    )

    st.success(
        "Your medical dataset is loaded."
    )

    st.info(MEDICAL_DISCLAIMER)


# ==========================================
# DISEASE DIRECTORY
# ==========================================

def render_disease_directory():

    render_section_heading(
        "Disease Directory",
        "Browse diseases and medical conditions supported by the registry.",
    )

    categories = get_disease_categories()

    selected_category = st.selectbox(
        "Select disease category",
        ["All Categories"] + categories,
        key="jak_healthcare_category",
    )

    search_term = st.text_input(
        "Search for a disease or condition",
        placeholder="Example: diabetes, malaria, cancer...",
        key="jak_healthcare_search",
    )

    if search_term.strip():

        diseases = search_diseases(
            search_term
        )

    elif selected_category == "All Categories":

        diseases = DISEASE_REGISTRY

    else:

        diseases = get_diseases_by_category(
            selected_category
        )

    if not diseases:

        st.info(
            "No matching diseases were found."
        )

        return

    st.caption(
        f"{len(diseases)} registered disease entries found."
    )

    for code, disease in diseases.items():

        with st.expander(
            f"{disease['name']} — {disease['category']}"
        ):

            st.write(
                disease["description"]
            )

            st.markdown("**Related conditions**")

            for condition in disease.get("conditions", []):
                st.write(f"• {condition}")

            st.markdown("**Assessment method**")

            st.write(
                disease["assessment_type"]
            )

            st.markdown("**Required information**")

            st.write(
                ", ".join(disease["required_data"])
            )

            st.caption(
                "Model development status: "
                + disease["model_status"].replace("_", " ").title()
            )

            st.button(
                "Use this disease",
                key=f"use_disease_{code}",
                on_click=lambda selected=code: (
                    st.session_state.update({
                        "jak_healthcare_selected_disease": selected
                    })
                ),
            )


# ==========================================
# DATASET MANAGEMENT
# ==========================================

def render_medical_dataset_upload():

    render_section_heading(
        "Medical Dataset Management",
        "Upload, view, load and manage healthcare datasets.",
    )

    upload_tab, library_tab = st.tabs([
        "Upload Dataset",
        "Dataset Library",
    ])

    with upload_tab:

        st.subheader("Upload a Medical Dataset")

        st.caption(
            "Supported formats: CSV, XLSX and XLS."
        )

        uploaded_file = st.file_uploader(
            "Choose a medical dataset",
            type=["csv", "xlsx", "xls"],
            key="jak_healthcare_upload",
        )

        if uploaded_file is not None:

            try:

                if uploaded_file.name.lower().endswith(".csv"):

                    dataframe = pd.read_csv(
                        uploaded_file
                    )

                else:

                    dataframe = pd.read_excel(
                        uploaded_file
                    )

                if dataframe.empty:

                    st.error(
                        "The uploaded dataset is empty."
                    )

                else:

                    register_uploaded_healthcare_dataset(
                        dataframe,
                        uploaded_file.name,
                    )

                    st.success(
                        f"{uploaded_file.name} is available "
                        "in your healthcare dataset library."
                    )

                    st.write("### Dataset Preview")

                    st.dataframe(
                        dataframe.head(10),
                        use_container_width=True,
                    )

            except Exception as error:

                st.error(
                    f"Unable to read dataset: {error}"
                )

    with library_tab:

        st.subheader("Your Dataset Library")

        uploaded_datasets = get_uploaded_healthcare_datasets()

        existing_datasets = get_healthcare_datasets()

        dataset_options = {}

        for name, item in uploaded_datasets.items():

            if not isinstance(item, dict):
                continue

            dataframe = item.get("data")

            if not isinstance(dataframe, pd.DataFrame):
                continue

            dataset_options[
                f"{name} — Uploaded Medical Dataset"
            ] = {
                "name": name,
                "data": dataframe,
                "source": "healthcare_upload",
            }

        for name, dataframe in existing_datasets.items():

            dataset_options[
                f"{name} — JAK Dataset"
            ] = {
                "name": name,
                "data": dataframe,
                "source": "jak_dataset",
            }

        if not dataset_options:

            st.info(
                "Your dataset library is empty. "
                "Upload a dataset to get started."
            )

        else:

            st.caption(
                f"{len(dataset_options)} dataset(s) available."
            )

            for display_name, item in dataset_options.items():

                dataframe = item["data"]

                name = item["name"]

                source = item["source"]

                with st.container(border=True):

                    st.markdown(
                        f"### 📁 {name}"
                    )

                    st.caption(
                        "Uploaded medical dataset"
                        if source == "healthcare_upload"
                        else "Existing JAK dataset"
                    )

                    col1, col2, col3 = st.columns(3)

                    with col1:

                        st.metric(
                            "Records",
                            f"{len(dataframe):,}",
                        )

                    with col2:

                        st.metric(
                            "Columns",
                            len(dataframe.columns),
                        )

                    with col3:

                        st.metric(
                            "Missing Cells",
                            int(dataframe.isna().sum().sum()),
                        )

                    action_col1, action_col2 = st.columns(2)

                    with action_col1:

                        if st.button(
                            "Load Dataset",
                            key=f"load_healthcare_{source}_{name}",
                            use_container_width=True,
                        ):

                            store_healthcare_dataset(
                                dataframe,
                                name,
                            )

                            st.success(
                                f"{name} is now active."
                            )

                            st.rerun()

                    with action_col2:

                        if st.button(
                            "Delete Dataset",
                            key=f"delete_healthcare_{source}_{name}",
                            use_container_width=True,
                        ):

                            st.session_state[
                                "jak_healthcare_delete_confirmation"
                            ] = {
                                "name": name,
                                "source": source,
                            }

                            st.rerun()

                    with st.expander("Preview Dataset"):

                        st.dataframe(
                            dataframe.head(20),
                            use_container_width=True,
                        )

        confirmation = st.session_state.get(
            "jak_healthcare_delete_confirmation"
        )

        if confirmation:

            st.divider()

            st.error(
                f"Delete '{confirmation['name']}'?"
            )

            st.warning(
                "Deleting a shared JAK dataset also removes it "
                "from the shared dataset session used by other pages."
            )

            confirm_col1, confirm_col2 = st.columns(2)

            with confirm_col1:

                if st.button(
                    "Yes, Delete Dataset",
                    type="primary",
                    key="jak_confirm_dataset_delete",
                    use_container_width=True,
                ):

                    delete_healthcare_dataset(
                        confirmation["name"],
                        confirmation["source"],
                    )

                    st.session_state[
                        "jak_healthcare_delete_confirmation"
                    ] = None

                    st.success(
                        "Dataset deleted successfully."
                    )

                    st.rerun()

            with confirm_col2:

                if st.button(
                    "Cancel",
                    key="jak_cancel_dataset_delete",
                    use_container_width=True,
                ):

                    st.session_state[
                        "jak_healthcare_delete_confirmation"
                    ] = None

                    st.rerun()

    saved = get_current_healthcare_dataset()

    if saved:

        st.divider()

        st.subheader("Active Medical Dataset")

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Dataset",
                saved["name"],
            )

        with col2:

            st.metric(
                "Records",
                f"{len(saved['data']):,}",
            )

        with col3:

            st.metric(
                "Columns",
                len(saved["data"].columns),
            )

        with st.expander("View Available Columns"):

            st.write(
                ", ".join(map(str, saved["data"].columns))
            )


# ==========================================
# MEDICAL DATA VALIDATION
# ==========================================

def render_medical_validation():

    render_section_heading(
        "Medical Data Validation",
        "Check data quality before training experimental models.",
    )

    saved = get_current_healthcare_dataset()

    if not saved:

        st.info(
            "Upload or load a medical dataset first."
        )

        return

    dataframe = saved["data"]

    st.write(
        f"Dataset: **{saved['name']}**"
    )

    required_fields = st.multiselect(
        "Select columns that must not be empty",
        options=list(dataframe.columns),
        key="jak_healthcare_required_fields",
    )

    if st.button(
        "Validate Medical Dataset",
        type="primary",
        key="jak_healthcare_validate",
    ):

        try:

            result = validate_medical_dataset(
                dataframe,
                required_fields,
            )

            st.session_state[
                "jak_healthcare_validation"
            ] = result

        except Exception as error:

            st.error(
                f"Validation failed: {error}"
            )

    result = st.session_state.get(
        "jak_healthcare_validation"
    )

    if result:

        summary = result.get(
            "summary",
            {},
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Total Records",
                summary.get("total_rows", 0),
            )

        with col2:

            st.metric(
                "Invalid Records",
                summary.get("invalid_rows", 0),
            )

        with col3:

            st.metric(
                "Missing Values",
                summary.get("missing_values", 0),
            )

        if result.get("valid"):

            st.success(
                "The selected validation checks passed."
            )

        else:

            st.warning(
                "The dataset has validation issues."
            )

        for error in result.get("column_errors", []):
            st.error(error)

        row_errors = result.get(
            "row_errors",
            [],
        )

        if row_errors:

            st.write("**Invalid Records**")

            st.dataframe(
                pd.DataFrame(row_errors),
                use_container_width=True,
            )

        missing_values = result.get(
            "missing_values",
            {},
        )

        if missing_values:

            missing_frame = pd.DataFrame({
                "Column": list(missing_values.keys()),
                "Missing Values": list(missing_values.values()),
            })

            st.write("**Missing Values by Column**")

            st.dataframe(
                missing_frame,
                use_container_width=True,
            )

        report = generate_validation_report(
            result
        )

        st.download_button(
            "Download Validation Report",
            data=report,
            file_name="jak_medical_validation_report.txt",
            mime="text/plain",
            key="jak_healthcare_validation_download",
        )


# ==========================================
# GENERAL DISEASE MODEL TRAINING
# ==========================================


def render_general_disease_model_training():
    render_section_heading(
        "General Disease Model Training",
        "Train experimental classification models using labelled medical data.",
    )

    saved = get_current_healthcare_dataset()
    if not saved:
        st.info("Upload or load a medical dataset first.")
        return

    dataframe = saved["data"]
    if dataframe.empty or len(dataframe.columns) < 2:
        st.error("The dataset must contain records and at least two columns.")
        return

    disease_options = {
        f"{value['name']} ({code})": code
        for code, value in DISEASE_REGISTRY.items()
    }
    selected_disease_label = st.selectbox(
        "Select disease or model category",
        list(disease_options.keys()),
        key="jak_healthcare_training_disease",
    )
    disease_code = disease_options[selected_disease_label]
    disease = DISEASE_REGISTRY[disease_code]
    st.info(disease["description"])

    target_column = st.selectbox(
        "Select target column",
        options=list(dataframe.columns),
        key="jak_healthcare_target",
    )
    possible_features = [
        column for column in dataframe.columns if column != target_column
    ]
    feature_columns = st.multiselect(
        "Select medical feature columns",
        options=possible_features,
        default=possible_features,
        key="jak_healthcare_features",
    )
    algorithm = st.selectbox(
        "Machine learning algorithm",
        options=SUPPORTED_ALGORITHMS,
        format_func=lambda value: value.replace("_", " ").title(),
        key="jak_healthcare_algorithm",
    )
    test_percentage = st.slider(
        "Testing dataset percentage",
        min_value=10,
        max_value=40,
        value=20,
        step=5,
        key="jak_healthcare_test_percentage",
    )

    st.warning(
        "Use appropriately obtained, labelled data and remove personal "
        "identifiers. Avoid data leakage and features that reveal the target."
    )

    if st.button(
        "Train General Disease Model",
        type="primary",
        key="jak_healthcare_train",
    ):
        if not feature_columns:
            st.error("Select at least one feature column.")
        elif dataframe[target_column].dropna().nunique() < 2:
            st.error("The target column must contain at least two classes.")
        else:
            try:
                with st.spinner("Training experimental disease model..."):
                    model_bundle = train_disease_model(
                        dataframe=dataframe,
                        disease_code=disease_code,
                        target_column=target_column,
                        feature_columns=feature_columns,
                        algorithm=algorithm,
                        test_size=test_percentage / 100,
                    )

                if not isinstance(model_bundle, dict):
                    raise TypeError(
                        "The training engine did not return a model bundle."
                    )

                metadata = model_bundle.setdefault("metadata", {})
                metadata.setdefault("disease_code", disease_code)
                metadata.setdefault("algorithm", algorithm)
                metadata.setdefault("target_column", target_column)
                metadata.setdefault("feature_columns", list(feature_columns))
                metadata.setdefault("dataset_name", saved["name"])
                metadata.setdefault("dataset_fingerprint", saved["fingerprint"])
                metadata.setdefault(
                    "trained_at",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )

                key = get_model_key(
                    disease_code,
                    saved["name"],
                    saved["fingerprint"],
                    target_column,
                )
                save_healthcare_model(key, model_bundle)
                st.session_state["jak_healthcare_last_trained_model"] = key
                st.session_state["jak_healthcare_predictions"] = None
                st.success(
                    "General disease model trained and saved to the model library."
                )
                st.rerun()

            except Exception as error:
                st.error(f"Model training failed: {error}")

    models = get_healthcare_models()
    last_key = st.session_state.get("jak_healthcare_last_trained_model")
    if last_key and last_key in models:
        render_model_evaluation(models[last_key])

    st.divider()
    st.subheader("Available General Models")
    models = get_healthcare_models()
    if models:
        st.success(f"{len(models)} general model(s) are available.")
        st.write("\n".join(f"• {key}" for key in models.keys()))
    else:
        st.info("No general model has been trained yet.")


def render_symptom_model_training():

    render_section_heading(
        "Symptom-Based Model Training",
        "Train a model that learns disease classifications from symptom combinations.",
    )

    saved = get_current_healthcare_dataset()

    if not saved:

        st.info(
            "Upload or load a medical dataset first."
        )

        return

    dataframe = saved["data"]

    st.markdown("### Dataset Requirements")

    st.write(
        "Your dataset must contain:"
    )

    st.write(
        "- At least three supported symptom columns."
    )

    st.write(
        "- A target column named disease_label."
    )

    st.write(
        "- Known disease labels for each training record."
    )

    st.write(
        "- Symptom values represented as 1 for Yes and 0 for No."
    )

    if "disease_label" not in dataframe.columns:

        st.error(
            "The active dataset does not contain the required "
            "'disease_label' column."
        )

        st.info(
            "Rename your disease outcome column to disease_label "
            "or prepare a separate symptom training dataset."
        )

        return

    available_symptoms = [
        column
        for column in SYMPTOM_COLUMNS
        if column in dataframe.columns
    ]

    missing_symptoms = [
        column
        for column in SYMPTOM_COLUMNS
        if column not in dataframe.columns
    ]

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Available Symptoms",
            len(available_symptoms),
        )

    with col2:

        st.metric(
            "Missing Supported Symptoms",
            len(missing_symptoms),
        )

    with col3:

        st.metric(
            "Disease Classes",
            dataframe["disease_label"].nunique(),
        )

    if len(available_symptoms) < 3:

        st.error(
            "At least three supported symptom columns are required."
        )

        return

    with st.expander("View detected symptom columns"):

        st.write(
            ", ".join(available_symptoms)
        )

    with st.expander("View missing supported symptom columns"):

        st.write(
            ", ".join(missing_symptoms)
            if missing_symptoms
            else "All supported symptom columns are available."
        )

    st.warning(
        "The model uses symptom columns only. It does not use "
        "laboratory measurements or unrelated information. "
        "The quality of the labels and dataset determines what "
        "the model can learn."
    )

    test_percentage = st.slider(
        "Testing dataset percentage",
        min_value=10,
        max_value=40,
        value=20,
        step=5,
        key="jak_symptom_test_percentage",
    )

    if st.button(
        "Train Symptom Prediction Model",
        type="primary",
        key="jak_symptom_train_button",
        use_container_width=True,
    ):

        try:

            with st.spinner(
                "Training the symptom-based model..."
            ):

                model_bundle = train_symptom_model(
                    dataframe=dataframe,
                    test_size=test_percentage / 100,
                    random_state=42,
                )

            model_bundle["dataset_name"] = saved["name"]

            model_bundle["dataset_fingerprint"] = (
                saved["fingerprint"]
            )

            st.session_state[
                SYMPTOM_MODEL_STATE_KEY
            ] = model_bundle

            st.session_state[
                SYMPTOM_RESULT_STATE_KEY
            ] = None

            st.success(
                "Symptom-based model trained successfully."
            )

        except Exception as error:

            st.error(
                f"Symptom model training failed: {error}"
            )

    model_bundle = st.session_state.get(
        SYMPTOM_MODEL_STATE_KEY
    )

    if model_bundle:

        st.divider()

        st.subheader("Symptom Model Information")

        metadata = model_bundle.get(
            "metadata",
            {},
        )

        metrics = model_bundle.get(
            "metrics",
            {},
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Training Records",
                metadata.get("training_records", 0),
            )

        with col2:

            st.metric(
                "Disease Classes",
                metadata.get("number_of_classes", 0),
            )

        with col3:

            st.metric(
                "Test Accuracy",
                f"{metrics.get('accuracy', 0) * 100:.2f}%",
            )

        st.write(
            f"**Dataset:** {model_bundle.get('dataset_name', 'Unknown')}"
        )

        st.write(
            f"**Training features:** {len(model_bundle.get('feature_columns', []))}"
        )

        st.write(
            f"**Clinical validation:** "
            f"{metadata.get('clinical_validation_status', 'Unknown')}"
        )

        st.caption(
            "Holdout test accuracy is not proof of real-world medical accuracy."
        )


# ==========================================
# MODEL EVALUATION
# ==========================================

def render_model_evaluation(model_bundle):

    render_section_heading(
        "Model Evaluation",
        "Performance on the held-out test data.",
    )

    information = get_model_information(
        model_bundle
    )

    metadata = information["metadata"]

    metrics = information["metrics"]

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Accuracy",
            f"{metrics.get('accuracy', 0) * 100:.2f}%",
        )

    with col2:

        st.metric(
            "Precision",
            f"{metrics.get('precision', 0) * 100:.2f}%",
        )

    with col3:

        st.metric(
            "Recall",
            f"{metrics.get('recall', 0) * 100:.2f}%",
        )

    col4, col5 = st.columns(2)

    with col4:

        st.metric(
            "F1 Score",
            f"{metrics.get('f1_score', 0) * 100:.2f}%",
        )

    with col5:

        st.metric(
            "Balanced Accuracy",
            f"{metrics.get('balanced_accuracy', 0) * 100:.2f}%",
        )

    st.subheader("Model Performance Comparison")

    performance_frame = pd.DataFrame({
        "Metric": [
            "Accuracy",
            "Balanced Accuracy",
            "Precision",
            "Recall",
            "F1 Score",
        ],
        "Score": [
            metrics.get("accuracy", 0),
            metrics.get("balanced_accuracy", 0),
            metrics.get("precision", 0),
            metrics.get("recall", 0),
            metrics.get("f1_score", 0),
        ],
    })

    st.bar_chart(
        performance_frame.set_index("Metric")
    )

    st.write("**Model Information**")

    st.write(
        f"Algorithm: {metadata.get('algorithm', 'Unknown')}"
    )

    st.write(
        f"Model category: {metadata.get('disease_code', 'Unknown')}"
    )

    st.write(
        f"Training records: {metadata.get('training_records', 0)}"
    )

    st.write(
        f"Testing records: {metadata.get('testing_records', 0)}"
    )

    st.write(
        f"Classes: {', '.join(metadata.get('class_labels', []))}"
    )

    st.write(
        f"Clinical validation: "
        f"{metadata.get('clinical_validation_status', 'Unknown')}"
    )

    confusion = metrics.get(
        "confusion_matrix"
    )

    if confusion:

        labels = metadata.get(
            "class_labels",
            [],
        )

        confusion_frame = pd.DataFrame(
            confusion,
            index=[
                f"Actual: {label}"
                for label in labels
            ],
            columns=[
                f"Predicted: {label}"
                for label in labels
            ],
        )

        st.write("**Confusion Matrix**")

        st.dataframe(
            confusion_frame,
            use_container_width=True,
        )

    st.caption(
        "These metrics describe performance on the selected test split. "
        "They do not establish clinical safety or real-world diagnostic accuracy."
    )


# ==========================================
# GENERAL MODEL INPUT TYPE DETECTION
# ==========================================

def get_model_feature_types(model_bundle):

    numeric_features = set()

    categorical_features = set()

    try:

        preprocessor = model_bundle[
            "model"
        ].named_steps["preprocessor"]

        for name, transformer, columns in preprocessor.transformers_:

            if name == "numeric":

                numeric_features.update(
                    columns
                )

            elif name == "categorical":

                categorical_features.update(
                    columns
                )

    except Exception:
        pass

    return numeric_features, categorical_features


# ==========================================
# GENERAL PREDICTION FORM
# ==========================================


def render_prediction_form(model_bundle, selected_key):
    metadata = model_bundle.get("metadata", {})
    feature_columns = metadata.get("feature_columns", [])

    if not feature_columns:
        st.error("This model does not contain feature-column metadata.")
        return

    numeric_features, categorical_features = get_model_feature_types(model_bundle)
    input_values = {}

    st.markdown("### Enter Available Information")
    st.info(
        "Enter the information you have. Leave unknown fields blank. "
        "Unknown numeric values are passed as missing values to the model."
    )

    with st.form("jak_healthcare_prediction_form"):
        columns = st.columns(2)
        for index, feature in enumerate(feature_columns):
            with columns[index % 2]:
                label = str(feature).replace("_", " ").title()
                input_values[feature] = st.text_input(
                    label,
                    placeholder=(
                        "Enter a number or leave blank"
                        if feature in numeric_features
                        else "Enter information or leave blank"
                    ),
                    key=f"jak_general_input_{selected_key}_{feature}",
                )

        top_k = st.slider(
            "Number of ranked suggestions",
            min_value=1,
            max_value=5,
            value=5,
            key=f"jak_healthcare_top_k_{selected_key}",
        )
        submitted = st.form_submit_button(
            "Generate Disease Suggestions",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    try:
        record = {}
        filled_fields = 0

        for feature, raw_value in input_values.items():
            value = str(raw_value).strip()
            if not value:
                record[feature] = np.nan
                continue

            filled_fields += 1
            if feature in numeric_features:
                try:
                    record[feature] = float(value)
                except ValueError:
                    raise ValueError(
                        f"{feature} must contain a valid number."
                    )
            else:
                record[feature] = value

        if filled_fields == 0:
            raise ValueError(
                "Enter at least one field before generating suggestions."
            )

        # Keep every model feature in the same order used during training.
        record_frame = pd.DataFrame(
            [{feature: record.get(feature, np.nan)
              for feature in feature_columns}],
            columns=feature_columns,
        )

        with st.spinner("Analysing available information..."):
            raw_result = predict_disease_model(model_bundle, record_frame)

        # The general prediction engine returns a DataFrame. Convert its
        # predicted class and model_score_<class> columns into the page format.
        if isinstance(raw_result, dict):
            prediction_frame = raw_result.get(
                "predictions",
                raw_result.get("prediction", pd.DataFrame()),
            )
            ranked_frame = raw_result.get("ranked_predictions")
        elif isinstance(raw_result, pd.DataFrame):
            prediction_frame = raw_result.copy()
            ranked_frame = None
        else:
            raise TypeError(
                "The prediction engine returned an unsupported result type."
            )

        if not isinstance(prediction_frame, pd.DataFrame):
            raise TypeError("The prediction engine did not return a DataFrame.")
        if prediction_frame.empty:
            raise ValueError("The prediction engine returned no predictions.")

        if not isinstance(ranked_frame, pd.DataFrame):
            prediction_row = prediction_frame.iloc[0]
            score_columns = [
                column for column in prediction_frame.columns
                if str(column).startswith("model_score_")
            ]

            ranked_items = []
            for score_column in score_columns:
                label = str(score_column)[len("model_score_"):]
                score = pd.to_numeric(
                    pd.Series([prediction_row[score_column]]),
                    errors="coerce",
                ).iloc[0]
                if pd.notna(score):
                    ranked_items.append({
                        "disease": label,
                        "model_score": float(score),
                    })

            if ranked_items:
                ranked_items.sort(
                    key=lambda item: item["model_score"],
                    reverse=True,
                )
                ranked_items = ranked_items[:top_k]
            else:
                predicted = prediction_row.get(
                    "predicted_class",
                    prediction_row.get("prediction", "Unranked output"),
                )
                ranked_items = [{
                    "disease": str(predicted),
                    "model_score": np.nan,
                }]

            ranked_frame = pd.DataFrame(ranked_items)
            ranked_frame.insert(0, "rank", range(1, len(ranked_frame) + 1))
            ranked_frame.insert(0, "record_number", 1)
            ranked_frame["clinical_validation_status"] = (
                metadata.get("clinical_validation_status", "Not clinically validated")
            )

        # Normalize an already-ranked engine result too.
        if "disease" not in ranked_frame.columns:
            label_column = next(
                (c for c in ["Disease label", "predicted_class", "prediction"]
                 if c in ranked_frame.columns),
                None,
            )
            if label_column:
                ranked_frame = ranked_frame.rename(
                    columns={label_column: "disease"}
                )

        if "model_score" not in ranked_frame.columns:
            score_column = next(
                (c for c in ["Model score", "score", "probability"]
                 if c in ranked_frame.columns),
                None,
            )
            if score_column:
                ranked_frame = ranked_frame.rename(
                    columns={score_column: "model_score"}
                )

        if "disease" not in ranked_frame.columns:
            raise ValueError(
                "The model output did not contain disease-class labels."
            )
        if "model_score" not in ranked_frame.columns:
            ranked_frame["model_score"] = np.nan

        ranked_frame = ranked_frame.head(top_k).copy()
        if "rank" not in ranked_frame.columns:
            ranked_frame.insert(0, "rank", range(1, len(ranked_frame) + 1))
        if "record_number" not in ranked_frame.columns:
            ranked_frame.insert(0, "record_number", 1)
        if "clinical_validation_status" not in ranked_frame.columns:
            ranked_frame["clinical_validation_status"] = (
                metadata.get("clinical_validation_status", "Not clinically validated")
            )

        created_at = datetime.now().isoformat()
        st.session_state["jak_healthcare_predictions"] = {
            "model_key": selected_key,
            "results": prediction_frame,
            "ranked_predictions": ranked_frame,
            "filled_fields": filled_fields,
            "total_fields": len(feature_columns),
            "created_at": created_at,
        }

        history = st.session_state.get(
            "jak_healthcare_prediction_history", []
        )
        history.append({
            "model": selected_key,
            "disease": metadata.get("disease_code"),
            "top_suggestion": str(ranked_frame.iloc[0]["disease"]),
            "filled_fields": filled_fields,
            "created_at": created_at,
        })
        st.session_state["jak_healthcare_prediction_history"] = history[-50:]
        st.success("Analysis completed.")

    except Exception as error:
        st.error(f"Prediction failed: {error}")



def render_prediction_charts(ranked_frame):
    if not isinstance(ranked_frame, pd.DataFrame) or ranked_frame.empty:
        return

    if "model_score" not in ranked_frame.columns:
        st.info("This model returned class labels but no ranked class scores.")
        return

    chart_frame = ranked_frame.copy()
    chart_frame["model_score"] = pd.to_numeric(
        chart_frame["model_score"], errors="coerce"
    )
    chart_frame = chart_frame.dropna(subset=["model_score"])

    if chart_frame.empty:
        st.info(
            "The selected model does not expose class-score values, "
            "so ranked score charts are unavailable."
        )
        return

    st.divider()
    st.subheader("Prediction Visual Analytics")
    chart_frame["disease"] = chart_frame["disease"].astype(str)
    chart_frame["model_score_percent"] = chart_frame["model_score"] * 100

    st.markdown("### Ranked Suggestion Comparison")
    st.bar_chart(
        chart_frame.set_index("disease")[["model_score_percent"]],
        horizontal=True,
        use_container_width=True,
    )

    st.markdown("### Relative Distribution of Displayed Model Scores")
    st.caption(
        "This chart compares scores among the displayed classes. "
        "It is not disease prevalence or a patient's clinical probability."
    )

    pie_data = chart_frame[["disease", "model_score"]].rename(
        columns={"disease": "Disease", "model_score": "Score"}
    )
    pie_spec = {
        "mark": {"type": "arc", "innerRadius": 55, "tooltip": True},
        "encoding": {
            "theta": {"field": "Score", "type": "quantitative"},
            "color": {
                "field": "Disease",
                "type": "nominal",
                "legend": {"orient": "right"},
            },
            "tooltip": [
                {"field": "Disease", "type": "nominal"},
                {"field": "Score", "type": "quantitative", "format": ".4f"},
            ],
        },
        "width": "container",
        "height": 320,
    }
    st.vega_lite_chart(pie_data, pie_spec, use_container_width=True)

    st.markdown("### Model Score Distribution")
    scores = chart_frame["model_score_percent"].dropna()
    if len(scores) >= 2:
        if scores.nunique() == 1:
            histogram = pd.DataFrame({
                "Score": [scores.iloc[0]],
                "Number of Suggestions": [len(scores)],
            }).set_index("Score")
        else:
            bins = min(5, max(2, scores.nunique()))
            categories = pd.cut(scores, bins=bins, include_lowest=True)
            histogram = (
                categories.value_counts()
                .sort_index()
                .rename_axis("Score Range")
                .reset_index(name="Number of Suggestions")
            )
            histogram["Score Range"] = histogram["Score Range"].astype(str)
            histogram = histogram.set_index("Score Range")

        st.bar_chart(histogram, use_container_width=True)

    st.caption(
        "The histogram describes displayed model scores, not disease prevalence."
    )


def render_prediction_results(saved_prediction, selected_key):

    if not saved_prediction:
        return

    if saved_prediction.get("model_key") != selected_key:
        return

    prediction_frame = saved_prediction.get(
        "results"
    )

    ranked_frame = saved_prediction.get(
        "ranked_predictions"
    )

    if not isinstance(prediction_frame, pd.DataFrame):
        return

    if not isinstance(ranked_frame, pd.DataFrame):
        return

    st.divider()

    st.subheader("Disease Suggestion Results")

    filled_fields = saved_prediction.get(
        "filled_fields",
        0,
    )

    total_fields = saved_prediction.get(
        "total_fields",
        0,
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Available Inputs",
            f"{filled_fields}/{total_fields}",
        )

    with col2:

        st.metric(
            "Suggestions Generated",
            len(ranked_frame),
        )

    with col3:

        st.metric(
            "Top Model Suggestion",
            str(ranked_frame.iloc[0]["disease"])
            if not ranked_frame.empty
            else "Unavailable",
        )

    if filled_fields < total_fields:

        st.warning(
            "Some information was not provided. The model "
            "handled missing values automatically. The missing "
            "information may affect the reliability of the results."
        )

    if not ranked_frame.empty:

        first = ranked_frame.iloc[0]

        safe_disease = html.escape(
            str(first["disease"])
        )

        st.markdown(
            f"""
            <div class="jak-prediction-card">

                <div class="jak-prediction-number">
                    TOP-RANKED MODEL SUGGESTION
                </div>

                <div class="jak-prediction-title">
                    {safe_disease}
                </div>

                <p>
                    Model score:
                    {(
                        f"{first['model_score'] * 100:.2f}%"
                        if pd.notna(first.get("model_score"))
                        else "Not supplied by this model"
                    )}
                </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Top Disease Suggestions")

    display_frame = ranked_frame.copy()

    display_frame["model_score"] = (
        pd.to_numeric(display_frame["model_score"], errors="coerce") * 100
    ).round(2)

    display_frame = display_frame.rename(
        columns={
            "record_number": "Record",
            "rank": "Rank",
            "disease": "Suggested Condition",
            "model_score": "Model Score (%)",
            "clinical_validation_status": "Clinical Status",
        }
    )

    st.dataframe(
        display_frame,
        use_container_width=True,
        hide_index=True,
    )

    render_prediction_charts(
        ranked_frame
    )

    st.warning(
        "These are experimental ranked model suggestions, not "
        "confirmed diagnoses. The model scores are not clinically "
        "validated probabilities."
    )

    st.subheader("Download Prediction Report")

    col1, col2 = st.columns(2)

    with col1:

        csv = ranked_frame.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Download Ranked Suggestions",
            data=csv,
            file_name="jak_ranked_disease_suggestions.csv",
            mime="text/csv",
            key="jak_healthcare_ranked_download",
            use_container_width=True,
        )

    with col2:

        summary = prediction_frame.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Download Main Prediction",
            data=summary,
            file_name="jak_healthcare_prediction.csv",
            mime="text/csv",
            key="jak_healthcare_main_download",
            use_container_width=True,
        )


# ==========================================
# SYMPTOM QUESTIONNAIRE
# ==========================================

def render_symptom_questionnaire():

    st.subheader("Patient Symptom Questionnaire")

    st.write(
        "Answer the questions based on the symptoms currently "
        "being experienced. Select Not sure when the answer is unknown."
    )

    questions = get_symptom_questions()

    answers = {}

    selected_model = st.session_state.get(
        SYMPTOM_MODEL_STATE_KEY
    )

    model_features = (
        selected_model.get("feature_columns", [])
        if selected_model
        else SYMPTOM_COLUMNS
    )

    available_questions = [
        question
        for question in questions
        if question["column"] in model_features
    ]

    if not available_questions:

        st.error(
            "The trained model does not contain supported symptom features."
        )

        return

    st.caption(
        f"{len(available_questions)} symptom questions are available "
        "for this trained model."
    )

    answer_options = [
        "Not sure",
        "Yes",
        "No",
    ]

    with st.form("jak_symptom_questionnaire_form"):

        st.markdown("### General Information")

        st.caption(
            "Age and sex are not used by this symptom-only model. "
            "The current model learns from the symptom columns."
        )

        symptom_groups = [
            available_questions[index:index + 8]
            for index in range(0, len(available_questions), 8)
        ]

        for group_number, group in enumerate(symptom_groups):

            with st.expander(
                f"Symptom Questions {group_number + 1}",
                expanded=(group_number == 0),
            ):

                columns = st.columns(2)

                for index, question in enumerate(group):

                    with columns[index % 2]:

                        answer = st.selectbox(
                            question["label"],
                            answer_options,
                            index=0,
                            key=(
                                "jak_symptom_answer_"
                                + question["column"]
                            ),
                        )

                        answers[question["column"]] = answer

        submitted = st.form_submit_button(
            "Analyse Symptoms and Predict",
            type="primary",
            use_container_width=True,
        )

    if submitted:

        try:

            summary = count_symptoms(answers)

            if summary["yes_count"] == 0:

                raise ValueError(
                    "Please answer Yes to at least one symptom "
                    "before requesting an analysis."
                )

            with st.spinner(
                "Analysing symptom combinations..."
            ):

                result = predict_from_symptoms(
                    selected_model,
                    answers,
                    top_k=5,
                )

            urgent_flags = get_urgent_warning_flags(
                answers
            )

            result["urgent_flags"] = urgent_flags

            result["dataset_name"] = (
                selected_model.get(
                    "dataset_name",
                    "Unknown",
                )
            )

            result["answers"] = answers

            st.session_state[
                SYMPTOM_RESULT_STATE_KEY
            ] = result

            history = st.session_state.get(
                SYMPTOM_HISTORY_STATE_KEY,
                [],
            )

            top_result = result["results"].iloc[0]

            history.append({
                "Date": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "Symptoms Selected": summary["yes_count"],
                "Symptoms Denied": summary["no_count"],
                "Unknown Answers": summary["unknown_count"],
                "Top Model Classification": (
                    top_result["Disease label"]
                ),
                "Dataset": result["dataset_name"],
            })

            st.session_state[
                SYMPTOM_HISTORY_STATE_KEY
            ] = history[-100:]

            st.success(
                "Symptom analysis completed."
            )

        except Exception as error:

            st.error(
                f"Symptom analysis failed: {error}"
            )


# ==========================================
# SYMPTOM CHARTS
# ==========================================

def render_symptom_prediction_charts(results):

    if results.empty:
        return

    chart_data = results.copy()

    chart_data["Model score (%)"] = (
        chart_data["Model score"] * 100
    )

    st.subheader("Disease Classification Charts")

    st.markdown("### Ranked Disease Suggestions")

    bar_data = chart_data[
        ["Disease label", "Model score (%)"]
    ].set_index("Disease label")

    st.bar_chart(
        bar_data,
        horizontal=True,
        use_container_width=True,
    )

    st.markdown("### Relative Share of Displayed Model Scores")

    st.caption(
        "This chart compares the displayed model scores. "
        "It does not show disease prevalence or a validated "
        "probability that the patient has a disease."
    )

    pie_data = chart_data[
        ["Disease label", "Model score"]
    ].rename(
        columns={
            "Disease label": "Disease",
            "Model score": "Score",
        }
    )

    pie_spec = {
        "mark": {
            "type": "arc",
            "innerRadius": 50,
            "tooltip": True,
        },
        "encoding": {
            "theta": {
                "field": "Score",
                "type": "quantitative",
            },
            "color": {
                "field": "Disease",
                "type": "nominal",
            },
            "tooltip": [
                {
                    "field": "Disease",
                    "type": "nominal",
                },
                {
                    "field": "Score",
                    "type": "quantitative",
                    "format": ".4f",
                },
            ],
        },
        "width": "container",
        "height": 320,
    }

    st.vega_lite_chart(
        pie_data,
        pie_spec,
        use_container_width=True,
    )

    st.markdown("### Distribution of Model Scores")

    scores = chart_data[
        "Model score (%)"
    ].dropna()

    if len(scores) >= 2:

        histogram = pd.DataFrame({
            "Model score": scores
        })

        histogram["Score range"] = pd.cut(
            histogram["Model score"],
            bins=min(
                5,
                max(2, histogram["Model score"].nunique()),
            ),
            include_lowest=True,
        )

        histogram_data = (
            histogram.groupby(
                "Score range",
                observed=False,
            )
            .size()
            .reset_index(name="Number of disease classes")
        )

        histogram_data["Score range"] = (
            histogram_data["Score range"].astype(str)
        )

        st.bar_chart(
            histogram_data.set_index("Score range"),
            use_container_width=True,
        )


# ==========================================
# RELATED CONDITIONS AND COMPLICATIONS
# ==========================================

def find_registry_entry_for_label(label):

    normalized = str(label).strip().lower()

    for code, disease in DISEASE_REGISTRY.items():

        registered_name = str(
            disease.get("name", "")
        ).strip().lower()

        if normalized == registered_name:
            return code, disease

    return None, None


def render_related_conditions(results):

    st.subheader(
        "Related Conditions and Possible Complications"
    )

    st.caption(
        "This section is informational. It does not predict that "
        "another disease will occur next."
    )

    if results.empty:
        return

    top_label = str(
        results.iloc[0]["Disease label"]
    )

    code, disease = find_registry_entry_for_label(
        top_label
    )

    if not disease:

        st.info(
            "No matching medically reviewed disease-registry entry "
            "is available for the top model classification. "
            "No future disease or complication will be guessed."
        )

        return

    related = disease.get(
        "related_conditions",
        [],
    )

    complications = disease.get(
        "complications",
        [],
    )

    if related:

        st.markdown("**Registered related conditions**")

        for item in related:
            st.write(f"• {item}")

    else:

        st.info(
            "No related conditions have been configured "
            "in the disease registry for this entry."
        )

    if complications:

        st.markdown("**Registered possible complications**")

        for item in complications:
            st.write(f"• {item}")

    else:

        st.info(
            "No medically reviewed complication information "
            "has been configured for this entry."
        )

    st.caption(
        "Related conditions and complications must be checked "
        "against reliable clinical references before being shown "
        "as medical guidance."
    )


# ==========================================
# SYMPTOM RESULTS
# ==========================================

def render_symptom_prediction_results():

    result = st.session_state.get(
        SYMPTOM_RESULT_STATE_KEY
    )

    if not isinstance(result, dict):
        return

    results = result.get(
        "results"
    )

    if not isinstance(results, pd.DataFrame):
        return

    if results.empty:
        return

    st.divider()

    st.header("Symptom Analysis Results")

    summary = result.get(
        "symptom_summary",
        {},
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Yes Answers",
            summary.get("yes_count", 0),
        )

    with col2:

        st.metric(
            "No Answers",
            summary.get("no_count", 0),
        )

    with col3:

        st.metric(
            "Unknown Answers",
            summary.get("unknown_count", 0),
        )

    with col4:

        st.metric(
            "Questions",
            summary.get("total_questions", 0),
        )

    st.markdown("### Symptoms Selected")

    selected = summary.get(
        "present_symptoms",
        [],
    )

    if selected:

        selected_labels = [
            SYMPTOM_LABELS.get(
                symptom,
                symptom.replace("_", " ").title(),
            )
            for symptom in selected
        ]

        st.write(
            ", ".join(selected_labels)
        )

    else:

        st.info(
            "No symptoms were selected."
        )

    st.markdown("### Ranked Disease Classifications")

    display = results.copy()

    display["Model score (%)"] = (
        display["Model score"] * 100
    ).round(2)

    display = display.drop(
        columns=["Model score"],
        errors="ignore",
    )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
    )

    top = results.iloc[0]

    safe_label = html.escape(
        str(top["Disease label"])
    )

    st.markdown(
        f"""
        <div class="jak-prediction-card">

            <div class="jak-prediction-number">
                TOP-RANKED MODEL CLASSIFICATION
            </div>

            <div class="jak-prediction-title">
                {safe_label}
            </div>

            <p>
                Model score:
                {top['Model score'] * 100:.2f}%
            </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "The displayed score is an experimental model score. "
        "It is not a clinically validated probability."
    )

    render_symptom_prediction_charts(
        results
    )

    st.divider()

    render_related_conditions(
        results
    )

    st.divider()

    urgent_flags = result.get(
        "urgent_flags",
        {},
    )

    if urgent_flags.get(
        "urgent_attention_recommended"
    ):

        st.error(
            "URGENT MEDICAL WARNING: One or more warning symptoms "
            "were selected. Seek urgent medical assessment. "
            "Do not wait for a model prediction."
        )

        for symptom in urgent_flags.get(
            "warning_symptoms",
            [],
        ):

            st.write(f"• {symptom}")

    else:

        st.info(
            "No listed urgent warning symptom was selected. "
            "This does not rule out a medical emergency."
        )

    st.warning(
        "JAK Health Intelligence does not diagnose diseases, "
        "predict which disease will develop next, or recommend "
        "treatment. Please consult a qualified healthcare professional."
    )

    st.subheader("Download Symptom Analysis")

    report_data = results.copy()

    report_data["Model score (%)"] = (
        report_data["Model score"] * 100
    )

    report_data = report_data.drop(
        columns=["Model score"],
        errors="ignore",
    )

    st.download_button(
        "Download Disease Suggestions",
        data=report_data.to_csv(
            index=False
        ).encode("utf-8"),
        file_name="jak_symptom_disease_suggestions.csv",
        mime="text/csv",
        key="jak_symptom_results_download",
    )

    symptom_report = pd.DataFrame([
        {
            "Symptom": SYMPTOM_LABELS.get(
                symptom,
                symptom,
            ),
            "Answer": "Yes",
        }
        for symptom in selected
    ])

    st.download_button(
        "Download Selected Symptoms",
        data=symptom_report.to_csv(
            index=False
        ).encode("utf-8"),
        file_name="jak_selected_symptoms.csv",
        mime="text/csv",
        key="jak_symptom_answers_download",
    )


# ==========================================
# SYMPTOM PREDICTION WORKSPACE
# ==========================================

def render_symptom_prediction_workspace():

    render_section_heading(
        "Symptom-Based Disease Prediction",
        "Answer Yes or No to symptoms and analyse their combination.",
    )

    model_bundle = st.session_state.get(
        SYMPTOM_MODEL_STATE_KEY
    )

    saved = get_current_healthcare_dataset()

    if not model_bundle:

        st.warning(
            "You must train a symptom-based model before using "
            "the symptom questionnaire."
        )

        st.info(
            "Open the Train Models tab and use the "
            "Symptom-Based Model Training section."
        )

        return

    if saved:

        if (
            model_bundle.get("dataset_fingerprint")
            != saved.get("fingerprint")
        ):

            st.warning(
                "The active dataset has changed since the symptom "
                "model was trained. Train the model again before "
                "using this dataset."
            )

    metadata = model_bundle.get(
        "metadata",
        {},
    )

    st.success(
        "Symptom model is ready."
    )

    st.write(
        f"**Training dataset:** "
        f"{model_bundle.get('dataset_name', 'Unknown')}"
    )

    st.write(
        f"**Supported symptom inputs:** "
        f"{len(model_bundle.get('feature_columns', []))}"
    )

    st.write(
        f"**Disease classes:** "
        f"{metadata.get('number_of_classes', 0)}"
    )

    st.divider()

    render_symptom_questionnaire()

    render_symptom_prediction_results()


# ==========================================
# GENERAL PREDICTION INTERFACE
# ==========================================


def render_general_disease_prediction():
    render_section_heading(
        "General Disease Prediction Workspace",
        "Generate ranked experimental suggestions using general trained models.",
    )

    models = get_healthcare_models()
    valid_models = {
        key: bundle for key, bundle in models.items()
        if isinstance(bundle, dict)
        and isinstance(bundle.get("metadata"), dict)
        and bundle.get("model") is not None
    }

    if not valid_models:
        symptom_model = st.session_state.get(SYMPTOM_MODEL_STATE_KEY)
        if symptom_model:
            st.info(
                "A symptom-based model is trained, but it is stored separately "
                "from General Disease Models. Use the Symptom Prediction tab, "
                "or train a model under Train Models → General Disease Models."
            )
        else:
            st.info(
                "No general trained healthcare models are available. "
                "Train one under Train Models → General Disease Models."
            )

        with st.expander("Model library diagnostics"):
            st.write("General model count:", len(models))
            st.write("Session state key exists:",
                     "jak_healthcare_models" in st.session_state)
            st.write("Persisted model file:", str(get_model_library_path()))
            st.write("Persisted model file exists:",
                     get_model_library_path().exists())
            st.write("Model keys:", list(models.keys()))
        return

    model_keys = list(valid_models.keys())

    def model_label(key):
        bundle = valid_models[key]
        metadata = bundle.get("metadata", {})
        return (
            f"{metadata.get('disease_code', 'Unknown')} — "
            f"{metadata.get('algorithm', 'Unknown')} — "
            f"{metadata.get('dataset_name', key.split('::')[1] if '::' in key else 'Dataset')}"
        )

    selected_key = st.selectbox(
        "Select trained disease model",
        model_keys,
        format_func=model_label,
        key="jak_healthcare_prediction_model",
    )
    model_bundle = valid_models[selected_key]

    safety = get_medical_model_safety_status(model_bundle)
    if isinstance(safety, dict) and safety.get("disclaimer"):
        st.warning(safety["disclaimer"])
    else:
        st.warning(
            "Experimental output only. This model is not clinically validated."
        )

    metadata = model_bundle.get("metadata", {})
    st.caption(
        f"Training dataset: {metadata.get('dataset_name', 'Unknown')} | "
        f"Target: {metadata.get('target_column', 'Unknown')}"
    )

    render_prediction_form(model_bundle, selected_key)

    saved_prediction = st.session_state.get("jak_healthcare_predictions")
    render_prediction_results(saved_prediction, selected_key)


def render_prediction_history():

    st.subheader("General Prediction History")

    history = st.session_state.get(
        "jak_healthcare_prediction_history",
        [],
    )

    if not history:

        st.info(
            "No general prediction history is available yet."
        )

    else:

        history_frame = pd.DataFrame(
            history
        )

        st.dataframe(
            history_frame,
            use_container_width=True,
            hide_index=True,
        )

        csv = history_frame.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Download General Prediction History",
            data=csv,
            file_name="jak_healthcare_prediction_history.csv",
            mime="text/csv",
            key="jak_healthcare_history_download",
        )

        if st.button(
            "Clear General Prediction History",
            key="jak_healthcare_clear_history",
        ):

            st.session_state[
                "jak_healthcare_prediction_history"
            ] = []

            st.rerun()

    st.divider()

    st.subheader("Symptom Prediction History")

    symptom_history = st.session_state.get(
        SYMPTOM_HISTORY_STATE_KEY,
        [],
    )

    if not symptom_history:

        st.info(
            "No symptom prediction history is available yet."
        )

    else:

        history_frame = pd.DataFrame(
            symptom_history
        )

        st.dataframe(
            history_frame,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download Symptom Prediction History",
            data=history_frame.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="jak_symptom_prediction_history.csv",
            mime="text/csv",
            key="jak_symptom_history_download",
        )

        if st.button(
            "Clear Symptom Prediction History",
            key="jak_symptom_clear_history",
        ):

            st.session_state[
                SYMPTOM_HISTORY_STATE_KEY
            ] = []

            st.session_state[
                SYMPTOM_RESULT_STATE_KEY
            ] = None

            st.rerun()


# ==========================================
# TRAINED MODEL LIBRARY
# ==========================================

def render_healthcare_model_library():

    render_section_heading(
        "Trained Model Library",
        "View experimental healthcare models created in this session.",
    )

    models = get_healthcare_models()

    if not models:

        st.info(
            "No general trained models are currently available."
        )

    else:

        rows = []

        for key, bundle in models.items():

            metadata = bundle.get(
                "metadata",
                {},
            )

            metrics = bundle.get(
                "metrics",
                {},
            )

            parts = key.split("::")

            rows.append({
                "Disease": metadata.get(
                    "disease_code",
                    "Unknown",
                ),
                "Dataset": parts[1]
                if len(parts) > 1
                else "Unknown",
                "Algorithm": metadata.get(
                    "algorithm",
                    "Unknown",
                ),
                "Target": metadata.get(
                    "target_column",
                    "Unknown",
                ),
                "Records": metadata.get(
                    "total_records",
                    0,
                ),
                "Accuracy (%)": round(
                    metrics.get("accuracy", 0) * 100,
                    2,
                ),
                "Clinical Status": metadata.get(
                    "clinical_validation_status",
                    "Unknown",
                ),
                "Trained At": metadata.get(
                    "trained_at",
                    "Unknown",
                ),
            })

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.subheader("Symptom Model")

    symptom_model = st.session_state.get(
        SYMPTOM_MODEL_STATE_KEY
    )

    if symptom_model:

        metadata = symptom_model.get(
            "metadata",
            {},
        )

        metrics = symptom_model.get(
            "metrics",
            {},
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Training Records",
                metadata.get("training_records", 0),
            )

        with col2:

            st.metric(
                "Disease Classes",
                metadata.get("number_of_classes", 0),
            )

        with col3:

            st.metric(
                "Accuracy (%)",
                round(
                    metrics.get("accuracy", 0) * 100,
                    2,
                ),
            )

        st.write(
            f"Dataset: {symptom_model.get('dataset_name', 'Unknown')}"
        )

        st.write(
            f"Features: {len(symptom_model.get('feature_columns', []))}"
        )

        st.write(
            f"Trained at: {metadata.get('trained_at', 'Unknown')}"
        )

        if st.button(
            "Clear Symptom Model",
            key="jak_clear_symptom_model",
        ):

            st.session_state[
                SYMPTOM_MODEL_STATE_KEY
            ] = None

            st.session_state[
                SYMPTOM_RESULT_STATE_KEY
            ] = None

            st.rerun()

    else:

        st.info(
            "No symptom model has been trained yet."
        )

    st.divider()

    st.subheader("General Model Library Management")

    if st.button(
        "Clear General Session Model Library",
        key="jak_healthcare_clear_models",
        type="secondary",
    ):

        st.session_state["jak_healthcare_models"] = {}
        st.session_state["jak_healthcare_model_library"] = {}
        try:
            model_path = get_model_library_path()
            if model_path.exists():
                model_path.unlink()
        except Exception as error:
            st.error(f"Could not remove saved model file: {error}")

        st.session_state.pop(
            "jak_healthcare_last_trained_model",
            None,
        )

        st.session_state[
            "jak_healthcare_predictions"
        ] = None

        st.rerun()


# ==========================================
# MAIN HEALTHCARE PAGE
# ==========================================

def render_healthcare_page():

    initialize_healthcare_state()

    apply_healthcare_design()

    render_healthcare_header()

    st.divider()

    tabs = st.tabs([
        "Overview",
        "Disease Directory",
        "Medical Dataset",
        "Data Validation",
        "Train Models",
        "Symptom Prediction",
        "General Prediction",
        "History",
        "Model Library",
    ])

    with tabs[0]:

        saved_dataset = get_current_healthcare_dataset()

        if saved_dataset:

            render_healthcare_overview()

        else:

            st.info(
                "Welcome to JAK Health Intelligence. "
                "Upload or load a medical dataset to activate "
                "your healthcare overview."
            )

    with tabs[1]:

        render_disease_directory()

    with tabs[2]:

        render_medical_dataset_upload()

    with tabs[3]:

        render_medical_validation()

    with tabs[4]:

        training_tabs = st.tabs([
            "Symptom Model",
            "General Disease Models",
        ])

        with training_tabs[0]:

            render_symptom_model_training()

        with training_tabs[1]:

            render_general_disease_model_training()

    with tabs[5]:

        render_symptom_prediction_workspace()

    with tabs[6]:

        render_general_disease_prediction()

    with tabs[7]:

        render_prediction_history()

    with tabs[8]:

        render_healthcare_model_library()

    st.divider()

    st.warning(
        MEDICAL_DISCLAIMER
    )

    st.warning(
        SYMPTOM_DISCLAIMER
    )

    show_footer()


# ==========================================
# COMPATIBILITY ALIASES
# ==========================================

def render_healthcare():

    render_healthcare_page()


def render_healthcare_dashboard():

    render_healthcare_page()