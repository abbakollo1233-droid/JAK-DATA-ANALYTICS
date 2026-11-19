"""
JAK Data Analytics
Machine Learning Service

Provides reusable machine learning functionality.

Features:
- Classification
- Regression
- Clustering
- Data preprocessing
- Missing value handling
- Categorical encoding
- Feature scaling
- Model training
- Model evaluation
- Predictions
- Feature importance

This module does not depend on Streamlit.

Models are returned in memory. Persistent model storage
will be implemented separately.
"""

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

from sklearn.model_selection import train_test_split

from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor,
    GradientBoostingClassifier,
    GradientBoostingRegressor,
)

from sklearn.cluster import KMeans

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    silhouette_score,
)


# ==================================================
# VALIDATION
# ==================================================

def validate_dataframe(data):
    """Validate a machine learning dataset."""

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


def validate_features(data, features):
    """Validate selected feature columns."""

    if not features:
        raise ValueError(
            "At least one feature is required."
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
            f"Unknown feature columns: {missing}"
        )

    return True


def clean_infinite_values(data):
    """Replace infinite numerical values with missing values."""

    cleaned = data.copy()

    numeric_columns = cleaned.select_dtypes(
        include=np.number
    ).columns

    cleaned[numeric_columns] = cleaned[
        numeric_columns
    ].replace(
        [np.inf, -np.inf],
        np.nan
    )

    return cleaned


# ==================================================
# PREPROCESSING
# ==================================================

def build_preprocessor(data):
    """
    Build preprocessing pipeline.

    Numerical columns:
    - Median imputation
    - Standard scaling

    Categorical columns:
    - Most frequent imputation
    - One-hot encoding
    """

    numeric_columns = data.select_dtypes(
        include=np.number
    ).columns.tolist()

    categorical_columns = data.select_dtypes(
        exclude=np.number
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
            ),
        ])

        transformers.append(
            (
                "numeric",
                numeric_pipeline,
                numeric_columns,
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
            ),
        ])

        transformers.append(
            (
                "categorical",
                categorical_pipeline,
                categorical_columns,
            )
        )

    if not transformers:
        raise ValueError(
            "No usable feature columns were found."
        )

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop",
    )


# ==================================================
# MODEL SELECTION
# ==================================================

def get_classification_model(
    algorithm="Random Forest",
    random_state=42,
):
    """Return a classification model."""

    models = {
        "Logistic Regression": LogisticRegression(
            max_iter=2000,
            random_state=random_state,
        ),

        "Decision Tree": DecisionTreeClassifier(
            random_state=random_state,
        ),

        "Random Forest": RandomForestClassifier(
            n_estimators=200,
            random_state=random_state,
            n_jobs=-1,
        ),

        "Gradient Boosting": GradientBoostingClassifier(
            random_state=random_state,
        ),
    }

    if algorithm not in models:
        raise ValueError(
            f"Unsupported classification algorithm: {algorithm}"
        )

    return models[algorithm]


def get_regression_model(
    algorithm="Random Forest",
    random_state=42,
):
    """Return a regression model."""

    models = {
        "Linear Regression": LinearRegression(),

        "Decision Tree": DecisionTreeRegressor(
            random_state=random_state,
        ),

        "Random Forest": RandomForestRegressor(
            n_estimators=200,
            random_state=random_state,
            n_jobs=-1,
        ),

        "Gradient Boosting": GradientBoostingRegressor(
            random_state=random_state,
        ),
    }

    if algorithm not in models:
        raise ValueError(
            f"Unsupported regression algorithm: {algorithm}"
        )

    return models[algorithm]


# ==================================================
# PREPARE TRAINING DATA
# ==================================================

def prepare_training_data(
    data,
    target,
    features=None,
):
    """Prepare features and target for training."""

    validate_dataframe(data)

    if target not in data.columns:
        raise ValueError(
            f"Target column '{target}' does not exist."
        )

    if features is None:
        features = [
            column
            for column in data.columns
            if column != target
        ]

    validate_features(data, features)

    if target in features:
        raise ValueError(
            "Target column cannot also be a feature."
        )

    cleaned = clean_infinite_values(
        data[features + [target]]
    )

    cleaned = cleaned.dropna(
        subset=[target]
    )

    if cleaned.empty:
        raise ValueError(
            "No valid target values remain."
        )

    X = cleaned[features].copy()
    y = cleaned[target].copy()

    usable_features = [
        column
        for column in X.columns
        if X[column].notna().any()
    ]

    X = X[usable_features]

    if X.empty:
        raise ValueError(
            "All selected feature columns contain missing values."
        )

    constant_columns = [
        column
        for column in X.columns
        if X[column].nunique(dropna=True) <= 1
    ]

    X = X.drop(
        columns=constant_columns
    )

    if X.empty:
        raise ValueError(
            "No varying feature columns remain."
        )

    return X, y


# ==================================================
# CLASSIFICATION TRAINING
# ==================================================

def train_classification_model(
    data,
    target,
    features=None,
    algorithm="Random Forest",
    test_size=0.2,
    random_state=42,
):
    """Train and evaluate a classification model."""

    if not 0.1 <= test_size <= 0.5:
        raise ValueError(
            "Test size must be between 0.1 and 0.5."
        )

    X, y = prepare_training_data(
        data,
        target,
        features,
    )

    if y.nunique() < 2:
        raise ValueError(
            "Classification requires at least two target classes."
        )

    if y.nunique() > 100:
        raise ValueError(
            "The target has too many unique classes for this classification workflow."
        )

    if y.value_counts().min() < 2:
        raise ValueError(
            "Each class must contain at least two observations."
        )

    stratify = y if (
        y.value_counts().min() >= 2
        and int(np.ceil(len(y) * test_size)) >= y.nunique()
    ) else None

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify,
    )

    preprocessor = build_preprocessor(
        X_train
    )

    model = get_classification_model(
        algorithm,
        random_state,
    )

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", model),
    ])

    pipeline.fit(
        X_train,
        y_train,
    )

    predictions = pipeline.predict(
        X_test
    )

    metrics = {
        "accuracy": float(
            accuracy_score(y_test, predictions)
        ),

        "precision_weighted": float(
            precision_score(
                y_test,
                predictions,
                average="weighted",
                zero_division=0,
            )
        ),

        "recall_weighted": float(
            recall_score(
                y_test,
                predictions,
                average="weighted",
                zero_division=0,
            )
        ),

        "f1_weighted": float(
            f1_score(
                y_test,
                predictions,
                average="weighted",
                zero_division=0,
            )
        ),
    }

    return {
        "task": "classification",
        "algorithm": algorithm,
        "target": target,
        "features": X.columns.tolist(),
        "model": pipeline,
        "metrics": metrics,
        "confusion_matrix": confusion_matrix(
            y_test,
            predictions,
        ).tolist(),
        "classification_report": classification_report(
            y_test,
            predictions,
            output_dict=True,
            zero_division=0,
        ),
        "actual_values": y_test.tolist(),
        "predictions": predictions.tolist(),
        "training_rows": len(X_train),
        "testing_rows": len(X_test),
        "classes": pd.Series(y).unique().tolist(),
    }


# ==================================================
# REGRESSION TRAINING
# ==================================================

def train_regression_model(
    data,
    target,
    features=None,
    algorithm="Random Forest",
    test_size=0.2,
    random_state=42,
):
    """Train and evaluate a regression model."""

    if not 0.1 <= test_size <= 0.5:
        raise ValueError(
            "Test size must be between 0.1 and 0.5."
        )

    X, y = prepare_training_data(
        data,
        target,
        features,
    )

    y = pd.to_numeric(
        y,
        errors="coerce"
    )

    valid = y.notna() & np.isfinite(y)

    X = X.loc[valid]
    y = y.loc[valid]

    if len(y) < 3:
        raise ValueError(
            "At least three valid target values are required."
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
    )

    if len(X_test) < 2:
        raise ValueError(
            "The test dataset must contain at least two rows."
        )

    preprocessor = build_preprocessor(
        X_train
    )

    model = get_regression_model(
        algorithm,
        random_state,
    )

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", model),
    ])

    pipeline.fit(
        X_train,
        y_train,
    )

    predictions = pipeline.predict(
        X_test
    )

    mse = mean_squared_error(
        y_test,
        predictions
    )

    metrics = {
        "mae": float(
            mean_absolute_error(
                y_test,
                predictions
            )
        ),

        "mse": float(mse),

        "rmse": float(
            np.sqrt(mse)
        ),

        "r2": float(
            r2_score(
                y_test,
                predictions
            )
        ),
    }

    return {
        "task": "regression",
        "algorithm": algorithm,
        "target": target,
        "features": X.columns.tolist(),
        "model": pipeline,
        "metrics": metrics,
        "actual_values": y_test.tolist(),
        "predictions": predictions.tolist(),
        "training_rows": len(X_train),
        "testing_rows": len(X_test),
    }


# ==================================================
# CLUSTERING
# ==================================================

def train_clustering_model(
    data,
    features=None,
    clusters=3,
    random_state=42,
):
    """Train a K-Means clustering model."""

    validate_dataframe(data)

    if features is None:
        features = data.select_dtypes(
            include=np.number
        ).columns.tolist()

    validate_features(
        data,
        features
    )

    if not isinstance(clusters, int) or isinstance(clusters, bool):
        raise ValueError(
            "Number of clusters must be an integer."
        )

    if clusters < 2:
        raise ValueError(
            "At least two clusters are required."
        )

    cleaned = clean_infinite_values(
        data[features]
    )

    usable_features = [
        column
        for column in cleaned.columns
        if cleaned[column].notna().any()
    ]

    cleaned = cleaned[usable_features]

    if cleaned.empty:
        raise ValueError(
            "No usable feature columns remain."
        )

    cleaned = cleaned.dropna(
        how="all"
    )

    if len(cleaned) <= clusters:
        raise ValueError(
            "Number of clusters must be smaller than the number of usable rows."
        )

    preprocessor = build_preprocessor(
        cleaned
    )

    prepared = preprocessor.fit_transform(
        cleaned
    )

    if hasattr(prepared, "toarray"):
        prepared = prepared.toarray()

    model = KMeans(
        n_clusters=clusters,
        random_state=random_state,
        n_init=10,
    )

    labels = model.fit_predict(
        prepared
    )

    score = None

    unique_labels = np.unique(labels)

    if 1 < len(unique_labels) < len(labels):
        score = float(
            silhouette_score(
                prepared,
                labels,
                sample_size=min(
                    len(labels),
                    5000
                ),
                random_state=random_state,
            )
        )

    result_data = data.loc[
        cleaned.index
    ].copy()

    result_data["cluster"] = labels

    return {
        "task": "clustering",
        "algorithm": "K-Means",
        "features": usable_features,
        "model": model,
        "preprocessor": preprocessor,
        "cluster_count": clusters,
        "silhouette_score": score,
        "labels": labels.tolist(),
        "cluster_sizes": pd.Series(
            labels
        ).value_counts().sort_index().to_dict(),
        "results": result_data,
    }


# ==================================================
# GENERATE PREDICTIONS
# ==================================================

def generate_predictions(
    trained_model,
    new_data,
):
    """Generate predictions using a trained pipeline."""

    if not isinstance(trained_model, Pipeline):
        raise TypeError(
            "A trained scikit-learn Pipeline is required."
        )

    if not isinstance(new_data, pd.DataFrame):
        raise TypeError(
            "Prediction input must be a pandas DataFrame."
        )

    if new_data.empty:
        raise ValueError(
            "Prediction dataset is empty."
        )

    return trained_model.predict(
        new_data
    )


# ==================================================
# CLASS PROBABILITIES
# ==================================================

def generate_class_probabilities(
    trained_model,
    new_data,
):
    """Generate class probabilities when supported."""

    if not hasattr(
        trained_model,
        "predict_proba"
    ):
        raise ValueError(
            "This model does not support probability predictions."
        )

    probabilities = trained_model.predict_proba(
        new_data
    )

    model = trained_model.named_steps.get(
        "model"
    )

    classes = getattr(
        model,
        "classes_",
        None
    )

    return {
        "classes": (
            classes.tolist()
            if classes is not None
            else []
        ),
        "probabilities": probabilities.tolist(),
    }


# ==================================================
# FEATURE IMPORTANCE
# ==================================================

def get_feature_importance(
    trained_model,
):
    """Extract feature importance or coefficients when available."""

    if not isinstance(trained_model, Pipeline):
        raise TypeError(
            "A trained scikit-learn Pipeline is required."
        )

    model = trained_model.named_steps.get(
        "model"
    )

    if model is None:
        raise ValueError(
            "The pipeline does not contain a model step."
        )

    preprocessor = trained_model.named_steps.get(
        "preprocessor"
    )

    try:
        feature_names = preprocessor.get_feature_names_out()
    except Exception:
        feature_names = [
            f"Feature {index + 1}"
            for index in range(
                len(model.feature_importances_)
                if hasattr(model, "feature_importances_")
                else len(model.coef_.ravel())
            )
        ]

    if hasattr(model, "feature_importances_"):

        importance = model.feature_importances_

    elif hasattr(model, "coef_"):

        coefficients = np.asarray(
            model.coef_
        )

        if coefficients.ndim == 1:
            importance = np.abs(coefficients)
        else:
            importance = np.abs(
                coefficients
            ).mean(axis=0)

    else:
        raise ValueError(
            "This algorithm does not provide feature importance or coefficients."
        )

    if len(feature_names) != len(importance):
        raise ValueError(
            "Feature importance dimensions do not match."
        )

    result = pd.DataFrame({
        "feature": feature_names,
        "importance": importance,
    })

    return result.sort_values(
        "importance",
        ascending=False
    ).reset_index(drop=True)