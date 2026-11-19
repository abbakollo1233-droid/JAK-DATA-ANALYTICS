"""
JAK Health Intelligence
Multiple Disease Prediction Engine

Features:
- Multiple disease prediction.
- Ranked disease results.
- Partial symptom input.
- Automatic symptom processing.
- Compatibility with trained scikit-learn models.
- Prediction score interpretation.
- Input validation.
- Safety warnings.

IMPORTANT:
This is a research and screening engine.
It is not a clinically validated diagnostic system.

Do not use its results to make medical decisions
without appropriate clinical validation and review.
"""

import re
from typing import Any, Optional

import numpy as np
import pandas as pd

from .symptom_processor import process_symptoms


# ============================================================
# 1. CONFIGURATION
# ============================================================

DEFAULT_TOP_K = 5

MIN_TOP_K = 2

MAX_TOP_K = 10


# ============================================================
# 2. TEXT NORMALIZATION
# ============================================================

def normalize_feature_name(value: Any) -> str:
    """
    Normalize feature names so that different naming
    conventions can be matched.

    Examples:
        high_fever -> high fever
        High Fever -> high fever
    """

    value = str(value).strip().lower()

    value = value.replace("_", " ")

    value = re.sub(r"[^a-z0-9\s]", " ", value)

    value = re.sub(r"\s+", " ", value)

    return value.strip()


# ============================================================
# 3. EXTRACT MODEL PIPELINE
# ============================================================

def extract_pipeline(model: Any):
    """
    Accept either a trained model or a dictionary
    containing a trained pipeline.

    Supported dictionary examples:

        {
            "pipeline": trained_pipeline
        }

        {
            "model": trained_pipeline
        }
    """

    if model is None:

        raise ValueError(
            "No trained disease prediction model was supplied."
        )

    if isinstance(model, dict):

        pipeline = model.get("pipeline")

        if pipeline is None:

            pipeline = model.get("model")

        if pipeline is None:

            raise ValueError(
                "The model dictionary does not contain "
                "a trained pipeline."
            )

        return pipeline

    return model


# ============================================================
# 4. GET MODEL FEATURES
# ============================================================

def get_model_features(pipeline) -> list:
    """
    Retrieve the feature names expected by the model.
    """

    features = getattr(
        pipeline,
        "feature_names_in_",
        None
    )

    if features is None:

        raise ValueError(
            "The trained model does not expose feature names. "
            "Train the model using a pandas DataFrame or "
            "store its feature names separately."
        )

    return list(features)


# ============================================================
# 5. PREPARE SYMPTOM FEATURES
# ============================================================

def prepare_symptom_features(
    symptom_result: dict,
    model_features: list
) -> pd.DataFrame:
    """
    Convert processed symptoms into the binary feature
    format expected by a trained symptom-based model.

    Recognized symptoms are represented as 1.

    Other supported symptom features are represented as 0.

    NOTE:
    Missing symptoms must not automatically be interpreted
    as clinically confirmed absent symptoms.

    This function creates model input values only.
    """

    present_symptoms = set(
        symptom_result.get(
            "recognized_symptoms",
            []
        )
    )

    absent_symptoms = set(
        symptom_result.get(
            "absent_symptoms",
            []
        )
    )

    row = {}

    matched_count = 0

    for feature in model_features:

        normalized_feature = normalize_feature_name(
            feature
        )

        if normalized_feature in present_symptoms:

            row[feature] = 1

            matched_count += 1

        elif normalized_feature in absent_symptoms:

            row[feature] = 0

        else:

            # The model requires a value for every feature.
            # This is a computational default, not a claim
            # that the patient does not have the symptom.
            row[feature] = 0

    dataframe = pd.DataFrame(
        [row],
        columns=model_features
    )

    dataframe.attrs["matched_symptoms"] = matched_count

    dataframe.attrs["input_warning"] = (
        "Unreported symptoms were assigned zero for model "
        "compatibility. They have not been confirmed absent."
    )

    return dataframe


# ============================================================
# 6. GET MODEL CLASSES
# ============================================================

def get_model_classes(pipeline) -> list:
    """
    Retrieve disease labels from the trained classifier.
    """

    classes = getattr(
        pipeline,
        "classes_",
        None
    )

    if classes is not None:

        return list(classes)

    # Some classifiers expose classes on their final estimator.
    final_estimator = getattr(
        pipeline,
        "steps",
        None
    )

    if final_estimator:

        estimator = final_estimator[-1][1]

        classes = getattr(
            estimator,
            "classes_",
            None
        )

        if classes is not None:

            return list(classes)

    raise ValueError(
        "The trained model does not expose disease classes."
    )


# ============================================================
# 7. GENERATE CLASS SCORES
# ============================================================

def generate_class_scores(
    pipeline,
    dataframe: pd.DataFrame
) -> dict:
    """
    Generate scores for all disease classes.

    Prefer predict_proba when supported.

    Otherwise use decision_function.

    Raw scores must not be interpreted as calibrated
    disease probabilities.
    """

    classes = get_model_classes(pipeline)

    if hasattr(pipeline, "predict_proba"):

        raw_scores = pipeline.predict_proba(
            dataframe
        )[0]

        scores = np.asarray(
            raw_scores,
            dtype=float
        )

        if len(scores) != len(classes):

            raise ValueError(
                "The number of model scores does not match "
                "the number of disease classes."
            )

        return {
            "classes": classes,
            "scores": scores.tolist(),
            "score_type": "uncalibrated_model_probability"
        }

    if hasattr(pipeline, "decision_function"):

        raw_scores = pipeline.decision_function(
            dataframe
        )

        scores = np.asarray(
            raw_scores,
            dtype=float
        )

        if scores.ndim == 1:

            if len(classes) != 2:

                raise ValueError(
                    "Unexpected decision score format."
                )

            scores = np.array([
                -scores[0],
                scores[0]
            ])

        else:

            scores = scores[0]

        return {
            "classes": classes,
            "scores": scores.tolist(),
            "score_type": "decision_score"
        }

    raise ValueError(
        "This model does not support ranked disease scores. "
        "Use a classifier supporting predict_proba or "
        "decision_function."
    )


# ============================================================
# 8. RANK DISEASE PREDICTIONS
# ============================================================

def rank_disease_predictions(
    class_scores: dict,
    top_k: int = DEFAULT_TOP_K
) -> list:
    """
    Rank possible diseases from highest to lowest score.
    """

    classes = class_scores["classes"]

    scores = class_scores["scores"]

    score_type = class_scores["score_type"]

    if not isinstance(top_k, int):

        raise ValueError(
            "top_k must be an integer."
        )

    if top_k < MIN_TOP_K or top_k > MAX_TOP_K:

        raise ValueError(
            f"top_k must be between "
            f"{MIN_TOP_K} and {MAX_TOP_K}."
        )

    if len(classes) != len(scores):

        raise ValueError(
            "Disease classes and scores do not match."
        )

    results = []

    for disease, score in zip(classes, scores):

        score = float(score)

        if not np.isfinite(score):

            continue

        results.append({

            "disease": str(disease),

            "model_score": score,

            "score_type": score_type

        })

    results.sort(
        key=lambda item: item["model_score"],
        reverse=True
    )

    return results[:top_k]


# ============================================================
# 9. MAIN MULTIPLE DISEASE PREDICTOR
# ============================================================

def predict_multiple_diseases(
    model: Any,
    symptoms: Any,
    top_k: int = DEFAULT_TOP_K
) -> dict:
    """
    Generate multiple ranked disease predictions.

    Parameters
    ----------
    model:
        A trained multiclass scikit-learn classifier
        or a dictionary containing its pipeline.

    symptoms:
        A symptom description or list of symptoms.

    top_k:
        Number of disease results to return.

    Returns
    -------
    Dictionary containing prediction results,
    recognized symptoms and warnings.

    Example
    -------
    result = predict_multiple_diseases(
        model=trained_pipeline,
        symptoms=[
            "fever",
            "headache",
            "vomiting"
        ],
        top_k=5
    )
    """

    if not isinstance(top_k, int):

        raise ValueError(
            "top_k must be an integer."
        )

    if top_k < MIN_TOP_K or top_k > MAX_TOP_K:

        raise ValueError(
            f"Select between {MIN_TOP_K} and "
            f"{MAX_TOP_K} predictions."
        )

    # --------------------------------------------------------
    # Process symptoms
    # --------------------------------------------------------

    symptom_result = process_symptoms(
        symptoms
    )

    recognized = symptom_result.get(
        "recognized_symptoms",
        []
    )

    if not recognized:

        return {

            "success": False,

            "predictions": [],

            "recognized_symptoms": [],

            "absent_symptoms": symptom_result.get(
                "absent_symptoms",
                []
            ),

            "unrecognized_symptoms": symptom_result.get(
                "unrecognized_symptoms",
                []
            ),

            "total_predictions": 0,

            "message": (
                "No recognized positive symptoms were "
                "provided. Enter at least one recognized "
                "symptom before requesting a screening result."
            ),

            "warnings": symptom_result.get(
                "warnings",
                []
            )

        }

    # --------------------------------------------------------
    # Extract model
    # --------------------------------------------------------

    pipeline = extract_pipeline(
        model
    )

    # --------------------------------------------------------
    # Obtain expected features
    # --------------------------------------------------------

    model_features = get_model_features(
        pipeline
    )

    # --------------------------------------------------------
    # Prepare input
    # --------------------------------------------------------

    dataframe = prepare_symptom_features(
        symptom_result,
        model_features
    )

    matched_count = dataframe.attrs.get(
        "matched_symptoms",
        0
    )

    if matched_count == 0:

        return {

            "success": False,

            "predictions": [],

            "recognized_symptoms": recognized,

            "total_predictions": 0,

            "message": (
                "The supplied symptoms do not match "
                "the features supported by this model."
            ),

            "warnings": [
                "A different disease prediction model "
                "may be required."
            ]

        }

    # --------------------------------------------------------
    # Generate scores
    # --------------------------------------------------------

    class_scores = generate_class_scores(
        pipeline,
        dataframe
    )

    # --------------------------------------------------------
    # Rank results
    # --------------------------------------------------------

    predictions = rank_disease_predictions(
        class_scores,
        top_k=top_k
    )

    # --------------------------------------------------------
    # Safety warnings
    # --------------------------------------------------------

    warnings = [

        "These are model-generated screening results, "
        "not confirmed medical diagnoses.",

        "The model has not been clinically validated "
        "by this prediction engine.",

        "Unreported symptoms were assigned zero for "
        "model compatibility and must not be treated "
        "as confirmed absent symptoms.",

        "Seek assessment from a qualified healthcare "
        "professional before making medical decisions."

    ]

    if class_scores["score_type"] != (
        "uncalibrated_model_probability"
    ):

        warnings.append(
            "The displayed scores are model ranking scores, "
            "not disease probabilities."
        )

    else:

        warnings.append(
            "The model's probability outputs are not "
            "verified as clinically calibrated probabilities."
        )

    return {

        "success": True,

        "predictions": predictions,

        "recognized_symptoms": recognized,

        "absent_symptoms": symptom_result.get(
            "absent_symptoms",
            []
        ),

        "unrecognized_symptoms": symptom_result.get(
            "unrecognized_symptoms",
            []
        ),

        "total_predictions": len(predictions),

        "score_type": class_scores["score_type"],

        "matched_model_features": matched_count,

        "message": (
            "Multiple disease screening results generated."
        ),

        "warnings": warnings

    }


# ============================================================
# 10. FORMAT PREDICTION RESULTS
# ============================================================

def format_prediction_results(result: dict) -> pd.DataFrame:
    """
    Convert prediction results into a DataFrame
    for Streamlit display or CSV export.
    """

    predictions = result.get(
        "predictions",
        []
    )

    if not predictions:

        return pd.DataFrame(
            columns=[
                "Rank",
                "Possible Condition",
                "Model Score",
                "Score Type"
            ]
        )

    rows = []

    for index, item in enumerate(
        predictions,
        start=1
    ):

        rows.append({

            "Rank": index,

            "Possible Condition": item["disease"],

            "Model Score": item["model_score"],

            "Score Type": item["score_type"]

        })

    return pd.DataFrame(rows)


# ============================================================
# 11. GET PREDICTION SUMMARY
# ============================================================

def get_prediction_summary(result: dict) -> dict:
    """
    Prepare a short summary for the healthcare dashboard.
    """

    predictions = result.get(
        "predictions",
        []
    )

    if not predictions:

        return {

            "status": "No prediction available",

            "total_predictions": 0,

            "leading_condition": None,

            "message": result.get(
                "message",
                "Insufficient information."
            )

        }

    return {

        "status": "Screening results available",

        "total_predictions": len(predictions),

        "leading_condition": predictions[0]["disease"],

        "message": (
            "Ranked screening possibilities are available "
            "for professional review."
        )

    }


# ============================================================
# 12. EXPORT PREDICTION RESULTS
# ============================================================

def export_prediction_results(
    result: dict
) -> bytes:
    """
    Export screening results as CSV bytes.
    """

    dataframe = format_prediction_results(
        result
    )

    return dataframe.to_csv(
        index=False
    ).encode("utf-8")


# ============================================================
# 13. MODULE TEST
# ============================================================

if __name__ == "__main__":

    print("JAK HEALTH INTELLIGENCE")

    print("MULTIPLE DISEASE PREDICTION ENGINE")

    print("-" * 50)

    print(
        "This module requires a trained multiclass "
        "disease prediction model."
    )

    print(
        "Connect a properly evaluated model before "
        "generating predictions."
    )