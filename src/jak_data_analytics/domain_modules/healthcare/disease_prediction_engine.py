"""
JAK Health Intelligence
Disease Prediction Engine

Features:
- Random Forest classification
- Logistic Regression classification
- Numeric and categorical preprocessing
- Missing-value handling
- Model evaluation
- Partial-information prediction
- Top disease suggestions
- Ranked prediction scores
- Chart-ready prediction results

IMPORTANT:
This engine provides experimental machine-learning outputs.
It does not provide confirmed medical diagnoses.
"""

import inspect
import numpy as np
import pandas as pd

from datetime import datetime, timezone

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler,
    LabelEncoder,
)

from sklearn.model_selection import train_test_split

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)


# ==========================================
# ENGINE CONFIGURATION
# ==========================================

ENGINE_NAME = "JAK Health Intelligence"

ENGINE_VERSION = "2.0"

SUPPORTED_ALGORITHMS = [
    "random_forest",
    "logistic_regression",
]

DEFAULT_TOP_K = 5

MEDICAL_DISCLAIMER = (
    "This is an experimental machine-learning result, "
    "not a confirmed medical diagnosis. It must not replace "
    "professional medical assessment, laboratory testing "
    "or clinical judgement."
)


# ==========================================
# DATASET VALIDATION
# ==========================================

def validate_training_dataset(dataframe, target_column):

    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError(
            "Training data must be a pandas DataFrame."
        )

    if dataframe.empty:
        raise ValueError(
            "The medical dataset is empty."
        )

    if dataframe.columns.duplicated().any():
        raise ValueError(
            "The dataset contains duplicate column names."
        )

    if target_column not in dataframe.columns:
        raise ValueError(
            f"Target column '{target_column}' was not found."
        )

    if dataframe[target_column].isna().any():
        raise ValueError(
            "The target column contains missing values."
        )

    if dataframe[target_column].nunique() < 2:
        raise ValueError(
            "At least two target classes are required."
        )

    if len(dataframe) < 20:
        raise ValueError(
            "At least 20 records are required for this "
            "experimental training workflow."
        )

    return True


# ==========================================
# FEATURE PREPARATION
# ==========================================

def prepare_features(
    dataframe,
    target_column,
    feature_columns=None,
):

    if feature_columns is None:

        feature_columns = [
            column
            for column in dataframe.columns
            if column != target_column
        ]

    if not feature_columns:
        raise ValueError(
            "Select at least one feature column."
        )

    if target_column in feature_columns:
        raise ValueError(
            "The target column cannot also be a feature."
        )

    missing_columns = [
        column
        for column in feature_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing feature columns: "
            + ", ".join(missing_columns)
        )

    X = dataframe[feature_columns].copy()

    y = dataframe[target_column].copy()

    empty_columns = [
        column
        for column in X.columns
        if X[column].isna().all()
    ]

    if empty_columns:

        X = X.drop(
            columns=empty_columns
        )

        feature_columns = [
            column
            for column in feature_columns
            if column not in empty_columns
        ]

    if X.empty:
        raise ValueError(
            "No usable feature columns remain."
        )

    unsupported = [
        column
        for column in X.columns
        if not (
            pd.api.types.is_numeric_dtype(X[column])
            or pd.api.types.is_object_dtype(X[column])
            or pd.api.types.is_string_dtype(X[column])
            or isinstance(
                X[column].dtype,
                pd.CategoricalDtype,
            )
            or pd.api.types.is_bool_dtype(X[column])
        )
    ]

    if unsupported:
        raise ValueError(
            "Unsupported feature types: "
            + ", ".join(unsupported)
        )

    return X, y, feature_columns


# ==========================================
# ONE HOT ENCODER
# ==========================================

def create_one_hot_encoder():

    parameters = inspect.signature(
        OneHotEncoder
    ).parameters

    if "sparse_output" in parameters:

        return OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=True,
        )

    return OneHotEncoder(
        handle_unknown="ignore",
        sparse=True,
    )


# ==========================================
# PREPROCESSING
# ==========================================

def create_preprocessor(X):

    numeric_columns = [
        column
        for column in X.columns
        if pd.api.types.is_numeric_dtype(X[column])
        and not pd.api.types.is_bool_dtype(X[column])
    ]

    categorical_columns = [
        column
        for column in X.columns
        if column not in numeric_columns
    ]

    transformers = []

    if numeric_columns:

        numeric_pipeline = Pipeline([
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                ),
            ),
            (
                "scaler",
                StandardScaler(),
            ),
        ])

        transformers.append((
            "numeric",
            numeric_pipeline,
            numeric_columns,
        ))

    if categorical_columns:

        categorical_pipeline = Pipeline([
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                ),
            ),
            (
                "encoder",
                create_one_hot_encoder(),
            ),
        ])

        transformers.append((
            "categorical",
            categorical_pipeline,
            categorical_columns,
        ))

    if not transformers:
        raise ValueError(
            "No supported features were found."
        )

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop",
    )


# ==========================================
# CLASSIFIER
# ==========================================

def create_classifier(
    algorithm="random_forest",
    random_state=42,
):

    if algorithm == "random_forest":

        return RandomForestClassifier(
            n_estimators=300,
            max_depth=None,
            min_samples_split=2,
            min_samples_leaf=1,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
        )

    if algorithm == "logistic_regression":

        return LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=random_state,
        )

    raise ValueError(
        f"Unsupported algorithm: {algorithm}"
    )


# ==========================================
# CLASS DISTRIBUTION
# ==========================================

def validate_class_distribution(y):

    counts = y.value_counts()

    if len(counts) < 2:
        raise ValueError(
            "At least two classes are required."
        )

    rare_classes = counts[counts < 2]

    if not rare_classes.empty:

        details = ", ".join(
            f"{label}: {count}"
            for label, count in rare_classes.items()
        )

        raise ValueError(
            "Every class needs at least two records. "
            f"Insufficient classes: {details}"
        )

    return counts


# ==========================================
# MODEL TRAINING
# ==========================================

def train_disease_model(
    dataframe,
    disease_code,
    target_column,
    feature_columns=None,
    algorithm="random_forest",
    test_size=0.20,
    random_state=42,
):

    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(
            "Unsupported algorithm selected."
        )

    if not 0.10 <= test_size <= 0.40:
        raise ValueError(
            "Test size must be between 10% and 40%."
        )

    validate_training_dataset(
        dataframe,
        target_column,
    )

    X, y, feature_columns = prepare_features(
        dataframe,
        target_column,
        feature_columns,
    )

    class_counts = validate_class_distribution(y)

    label_encoder = LabelEncoder()

    y_encoded = label_encoder.fit_transform(y)

    number_of_classes = len(
        label_encoder.classes_
    )

    test_records = int(
        np.ceil(len(X) * test_size)
    )

    training_records = len(X) - test_records

    if test_records < number_of_classes:
        raise ValueError(
            "The test set is too small to represent "
            "every class. Increase the test percentage "
            "or provide more records."
        )

    if training_records < number_of_classes:
        raise ValueError(
            "The training set is too small."
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y_encoded,
        test_size=test_size,
        random_state=random_state,
        stratify=y_encoded,
    )

    preprocessor = create_preprocessor(
        X_train
    )

    classifier = create_classifier(
        algorithm,
        random_state,
    )

    model = Pipeline([
        (
            "preprocessor",
            preprocessor,
        ),
        (
            "classifier",
            classifier,
        ),
    ])

    model.fit(
        X_train,
        y_train,
    )

    predictions = model.predict(
        X_test
    )

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    balanced_accuracy = balanced_accuracy_score(
        y_test,
        predictions,
    )

    precision = precision_score(
        y_test,
        predictions,
        average="weighted",
        zero_division=0,
    )

    recall = recall_score(
        y_test,
        predictions,
        average="weighted",
        zero_division=0,
    )

    f1 = f1_score(
        y_test,
        predictions,
        average="weighted",
        zero_division=0,
    )

    matrix = confusion_matrix(
        y_test,
        predictions,
    )

    report = classification_report(
        y_test,
        predictions,
        labels=np.arange(number_of_classes),
        target_names=[
            str(label)
            for label in label_encoder.classes_
        ],
        output_dict=True,
        zero_division=0,
    )

    metadata = {
        "engine": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
        "disease_code": disease_code,
        "target_column": target_column,
        "feature_columns": feature_columns,
        "algorithm": algorithm,
        "total_records": int(len(X)),
        "training_records": int(len(X_train)),
        "testing_records": int(len(X_test)),
        "number_of_classes": int(number_of_classes),
        "class_labels": [
            str(label)
            for label in label_encoder.classes_
        ],
        "class_distribution": {
            str(label): int(count)
            for label, count in class_counts.items()
        },
        "test_size": float(test_size),
        "random_state": int(random_state),
        "trained_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "clinical_validation_status": "not_clinically_validated",
    }

    metrics = {
        "accuracy": float(accuracy),
        "balanced_accuracy": float(balanced_accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "confusion_matrix": matrix.tolist(),
        "classification_report": report,
    }

    return {
        "model": model,
        "label_encoder": label_encoder,
        "metadata": metadata,
        "metrics": metrics,
        "disclaimer": MEDICAL_DISCLAIMER,
        "status": "experimental",
    }


# ==========================================
# PREDICTION INPUT PREPARATION
# ==========================================

def prepare_prediction_data(
    records,
    feature_columns,
):

    if isinstance(records, dict):

        records = pd.DataFrame([
            records
        ])

    elif isinstance(records, pd.Series):

        records = pd.DataFrame([
            records
        ])

    elif not isinstance(records, pd.DataFrame):

        raise TypeError(
            "Prediction input must be a dictionary, "
            "Series or DataFrame."
        )

    if records.empty:
        raise ValueError(
            "No prediction records were provided."
        )

    # Keep only model features.
    # Missing fields are filled with NaN so that the
    # trained preprocessing pipeline can handle them.

    X = records.reindex(
        columns=feature_columns
    ).copy()

    if X.isna().all(axis=1).any():

        completely_empty = X.isna().all(
            axis=1
        )

        if completely_empty.any():

            raise ValueError(
                "At least one usable input field is required "
                "for every prediction record."
            )

    return X


# ==========================================
# RANKED DISEASE PREDICTIONS
# ==========================================

def predict_disease_model(
    model_bundle,
    records,
    top_k=DEFAULT_TOP_K,
):
    """
    Generate ranked experimental predictions.

    Returns:
        predictions:
            One predicted class per record.

        ranked_predictions:
            Top-k ranked classes per record.

        chart_data:
            Data suitable for charts.

    Scores are model outputs, not clinically validated
    probabilities of having a disease.
    """

    if not isinstance(model_bundle, dict):
        raise TypeError(
            "Invalid model bundle."
        )

    required_keys = [
        "model",
        "label_encoder",
        "metadata",
    ]

    for key in required_keys:

        if key not in model_bundle:

            raise ValueError(
                f"Model bundle is missing: {key}"
            )

    if model_bundle.get("status") != "experimental":

        raise ValueError(
            "This model is not available for prediction."
        )

    try:

        top_k = int(top_k)

    except (TypeError, ValueError):

        raise ValueError(
            "top_k must be a valid integer."
        )

    if top_k < 1:
        raise ValueError(
            "top_k must be at least 1."
        )

    feature_columns = model_bundle[
        "metadata"
    ]["feature_columns"]

    X = prepare_prediction_data(
        records,
        feature_columns,
    )

    model = model_bundle["model"]

    label_encoder = model_bundle["label_encoder"]

    encoded_predictions = model.predict(X)

    predicted_labels = label_encoder.inverse_transform(
        encoded_predictions.astype(int)
    )

    predictions = pd.DataFrame({
        "predicted_class": predicted_labels,
    }, index=X.index)

    predictions["clinical_validation_status"] = (
        "not_clinically_validated"
    )

    ranked_rows = []

    classifier = model.named_steps["classifier"]

    if not hasattr(model, "predict_proba"):

        raise ValueError(
            "This model does not support prediction scores."
        )

    probabilities = model.predict_proba(X)

    classes = label_encoder.classes_

    number_of_suggestions = min(
        top_k,
        len(classes),
    )

    for record_position in range(len(X)):

        row_scores = probabilities[
            record_position
        ]

        sorted_positions = np.argsort(
            row_scores
        )[::-1]

        for rank, class_position in enumerate(
            sorted_positions[:number_of_suggestions],
            start=1,
        ):

            disease_name = str(
                classes[class_position]
            )

            score = float(
                row_scores[class_position]
            )

            ranked_rows.append({
                "record_number": record_position + 1,
                "rank": rank,
                "disease": disease_name,
                "model_score": score,
                "clinical_validation_status": (
                    "not_clinically_validated"
                ),
            })

    ranked_predictions = pd.DataFrame(
        ranked_rows
    )

    chart_data = ranked_predictions.copy()

    return {
        "predictions": predictions,
        "ranked_predictions": ranked_predictions,
        "chart_data": chart_data,
        "disclaimer": MEDICAL_DISCLAIMER,
        "status": "experimental",
    }


# ==========================================
# MODEL INFORMATION
# ==========================================

def get_model_information(model_bundle):

    if not isinstance(model_bundle, dict):
        raise TypeError(
            "Invalid model bundle."
        )

    return {
        "metadata": model_bundle.get(
            "metadata",
            {},
        ),
        "metrics": model_bundle.get(
            "metrics",
            {},
        ),
        "status": model_bundle.get(
            "status",
            "unknown",
        ),
        "disclaimer": model_bundle.get(
            "disclaimer",
            MEDICAL_DISCLAIMER,
        ),
    }


# ==========================================
# MODEL COMPARISON
# ==========================================

def compare_disease_models(model_bundles):

    if not model_bundles:
        raise ValueError(
            "No trained models were supplied."
        )

    rows = []

    for bundle in model_bundles:

        metadata = bundle.get(
            "metadata",
            {},
        )

        metrics = bundle.get(
            "metrics",
            {},
        )

        rows.append({
            "Disease": metadata.get(
                "disease_code",
                "Unknown",
            ),
            "Algorithm": metadata.get(
                "algorithm",
                "Unknown",
            ),
            "Accuracy": metrics.get(
                "accuracy",
                np.nan,
            ),
            "Balanced Accuracy": metrics.get(
                "balanced_accuracy",
                np.nan,
            ),
            "Precision": metrics.get(
                "precision",
                np.nan,
            ),
            "Recall": metrics.get(
                "recall",
                np.nan,
            ),
            "F1 Score": metrics.get(
                "f1_score",
                np.nan,
            ),
            "Clinical Validation": metadata.get(
                "clinical_validation_status",
                "unknown",
            ),
        })

    return pd.DataFrame(rows)


# ==========================================
# MEDICAL MODEL SAFETY
# ==========================================

def get_medical_model_safety_status(model_bundle):

    if not isinstance(model_bundle, dict):
        model_bundle = {}

    metadata = model_bundle.get(
        "metadata",
        {},
    )

    return {
        "trained": (
            model_bundle.get("status") == "experimental"
        ),
        "clinical_validation_status": metadata.get(
            "clinical_validation_status",
            "not_clinically_validated",
        ),
        "approved_for_clinical_diagnosis": False,
        "disclaimer": MEDICAL_DISCLAIMER,
    }