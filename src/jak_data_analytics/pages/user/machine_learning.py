"""
JAK Data Analytics
Machine Learning Module

Supports:
- Classification
- Regression
- Clustering
- Model evaluation
- Confusion matrix
- Classification report
- Model comparison-ready results
- Cluster analysis

Uses native Streamlit components.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from datetime import datetime

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer

from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor,
    GradientBoostingClassifier,
    GradientBoostingRegressor,
)

from sklearn.linear_model import (
    LogisticRegression,
    LinearRegression,
)

from sklearn.tree import (
    DecisionTreeClassifier,
    DecisionTreeRegressor,
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

from ...ui.layout import (
    render_topbar,
    render_page_intro,
    render_section_heading,
)

from ...ui.theme import show_footer


# =========================================================
# SESSION STATE
# =========================================================

def initialize_ml_state():

    if "jak_ml_results" not in st.session_state:
        st.session_state["jak_ml_results"] = None


# =========================================================
# DATASET HELPERS
# =========================================================

def get_datasets():

    datasets = st.session_state.get("jak_datasets", [])

    if not isinstance(datasets, list):
        return []

    return [
        item for item in datasets
        if isinstance(item, dict)
        and isinstance(item.get("data"), pd.DataFrame)
        and not item["data"].empty
    ]


def render_dataset_selector():

    datasets = get_datasets()

    if not datasets:
        st.warning(
            "No datasets available. Upload a dataset before "
            "using the Machine Learning Studio."
        )
        return None, None

    options = {}

    for index, item in enumerate(datasets):

        name = str(item.get("name") or f"Dataset {index + 1}")

        display_name = name

        if display_name in options:
            display_name = f"{name} ({index + 1})"

        options[display_name] = item

    selected_name = st.selectbox(
        "Select Dataset",
        list(options.keys()),
        key="jak_ml_dataset_selector",
    )

    return options[selected_name], selected_name


def render_dataset_overview(data):

    numeric_count = len(
        data.select_dtypes(include="number").columns
    )

    categorical_count = len(
        data.select_dtypes(
            include=["object", "string", "category", "bool"]
        ).columns
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Records", f"{len(data):,}")
    col2.metric("Total Features", len(data.columns))
    col3.metric("Numeric Features", numeric_count)
    col4.metric("Categorical Features", categorical_count)


def get_feature_types(data):

    numeric_features = data.select_dtypes(
        include="number"
    ).columns.tolist()

    categorical_features = data.select_dtypes(
        include=["object", "string", "category", "bool"]
    ).columns.tolist()

    return numeric_features, categorical_features


# =========================================================
# DATA PREPROCESSING
# =========================================================

def clean_feature_data(data):
    """
    Clean feature data and remove completely empty columns.
    """

    X = data.copy()

    X = X.replace(
        [np.inf, -np.inf],
        np.nan
    )

    empty_columns = [
        column for column in X.columns
        if X[column].isna().all()
    ]

    if empty_columns:
        X = X.drop(columns=empty_columns)

    if X.empty or len(X.columns) == 0:
        raise ValueError(
            "No usable input features remain after removing "
            "empty columns."
        )

    return X


def build_preprocessor(data):

    numeric_features, categorical_features = get_feature_types(data)

    transformers = []

    if numeric_features:

        numeric_pipeline = Pipeline([
            (
                "imputer",
                SimpleImputer(strategy="median")
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
                numeric_features
            )
        )

    if categorical_features:

        categorical_pipeline = Pipeline([
            (
                "imputer",
                SimpleImputer(strategy="most_frequent")
            ),
            (
                "encoder",
                OneHotEncoder(handle_unknown="ignore")
            ),
        ])

        transformers.append(
            (
                "categorical",
                categorical_pipeline,
                categorical_features
            )
        )

    if not transformers:
        raise ValueError(
            "No supported numeric or categorical features were found."
        )

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop"
    )


# =========================================================
# MACHINE LEARNING MODELS
# =========================================================

def get_classification_models():

    return {
        "Logistic Regression": LogisticRegression(
            max_iter=1000,
            class_weight="balanced"
        ),

        "Decision Tree": DecisionTreeClassifier(
            max_depth=10,
            class_weight="balanced",
            random_state=42
        ),

        "Random Forest": RandomForestClassifier(
            n_estimators=150,
            max_depth=15,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        ),

        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            random_state=42
        ),
    }


def get_regression_models():

    return {
        "Linear Regression": LinearRegression(),

        "Decision Tree": DecisionTreeRegressor(
            max_depth=10,
            random_state=42
        ),

        "Random Forest": RandomForestRegressor(
            n_estimators=150,
            max_depth=15,
            random_state=42,
            n_jobs=-1
        ),

        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            random_state=42
        ),
    }


# =========================================================
# CONFIGURATION
# =========================================================

def render_problem_configuration(data):

    render_section_heading(
        "Machine Learning Configuration",
        "Choose the machine learning problem you want to solve."
    )

    task = st.selectbox(
        "Machine Learning Task",
        [
            "Classification",
            "Regression",
            "Clustering",
        ],
        key="jak_ml_task",
    )

    target = None

    if task in ["Classification", "Regression"]:

        target = st.selectbox(
            "Select Target Variable",
            data.columns.tolist(),
            key="jak_ml_target",
        )

    return task, target


def render_training_settings():

    render_section_heading(
        "Training Settings",
        "Configure how your model will be trained."
    )

    col1, col2 = st.columns(2)

    with col1:

        test_size = st.slider(
            "Testing Data Percentage",
            min_value=10,
            max_value=40,
            value=20,
            step=5,
            key="jak_ml_test_size",
        )

    with col2:

        random_state = st.number_input(
            "Random State",
            min_value=0,
            max_value=10000,
            value=42,
            key="jak_ml_random_state",
        )

    return test_size / 100, int(random_state)


def render_feature_selector(data, target=None):

    render_section_heading(
        "Feature Selection",
        "Choose which variables the model should use."
    )

    available_features = [
        column for column in data.columns
        if column != target
    ]

    if not available_features:

        st.warning(
            "No input features are available for this task."
        )

        return []

    selected_features = st.multiselect(
        "Select Input Features",
        available_features,
        default=available_features,
        key="jak_ml_features",
    )

    if not selected_features:
        st.warning("Select at least one input feature.")

    return selected_features


def render_model_configuration(task):

    render_section_heading(
        "Choose Machine Learning Algorithm",
        "Select the model you want JAK to train."
    )

    if task == "Classification":

        return st.selectbox(
            "Classification Algorithm",
            list(get_classification_models().keys()),
            key="jak_ml_classification_model",
        )

    if task == "Regression":

        return st.selectbox(
            "Regression Algorithm",
            list(get_regression_models().keys()),
            key="jak_ml_regression_model",
        )

    return "K-Means Clustering"


# =========================================================
# SUPERVISED DATA PREPARATION
# =========================================================

def prepare_supervised_data(data, target, features):

    if target not in data.columns:
        raise ValueError(
            "The selected target column does not exist."
        )

    if not features:
        raise ValueError(
            "Select at least one input feature."
        )

    working = data[features + [target]].copy()

    working = working.replace(
        [np.inf, -np.inf],
        np.nan
    )

    working = working.dropna(
        subset=[target]
    )

    X = working[features].copy()
    y = working[target].copy()

    X = clean_feature_data(X)

    if len(X) == 0:
        raise ValueError(
            "There are no usable records."
        )

    if y.nunique() < 2 and not pd.api.types.is_numeric_dtype(y):
        raise ValueError(
            "The selected target does not contain enough variation."
        )

    return X, y


# =========================================================
# CLASSIFICATION VALIDATION
# =========================================================

def validate_classification_data(y, test_size):

    if y.nunique() < 2:

        raise ValueError(
            "Classification requires at least two target classes."
        )

    class_counts = y.value_counts()

    if class_counts.min() < 2:

        rare_classes = class_counts[class_counts < 2].to_dict()

        raise ValueError(
            "Some target classes have fewer than two records. "
            f"Check these classes: {rare_classes}. "
            "Collect more records for these classes before training."
        )

    test_records = int(np.ceil(len(y) * test_size))

    train_records = len(y) - test_records

    number_of_classes = y.nunique()

    if test_records < number_of_classes:

        raise ValueError(
            "The test dataset is too small to contain every class. "
            "Increase the testing percentage or collect more records."
        )

    if train_records < number_of_classes:

        raise ValueError(
            "The training dataset is too small for the number of "
            "classes. Reduce the testing percentage or collect more records."
        )


# =========================================================
# CLASSIFICATION TRAINING
# =========================================================

def train_classification_model(
    X,
    y,
    model_name,
    test_size,
    random_state,
):

    validate_classification_data(y, test_size)

    models = get_classification_models()

    if model_name not in models:

        raise ValueError(
            "Invalid classification model."
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    pipeline = Pipeline([
        (
            "preprocessor",
            build_preprocessor(X_train)
        ),
        (
            "model",
            models[model_name]
        ),
    ])

    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)

    metrics = {
        "Accuracy": accuracy_score(y_test, predictions),

        "Precision": precision_score(
            y_test,
            predictions,
            average="weighted",
            zero_division=0,
        ),

        "Recall": recall_score(
            y_test,
            predictions,
            average="weighted",
            zero_division=0,
        ),

        "F1 Score": f1_score(
            y_test,
            predictions,
            average="weighted",
            zero_division=0,
        ),
    }

    return {
        "pipeline": pipeline,
        "predictions": predictions,
        "actual": y_test,
        "metrics": metrics,
        "X_test": X_test,
        "y_test": y_test,
        "X_train": X_train,
        "y_train": y_train,
    }


# =========================================================
# REGRESSION TRAINING
# =========================================================

def train_regression_model(
    X,
    y,
    model_name,
    test_size,
    random_state,
):

    models = get_regression_models()

    if model_name not in models:

        raise ValueError(
            "Invalid regression model."
        )

    if len(X) < 3:

        raise ValueError(
            "At least three usable records are required for regression."
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
    )

    if len(X_train) < 2 or len(X_test) < 1:

        raise ValueError(
            "The training or testing dataset is too small. "
            "Add more records or adjust the testing percentage."
        )

    pipeline = Pipeline([
        (
            "preprocessor",
            build_preprocessor(X_train)
        ),
        (
            "model",
            models[model_name]
        ),
    ])

    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)

    mse = mean_squared_error(
        y_test,
        predictions
    )

    r2 = (
        r2_score(y_test, predictions)
        if len(y_test) >= 2 and y_test.nunique() >= 2
        else None
    )

    metrics = {
        "MAE": mean_absolute_error(
            y_test,
            predictions
        ),

        "MSE": mse,

        "RMSE": np.sqrt(mse),

        "R2 Score": r2,
    }

    return {
        "pipeline": pipeline,
        "predictions": predictions,
        "actual": y_test,
        "metrics": metrics,
        "X_test": X_test,
        "y_test": y_test,
        "X_train": X_train,
        "y_train": y_train,
    }


# =========================================================
# CLUSTERING TRAINING
# =========================================================

def train_clustering_model(
    data,
    features,
    number_of_clusters,
    random_state,
):

    if not features:

        raise ValueError(
            "Select at least one clustering feature."
        )

    X = data[features].copy()

    X = clean_feature_data(X)

    if len(X) <= number_of_clusters:

        raise ValueError(
            "The dataset must contain more records than clusters."
        )

    preprocessor = build_preprocessor(X)

    prepared_data = preprocessor.fit_transform(X)

    if hasattr(prepared_data, "toarray"):
        prepared_data = prepared_data.toarray()

    if not np.isfinite(prepared_data).all():

        raise ValueError(
            "The selected features contain invalid values "
            "that could not be processed."
        )

    model = KMeans(
        n_clusters=number_of_clusters,
        random_state=random_state,
        n_init=10,
    )

    labels = model.fit_predict(prepared_data)

    silhouette = None

    if (
        len(np.unique(labels)) > 1
        and len(labels) > number_of_clusters
    ):

        silhouette = silhouette_score(
            prepared_data,
            labels,
        )

    results = data.loc[X.index].copy()

    results["JAK_Cluster"] = labels

    return {
        "model": model,
        "preprocessor": preprocessor,
        "results": results,
        "labels": labels,
        "silhouette": silhouette,
    }


# =========================================================
# CLASSIFICATION RESULTS
# =========================================================

def render_classification_results(results):

    render_section_heading(
        "Classification Results",
        "Evaluate how accurately your model predicts categories."
    )

    metrics = results["metrics"]

    columns = st.columns(len(metrics))

    for index, (name, value) in enumerate(metrics.items()):

        with columns[index]:
            st.metric(name, f"{value:.4f}")

    st.subheader("Confusion Matrix")

    matrix = confusion_matrix(
        results["actual"],
        results["predictions"],
    )

    fig = px.imshow(
        matrix,
        text_auto=True,
        color_continuous_scale="Blues",
        title="Classification Confusion Matrix",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.subheader("Classification Report")

    report = classification_report(
        results["actual"],
        results["predictions"],
        zero_division=0,
        output_dict=True,
    )

    st.dataframe(
        pd.DataFrame(report).T,
        use_container_width=True,
    )


# =========================================================
# REGRESSION RESULTS
# =========================================================

def render_regression_results(results):

    render_section_heading(
        "Regression Results",
        "Evaluate how closely predictions match actual values."
    )

    metrics = results["metrics"]

    columns = st.columns(len(metrics))

    for index, (name, value) in enumerate(metrics.items()):

        with columns[index]:

            if value is None:
                st.metric(name, "Unavailable")
            else:
                st.metric(name, f"{value:,.4f}")

    if metrics["R2 Score"] is None:

        st.info(
            "R² is unavailable because the test dataset does not "
            "contain enough records or target variation."
        )

    comparison = pd.DataFrame({
        "Actual": np.asarray(results["actual"]),
        "Predicted": results["predictions"],
    })

    st.subheader("Actual vs Predicted")

    fig = px.scatter(
        comparison,
        x="Actual",
        y="Predicted",
        title="Actual Values vs Predicted Values",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.subheader("Prediction Comparison")

    st.dataframe(
        comparison.head(100),
        use_container_width=True,
    )

    csv_data = comparison.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "Download Predictions",
        data=csv_data,
        file_name="jak_regression_predictions.csv",
        mime="text/csv",
    )


# =========================================================
# CLUSTERING RESULTS
# =========================================================

def render_clustering_results(results):

    render_section_heading(
        "Clustering Results",
        "Explore the groups discovered by the model."
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "Clusters Created",
        len(np.unique(results["labels"])),
    )

    if results["silhouette"] is not None:

        col2.metric(
            "Silhouette Score",
            f"{results['silhouette']:.4f}",
        )

    else:

        col2.metric(
            "Silhouette Score",
            "Unavailable",
        )

    st.subheader("Cluster Distribution")

    cluster_counts = (
        results["results"]["JAK_Cluster"]
        .value_counts()
        .sort_index()
        .rename_axis("Cluster")
        .reset_index(name="Records")
    )

    fig = px.bar(
        cluster_counts,
        x="Cluster",
        y="Records",
        title="Records per Cluster",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.subheader("Clustered Dataset")

    st.dataframe(
        results["results"].head(100),
        use_container_width=True,
    )

    csv_data = results["results"].to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "Download Clustered Dataset",
        data=csv_data,
        file_name="jak_clustered_dataset.csv",
        mime="text/csv",
    )


# =========================================================
# DISPLAY TRAINING RESULTS
# =========================================================

def render_training_results(task, results):

    st.divider()

    if task == "Classification":

        render_classification_results(results)

    elif task == "Regression":

        render_regression_results(results)

    elif task == "Clustering":

        render_clustering_results(results)


# =========================================================
# MODEL TRAINING PAGE
# =========================================================

def render_model_training_page(data, dataset_name):

    task, target = render_problem_configuration(data)

    st.divider()

    selected_features = render_feature_selector(
        data,
        target if task != "Clustering" else None,
    )

    if not selected_features:
        return

    st.divider()

    model_name = render_model_configuration(task)

    if task == "Clustering":

        if len(data) < 3:

            st.warning(
                "At least three records are required for clustering."
            )

            return

        maximum_clusters = min(10, len(data) - 1)

        number_of_clusters = st.slider(
            "Number of Clusters",
            min_value=2,
            max_value=maximum_clusters,
            value=min(3, maximum_clusters),
            key="jak_ml_cluster_count",
        )

        test_size = None

        random_state = int(
            st.number_input(
                "Random State",
                min_value=0,
                max_value=10000,
                value=42,
                key="jak_ml_cluster_random_state",
            )
        )

    else:

        test_size, random_state = render_training_settings()

        number_of_clusters = None

    with st.container(border=True):

        st.warning(
            """
            Model performance depends on data quality, sample size,
            feature selection and the suitability of the algorithm.

            Test scores do not guarantee performance on future data.
            Review the results before using predictions to make decisions.
            """
        )

    if st.button(
        "🚀 Train Machine Learning Model",
        use_container_width=True,
        type="primary",
        key="jak_ml_train_button",
    ):

        try:

            with st.spinner(
                "JAK is training your machine learning model..."
            ):

                if task == "Classification":

                    X, y = prepare_supervised_data(
                        data,
                        target,
                        selected_features,
                    )

                    if len(X) < 10:

                        raise ValueError(
                            "At least 10 usable records are recommended "
                            "for classification."
                        )

                    results = train_classification_model(
                        X,
                        y,
                        model_name,
                        test_size,
                        random_state,
                    )

                elif task == "Regression":

                    X, y = prepare_supervised_data(
                        data,
                        target,
                        selected_features,
                    )

                    y = pd.to_numeric(
                        y,
                        errors="coerce",
                    )

                    valid = y.notna() & np.isfinite(y)

                    X = X.loc[valid]
                    y = y.loc[valid]

                    if len(X) < 10:

                        raise ValueError(
                            "At least 10 usable numeric target records "
                            "are recommended for regression."
                        )

                    if y.nunique() < 2:

                        raise ValueError(
                            "Regression requires at least two different "
                            "numeric target values."
                        )

                    results = train_regression_model(
                        X,
                        y,
                        model_name,
                        test_size,
                        random_state,
                    )

                else:

                    results = train_clustering_model(
                        data,
                        selected_features,
                        number_of_clusters,
                        random_state,
                    )

                st.session_state["jak_ml_results"] = {
                    "task": task,
                    "model_name": model_name,
                    "dataset_name": dataset_name,
                    "results": results,
                }

                activities = st.session_state.get(
                    "jak_recent_activities",
                    []
                )

                if not isinstance(activities, list):
                    activities = []

                activities.append({
                    "title": "Machine Learning Training",
                    "description": (
                        f"{model_name} completed on {dataset_name}."
                    ),
                    "date": datetime.now().strftime(
                        "%d %B %Y %H:%M"
                    ),
                })

                st.session_state["jak_recent_activities"] = activities[-50:]

            st.success(
                "Machine learning training completed successfully!"
            )

            st.rerun()

        except Exception as error:

            st.error(
                f"Model training failed: {error}"
            )

    # Display previously trained results for this dataset.

    saved_results = st.session_state.get(
        "jak_ml_results"
    )

    if (
        isinstance(saved_results, dict)
        and saved_results.get("dataset_name") == dataset_name
    ):

        st.divider()

        st.subheader(
            f"Trained Model: {saved_results['model_name']}"
        )

        render_training_results(
            saved_results["task"],
            saved_results["results"],
        )


# =========================================================
# MAIN MACHINE LEARNING PAGE
# =========================================================

def render_machine_learning_page():

    initialize_ml_state()

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
        "Machine Learning Studio",
        (
            "Train models, discover patterns, "
            "and evaluate predictions using your datasets."
        ),
    )

    with st.container(border=True):

        st.subheader("🤖 Machine Learning Studio")

        st.write(
            """
            Use your own data to build classification,
            regression and clustering models.

            Configure your features, select an algorithm,
            train the model and review its performance.
            """
        )

    selected_dataset, dataset_name = render_dataset_selector()

    if selected_dataset is None:

        show_footer()
        return

    data = selected_dataset["data"].copy()

    if data.empty:

        st.warning("The selected dataset is empty.")

        show_footer()
        return

    st.divider()

    render_section_heading(
        "Dataset Overview",
        f"Selected dataset: {dataset_name}",
    )

    render_dataset_overview(data)

    st.divider()

    render_model_training_page(
        data,
        dataset_name,
    )

    show_footer()


# =========================================================
# NAVIGATION COMPATIBILITY
# =========================================================

render_machine_learning = render_machine_learning_page