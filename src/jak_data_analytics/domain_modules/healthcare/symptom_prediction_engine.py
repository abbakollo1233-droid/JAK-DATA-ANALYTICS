"""
JAK Health Intelligence
Symptom-Based Disease Prediction Engine

Features:
- Yes/No symptom processing
- Automatic symptom counting
- Symptom-only model training
- Ranked disease classification
- Top-five model scores
- Prediction result summaries

IMPORTANT:
This is an experimental educational model.
It is not clinically validated and must not
be used to diagnose or treat patients.
"""

from datetime import datetime

import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


ENGINE_NAME = "JAK Symptom Intelligence"
ENGINE_VERSION = "1.0.0"

TARGET_COLUMN = "disease_label"

MEDICAL_DISCLAIMER = (
    "This system provides experimental educational "
    "classification results only. It does not diagnose "
    "diseases or predict what disease a person will "
    "develop next. Consult a qualified healthcare "
    "professional for medical assessment."
)


# --------------------------------------------------
# SYMPTOM DEFINITIONS
# --------------------------------------------------

SYMPTOM_LABELS = {
    "abdominal_pain": "Abdominal pain",
    "appetite_change": "Change in appetite",
    "bloating": "Bloating",
    "blurred_vision": "Blurred vision",
    "chest_pain": "Chest pain",
    "chest_tightness": "Chest tightness",
    "chills": "Chills",
    "cold_intolerance": "Sensitivity to cold",
    "confusion": "Confusion",
    "cough": "Cough",
    "dehydration": "Dehydration",
    "diarrhea": "Diarrhoea",
    "dizziness": "Dizziness",
    "excessive_thirst": "Excessive thirst",
    "excessive_worry": "Excessive worry",
    "facial_drooping": "Facial drooping",
    "fatigue": "Fatigue",
    "fever": "Fever",
    "frequent_urination": "Frequent urination",
    "headache": "Headache",
    "heat_intolerance": "Sensitivity to heat",
    "itching": "Itching",
    "jaundice": "Yellowing of the skin or eyes",
    "joint_pain": "Joint pain",
    "joint_stiffness": "Joint stiffness",
    "leg_swelling": "Leg swelling",
    "light_sensitivity": "Sensitivity to light",
    "loss_of_appetite": "Loss of appetite",
    "loss_of_smell": "Loss of smell",
    "low_mood": "Low mood",
    "lower_abdominal_pain": "Lower abdominal pain",
    "muscle_cramps": "Muscle cramps",
    "muscle_pain": "Muscle pain",
    "nausea": "Nausea",
    "night_sweats": "Night sweats",
    "pain": "Pain",
    "pain_crisis": "Severe pain episode",
    "painful_urination": "Painful urination",
    "pale_skin": "Pale skin",
    "palpitations": "Heart palpitations",
    "poor_concentration": "Poor concentration",
    "rash": "Skin rash",
    "redness": "Redness",
    "runny_nose": "Runny nose",
    "seizure": "Seizure",
    "shortness_of_breath": "Shortness of breath",
    "sleep_change": "Change in sleep",
    "slow_healing": "Slow wound healing",
    "sneezing": "Sneezing",
    "sore_throat": "Sore throat",
    "speech_difficulty": "Difficulty speaking",
    "sweating": "Excessive sweating",
    "swelling": "Swelling",
    "swollen_lymph_nodes": "Swollen lymph nodes",
    "vomiting": "Vomiting",
    "weakness_one_side": "Weakness on one side",
    "weight_change": "Weight change",
    "weight_loss": "Unexplained weight loss",
    "wheezing": "Wheezing",
}


SYMPTOM_COLUMNS = list(SYMPTOM_LABELS.keys())


# --------------------------------------------------
# SYMPTOM QUESTIONS
# --------------------------------------------------

def get_symptom_questions():
    """
    Return all supported Yes/No symptom questions.
    """

    return [
        {
            "column": column,
            "question": f"Are you experiencing {label.lower()}?",
            "label": label,
        }
        for column, label in SYMPTOM_LABELS.items()
    ]


# --------------------------------------------------
# YES / NO PROCESSING
# --------------------------------------------------

def normalize_yes_no(value):
    """
    Convert common Yes/No answers into binary values.
    """

    if value is None:
        return np.nan

    if isinstance(value, (int, float, np.integer, np.floating)):
        if pd.isna(value):
            return np.nan

        if value == 1:
            return 1

        if value == 0:
            return 0

    answer = str(value).strip().lower()

    if answer in {"yes", "y", "true", "1"}:
        return 1

    if answer in {"no", "n", "false", "0"}:
        return 0

    if answer in {"unknown", "not sure", "unsure", ""}:
        return np.nan

    raise ValueError(
        f"Invalid symptom answer: {value}. "
        "Use Yes, No, or Unknown."
    )


def process_symptom_answers(answers):
    """
    Convert questionnaire answers into model input.

    Unknown answers remain missing instead of
    being incorrectly treated as No.
    """

    record = {}

    for column in SYMPTOM_COLUMNS:
        value = answers.get(column)

        record[column] = normalize_yes_no(value)

    return pd.DataFrame([record])


# --------------------------------------------------
# SYMPTOM COUNTING
# --------------------------------------------------

def count_symptoms(answers):
    """
    Count present, absent and unknown symptoms.
    """

    present = []
    absent = []
    unknown = []

    for column in SYMPTOM_COLUMNS:

        value = normalize_yes_no(
            answers.get(column)
        )

        if pd.isna(value):
            unknown.append(column)

        elif value == 1:
            present.append(column)

        else:
            absent.append(column)

    return {
        "total_questions": len(SYMPTOM_COLUMNS),
        "yes_count": len(present),
        "no_count": len(absent),
        "unknown_count": len(unknown),
        "present_symptoms": present,
        "absent_symptoms": absent,
        "unknown_symptoms": unknown,
    }


# --------------------------------------------------
# DATASET VALIDATION
# --------------------------------------------------

def validate_symptom_dataset(dataframe):
    """
    Validate the dataset before model training.
    """

    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("A pandas DataFrame is required.")

    if TARGET_COLUMN not in dataframe.columns:
        raise ValueError(
            f"Dataset must contain {TARGET_COLUMN}."
        )

    available = [
        column
        for column in SYMPTOM_COLUMNS
        if column in dataframe.columns
    ]

    if len(available) < 3:
        raise ValueError(
            "The dataset must contain at least "
            "three supported symptom columns."
        )

    if dataframe[TARGET_COLUMN].nunique() < 2:
        raise ValueError(
            "At least two disease classes are required."
        )

    return available


# --------------------------------------------------
# MODEL TRAINING
# --------------------------------------------------

def train_symptom_model(
    dataframe,
    test_size=0.20,
    random_state=42,
):
    """
    Train a symptom-only disease classification model.

    The target must be disease_label.

    Only symptom columns are used as predictors.
    """

    symptom_columns = validate_symptom_dataset(
        dataframe
    )

    working = dataframe[
        symptom_columns + [TARGET_COLUMN]
    ].copy()

    working[TARGET_COLUMN] = (
        working[TARGET_COLUMN]
        .astype(str)
        .str.strip()
    )

    working = working[
        working[TARGET_COLUMN].ne("")
        & working[TARGET_COLUMN].ne("nan")
    ]

    for column in symptom_columns:
        working[column] = pd.to_numeric(
            working[column],
            errors="coerce"
        )

        working[column] = working[column].where(
            working[column].isin([0, 1]),
            np.nan
        )

    if len(working) < 20:
        raise ValueError(
            "At least 20 labelled records are required."
        )

    class_counts = working[TARGET_COLUMN].value_counts()

    if class_counts.min() < 2:
        raise ValueError(
            "Each disease class needs at least two records."
        )

    X = working[symptom_columns]
    y = working[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    model = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="most_frequent")
            ),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=300,
                    max_depth=None,
                    min_samples_split=2,
                    min_samples_leaf=1,
                    class_weight="balanced",
                    random_state=random_state,
                    n_jobs=-1,
                )
            ),
        ]
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    metrics = {
        "accuracy": float(
            accuracy_score(y_test, predictions)
        ),
        "balanced_accuracy": float(
            balanced_accuracy_score(y_test, predictions)
        ),
        "classification_report": classification_report(
            y_test,
            predictions,
            output_dict=True,
            zero_division=0,
        ),
    }

    return {
        "model": model,
        "feature_columns": symptom_columns,
        "class_labels": list(model.classes_),
        "metrics": metrics,
        "metadata": {
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "target_column": TARGET_COLUMN,
            "algorithm": "Random Forest",
            "training_records": len(X_train),
            "testing_records": len(X_test),
            "total_records": len(working),
            "number_of_classes": len(model.classes_),
            "class_distribution": (
                working[TARGET_COLUMN]
                .value_counts()
                .to_dict()
            ),
            "trained_at": datetime.now().isoformat(),
            "clinical_validation_status": (
                "not_clinically_validated"
            ),
            "dataset_warning": (
                "Synthetic or unverified data cannot "
                "establish real-world medical accuracy."
            ),
        },
        "status": "experimental",
        "disclaimer": MEDICAL_DISCLAIMER,
    }


# --------------------------------------------------
# DISEASE CLASSIFICATION
# --------------------------------------------------

def predict_from_symptoms(
    model_bundle,
    answers,
    top_k=5,
):
    """
    Generate ranked disease-classification results.

    Model scores are not clinical probabilities.
    """

    if not model_bundle or "model" not in model_bundle:
        raise ValueError("A trained symptom model is required.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    symptom_summary = count_symptoms(answers)

    if symptom_summary["yes_count"] == 0:
        raise ValueError(
            "Please select at least one symptom as Yes."
        )

    model = model_bundle["model"]

    feature_columns = model_bundle["feature_columns"]

    record = {}

    for column in feature_columns:
        record[column] = normalize_yes_no(
            answers.get(column)
        )

    input_data = pd.DataFrame(
        [record],
        columns=feature_columns,
    )

    if not input_data.notna().any(axis=1).iloc[0]:
        raise ValueError(
            "No usable symptom information was supplied."
        )

    if not hasattr(model, "predict_proba"):
        raise ValueError(
            "The trained model does not support ranked scores."
        )

    scores = model.predict_proba(input_data)[0]

    classes = model.classes_

    ranked = sorted(
        zip(classes, scores),
        key=lambda item: item[1],
        reverse=True,
    )

    ranked = ranked[:top_k]

    results = pd.DataFrame(
        [
            {
                "Rank": index + 1,
                "Disease label": str(label),
                "Model score": float(score),
            }
            for index, (label, score) in enumerate(ranked)
        ]
    )

    return {
        "results": results,
        "symptom_summary": symptom_summary,
        "all_class_scores": pd.DataFrame(
            {
                "Disease label": [
                    str(label) for label in classes
                ],
                "Model score": [
                    float(score) for score in scores
                ],
            }
        ).sort_values(
            "Model score",
            ascending=False
        ).reset_index(drop=True),
        "generated_at": datetime.now().isoformat(),
        "status": "experimental",
        "disclaimer": MEDICAL_DISCLAIMER,
    }


# --------------------------------------------------
# SAFETY CHECK
# --------------------------------------------------

def get_urgent_warning_flags(answers):
    """
    Flag selected symptoms that can require
    urgent medical assessment.

    This is not a complete emergency triage system.
    """

    urgent_symptoms = {
        "chest_pain",
        "shortness_of_breath",
        "facial_drooping",
        "weakness_one_side",
        "speech_difficulty",
        "seizure",
        "confusion",
    }

    selected = []

    for symptom in urgent_symptoms:

        if symptom not in SYMPTOM_COLUMNS:
            continue

        if normalize_yes_no(
            answers.get(symptom)
        ) == 1:

            selected.append(
                SYMPTOM_LABELS[symptom]
            )

    return {
        "urgent_attention_recommended": bool(selected),
        "warning_symptoms": selected,
        "message": (
            "Seek urgent medical assessment. "
            "Do not wait for an application prediction."
            if selected
            else (
                "No listed urgent warning symptom was "
                "selected. This does not rule out an "
                "emergency."
            )
        ),
    }