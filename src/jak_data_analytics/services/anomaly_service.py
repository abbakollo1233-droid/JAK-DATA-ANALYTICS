"""
JAK Data Analytics
Anomaly Detection Service

Provides reusable anomaly detection functionality.

Features:
- Z-Score detection
- IQR detection
- Isolation Forest
- Local Outlier Factor
- One-Class SVM
- Numerical and categorical preprocessing
- Anomaly scoring
- Anomaly summaries
- Detection result comparison

This module does not depend on Streamlit.

Anomaly scores are method-specific and should not
automatically be interpreted as probabilities.
"""

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM


# ==================================================
# VALIDATION
# ==================================================

def validate_dataframe(data):
    """Validate the input dataset."""

    if not isinstance(data, pd.DataFrame):
        raise TypeError(
            "Input must be a pandas DataFrame."
        )

    if data.empty:
        raise ValueError(
            "The dataset is empty."
        )

    if len(data) < 3:
        raise ValueError(
            "At least three rows are required."
        )

    return True


def validate_contamination(contamination):
    """Validate expected anomaly proportion."""

    if not isinstance(contamination, (int, float)):
        raise ValueError(
            "Contamination must be numeric."
        )

    if not 0 < contamination <= 0.5:
        raise ValueError(
            "Contamination must be greater than 0 and at most 0.5."
        )


def validate_features(data, features):
    """Validate selected feature columns."""

    if not features:
        raise ValueError(
            "Select at least one feature column."
        )

    if len(features) != len(set(features)):
        raise ValueError(
            "Duplicate feature columns are not allowed."
        )

    missing = [
        column
        for column in features
        if column not in data.columns
    ]

    if missing:
        raise ValueError(
            f"Unknown columns: {missing}"
        )

    return True


# ==================================================
# PREPARE FEATURES
# ==================================================

def prepare_anomaly_data(
    data,
    features=None,
):
    """
    Prepare numerical and categorical features.

    Numerical:
    - Median imputation
    - Standard scaling

    Categorical:
    - Most frequent imputation
    - One-hot encoding
    """

    validate_dataframe(data)

    if features is None:
        features = data.select_dtypes(
            include=["number", "object", "category", "bool", "string"]
        ).columns.tolist()

    validate_features(
        data,
        features
    )

    selected = data[features].copy()

    numeric_columns = selected.select_dtypes(
        include=np.number
    ).columns.tolist()

    categorical_columns = [
        column
        for column in selected.columns
        if column not in numeric_columns
    ]

    if not numeric_columns and not categorical_columns:
        raise ValueError(
            "No usable numerical or categorical features were found."
        )

    if numeric_columns:

        selected[numeric_columns] = selected[
            numeric_columns
        ].replace(
            [np.inf, -np.inf],
            np.nan
        )

    usable_columns = [
        column
        for column in selected.columns
        if selected[column].notna().any()
    ]

    selected = selected[usable_columns]

    if selected.empty:
        raise ValueError(
            "All selected features contain missing values."
        )

    numeric_columns = selected.select_dtypes(
        include=np.number
    ).columns.tolist()

    categorical_columns = [
        column
        for column in selected.columns
        if column not in numeric_columns
    ]

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
                )
            ),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore"
                )
            ),
        ])

        transformers.append((
            "categorical",
            categorical_pipeline,
            categorical_columns,
        ))

    preprocessor = ColumnTransformer(
        transformers=transformers,
        remainder="drop",
    )

    prepared = preprocessor.fit_transform(
        selected
    )

    if hasattr(prepared, "toarray"):
        prepared = prepared.toarray()

    prepared = np.asarray(
        prepared,
        dtype=float
    )

    if not np.isfinite(prepared).all():
        raise ValueError(
            "Preprocessing produced invalid numerical values."
        )

    if prepared.shape[1] == 0:
        raise ValueError(
            "No usable features remain after preprocessing."
        )

    return {
        "data": selected,
        "prepared_data": prepared,
        "preprocessor": preprocessor,
        "features": usable_columns,
        "numeric_features": numeric_columns,
        "categorical_features": categorical_columns,
    }


# ==================================================
# BUILD RESULT DATAFRAME
# ==================================================

def build_anomaly_results(
    original_data,
    row_indices,
    predictions,
    scores,
    method,
    features,
):
    """Build a standardized anomaly result."""

    result = original_data.loc[
        row_indices
    ].copy()

    result["anomaly_prediction"] = np.where(
        np.asarray(predictions) == -1,
        "Anomaly",
        "Normal",
    )

    result["anomaly_score"] = np.asarray(
        scores,
        dtype=float
    )

    result["detection_method"] = method

    result["selected_features"] = ", ".join(
        features
    )

    return result


# ==================================================
# Z-SCORE DETECTION
# ==================================================

def detect_zscore_anomalies(
    data,
    column,
    threshold=3.0,
):
    """
    Detect outliers using absolute Z-Scores.

    Z-Score measures how far a value is from
    the mean in standard deviation units.
    """

    validate_dataframe(data)

    if column not in data.columns:
        raise ValueError(
            f"Unknown column: {column}"
        )

    if threshold <= 0:
        raise ValueError(
            "Threshold must be greater than zero."
        )

    values = pd.to_numeric(
        data[column],
        errors="coerce"
    )

    values = values.replace(
        [np.inf, -np.inf],
        np.nan
    )

    valid = values.notna()

    clean_values = values[valid]

    if len(clean_values) < 2:
        raise ValueError(
            "At least two valid numerical observations are required."
        )

    mean = clean_values.mean()
    std = clean_values.std(ddof=0)

    if std == 0:
        raise ValueError(
            "Z-Score cannot be calculated for a constant column."
        )

    z_scores = (
        clean_values - mean
    ) / std

    predictions = np.where(
        z_scores.abs() > threshold,
        -1,
        1,
    )

    result = data.loc[
        clean_values.index
    ].copy()

    result["z_score"] = z_scores
    result["anomaly_prediction"] = np.where(
        predictions == -1,
        "Anomaly",
        "Normal",
    )

    result["anomaly_score"] = z_scores.abs()
    result["detection_method"] = "Z-Score"

    return {
        "method": "Z-Score",
        "threshold": threshold,
        "anomaly_count": int(
            (predictions == -1).sum()
        ),
        "normal_count": int(
            (predictions == 1).sum()
        ),
        "results": result,
    }


# ==================================================
# IQR DETECTION
# ==================================================

def detect_iqr_anomalies(
    data,
    column,
    multiplier=1.5,
):
    """Detect outliers using the Interquartile Range method."""

    validate_dataframe(data)

    if column not in data.columns:
        raise ValueError(
            f"Unknown column: {column}"
        )

    if multiplier <= 0:
        raise ValueError(
            "Multiplier must be greater than zero."
        )

    values = pd.to_numeric(
        data[column],
        errors="coerce"
    )

    values = values.replace(
        [np.inf, -np.inf],
        np.nan
    )

    valid = values.notna()

    clean_values = values[valid]

    if clean_values.empty:
        raise ValueError(
            "No valid numerical observations were found."
        )

    q1 = clean_values.quantile(0.25)
    q3 = clean_values.quantile(0.75)

    iqr = q3 - q1

    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr

    predictions = np.where(
        (clean_values < lower)
        | (clean_values > upper),
        -1,
        1,
    )

    distances = np.maximum(
        lower - clean_values,
        0
    ) + np.maximum(
        clean_values - upper,
        0
    )

    result = data.loc[
        clean_values.index
    ].copy()

    result["anomaly_prediction"] = np.where(
        predictions == -1,
        "Anomaly",
        "Normal",
    )

    result["anomaly_score"] = distances
    result["detection_method"] = "IQR"

    return {
        "method": "IQR",
        "lower_bound": float(lower),
        "upper_bound": float(upper),
        "anomaly_count": int(
            (predictions == -1).sum()
        ),
        "normal_count": int(
            (predictions == 1).sum()
        ),
        "results": result,
    }


# ==================================================
# ISOLATION FOREST
# ==================================================

def detect_isolation_forest(
    data,
    features=None,
    contamination=0.05,
    random_state=42,
    n_estimators=200,
):
    """Detect anomalies using Isolation Forest."""

    validate_dataframe(data)

    validate_contamination(
        contamination
    )

    prepared = prepare_anomaly_data(
        data,
        features
    )

    model = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=n_estimators,
        n_jobs=-1,
    )

    predictions = model.fit_predict(
        prepared["prepared_data"]
    )

    scores = -model.decision_function(
        prepared["prepared_data"]
    )

    results = build_anomaly_results(
        data,
        prepared["data"].index,
        predictions,
        scores,
        "Isolation Forest",
        prepared["features"],
    )

    return {
        "method": "Isolation Forest",
        "model": model,
        "preprocessor": prepared["preprocessor"],
        "features": prepared["features"],
        "anomaly_count": int(
            (predictions == -1).sum()
        ),
        "normal_count": int(
            (predictions == 1).sum()
        ),
        "results": results,
    }


# ==================================================
# LOCAL OUTLIER FACTOR
# ==================================================

def detect_local_outlier_factor(
    data,
    features=None,
    contamination=0.05,
    neighbors=20,
):
    """Detect local anomalies using Local Outlier Factor."""

    validate_dataframe(data)

    validate_contamination(
        contamination
    )

    prepared = prepare_anomaly_data(
        data,
        features
    )

    sample_count = len(
        prepared["prepared_data"]
    )

    if not isinstance(neighbors, int) or isinstance(neighbors, bool):
        raise ValueError(
            "Number of neighbors must be an integer."
        )

    if not 1 <= neighbors < sample_count:
        raise ValueError(
            "Neighbors must be at least 1 and smaller than the sample count."
        )

    model = LocalOutlierFactor(
        n_neighbors=neighbors,
        contamination=contamination,
        novelty=False,
    )

    predictions = model.fit_predict(
        prepared["prepared_data"]
    )

    scores = -model.negative_outlier_factor_

    results = build_anomaly_results(
        data,
        prepared["data"].index,
        predictions,
        scores,
        "Local Outlier Factor",
        prepared["features"],
    )

    return {
        "method": "Local Outlier Factor",
        "model": model,
        "preprocessor": prepared["preprocessor"],
        "features": prepared["features"],
        "anomaly_count": int(
            (predictions == -1).sum()
        ),
        "normal_count": int(
            (predictions == 1).sum()
        ),
        "results": results,
    }


# ==================================================
# ONE-CLASS SVM
# ==================================================

def detect_one_class_svm(
    data,
    features=None,
    contamination=0.05,
    kernel="rbf",
    gamma="scale",
):
    """Detect anomalies using One-Class SVM."""

    validate_dataframe(data)

    validate_contamination(
        contamination
    )

    if kernel not in [
        "linear",
        "poly",
        "rbf",
        "sigmoid",
    ]:
        raise ValueError(
            "Unsupported SVM kernel."
        )

    prepared = prepare_anomaly_data(
        data,
        features
    )

    model = OneClassSVM(
        kernel=kernel,
        gamma=gamma,
        nu=contamination,
    )

    predictions = model.fit_predict(
        prepared["prepared_data"]
    )

    scores = -model.decision_function(
        prepared["prepared_data"]
    )

    results = build_anomaly_results(
        data,
        prepared["data"].index,
        predictions,
        scores,
        "One-Class SVM",
        prepared["features"],
    )

    return {
        "method": "One-Class SVM",
        "model": model,
        "preprocessor": prepared["preprocessor"],
        "features": prepared["features"],
        "anomaly_count": int(
            (predictions == -1).sum()
        ),
        "normal_count": int(
            (predictions == 1).sum()
        ),
        "results": results,
    }


# ==================================================
# ANOMALY SUMMARY
# ==================================================

def summarize_anomalies(results):
    """Generate a summary of anomaly detection results."""

    if not isinstance(results, pd.DataFrame):
        raise TypeError(
            "Results must be a pandas DataFrame."
        )

    if "anomaly_prediction" not in results.columns:
        raise ValueError(
            "Anomaly prediction column is missing."
        )

    total = len(results)

    anomalies = int(
        (
            results["anomaly_prediction"] == "Anomaly"
        ).sum()
    )

    normal = total - anomalies

    return {
        "total_records": total,
        "anomaly_count": anomalies,
        "normal_count": normal,
        "anomaly_percentage": round(
            anomalies / total * 100,
            2
        ) if total else 0,
        "normal_percentage": round(
            normal / total * 100,
            2
        ) if total else 0,
    }


# ==================================================
# COMPARE DETECTION RESULTS
# ==================================================

def compare_detection_methods(
    detection_results,
):
    """
    Compare multiple anomaly detection results.

    detection_results must be a dictionary:
    {
        "Isolation Forest": result_dataframe,
        "Local Outlier Factor": result_dataframe
    }
    """

    if not isinstance(detection_results, dict):
        raise TypeError(
            "Detection results must be a dictionary."
        )

    if not detection_results:
        raise ValueError(
            "No detection results were provided."
        )

    summaries = []

    for method, results in detection_results.items():

        summary = summarize_anomalies(
            results
        )

        summaries.append({
            "method": method,
            **summary,
        })

    return pd.DataFrame(
        summaries
    )


# ==================================================
# EXTRACT ANOMALY RECORDS
# ==================================================

def get_anomaly_records(results):
    """Return only records classified as anomalies."""

    if not isinstance(results, pd.DataFrame):
        raise TypeError(
            "Results must be a pandas DataFrame."
        )

    if "anomaly_prediction" not in results.columns:
        raise ValueError(
            "Anomaly prediction column is missing."
        )

    return results.loc[
        results["anomaly_prediction"] == "Anomaly"
    ].copy()


# ==================================================
# EXPORT RESULTS
# ==================================================

def export_anomaly_results(
    results,
    file_path,
):
    """Export anomaly results to CSV."""

    if not isinstance(results, pd.DataFrame):
        raise TypeError(
            "Results must be a pandas DataFrame."
        )

    if results.empty:
        raise ValueError(
            "There are no results to export."
        )

    results.to_csv(
        file_path,
        index=False
    )

    return str(file_path)