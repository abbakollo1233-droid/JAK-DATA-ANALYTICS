"""
JAK Health Intelligence
Symptom Processing Engine

Purpose:
- Accept symptoms written in ordinary language.
- Normalize common symptom descriptions.
- Recognize alternative symptom names.
- Process multiple symptoms.
- Identify negative symptoms.
- Preserve unrecognized information for review.

IMPORTANT:
This module processes symptom descriptions.
It does not diagnose diseases or determine clinical risk.
"""

import re
from typing import Any


# ============================================================
# 1. SYMPTOM DICTIONARY
# ============================================================

SYMPTOM_ALIASES = {

    "fever": [
        "fever",
        "high temperature",
        "high body temperature",
        "hot body",
        "body is hot",
        "temperature"
    ],

    "headache": [
        "headache",
        "head pain",
        "pain in my head",
        "head hurts",
        "head is aching"
    ],

    "cough": [
        "cough",
        "coughing",
        "persistent cough",
        "dry cough",
        "wet cough"
    ],

    "vomiting": [
        "vomiting",
        "throwing up",
        "throw up",
        "being sick"
    ],

    "nausea": [
        "nausea",
        "feeling nauseous",
        "feeling sick",
        "urge to vomit"
    ],

    "diarrhea": [
        "diarrhea",
        "diarrhoea",
        "loose stool",
        "loose stools",
        "frequent watery stool"
    ],

    "abdominal_pain": [
        "abdominal pain",
        "stomach pain",
        "belly pain",
        "pain in my stomach",
        "stomach ache",
        "stomach cramps"
    ],

    "chest_pain": [
        "chest pain",
        "pain in chest",
        "chest discomfort",
        "tightness in chest"
    ],

    "shortness_of_breath": [
        "shortness of breath",
        "difficulty breathing",
        "breathing difficulty",
        "trouble breathing",
        "cannot breathe properly",
        "hard to breathe",
        "breathlessness"
    ],

    "fatigue": [
        "fatigue",
        "tiredness",
        "extreme tiredness",
        "feeling tired",
        "weakness",
        "body weakness",
        "lack of energy",
        "feeling weak"
    ],

    "muscle_pain": [
        "muscle pain",
        "muscle aches",
        "body pain",
        "body aches",
        "pain all over my body",
        "joint and muscle pain"
    ],

    "joint_pain": [
        "joint pain",
        "painful joints",
        "aching joints",
        "joint aches"
    ],

    "back_pain": [
        "back pain",
        "pain in my back",
        "lower back pain",
        "upper back pain"
    ],

    "dizziness": [
        "dizziness",
        "feeling dizzy",
        "lightheadedness",
        "feeling lightheaded"
    ],

    "loss_of_appetite": [
        "loss of appetite",
        "no appetite",
        "not hungry",
        "poor appetite"
    ],

    "weight_loss": [
        "weight loss",
        "losing weight",
        "unexplained weight loss"
    ],

    "weight_gain": [
        "weight gain",
        "gaining weight",
        "unexplained weight gain"
    ],

    "night_sweats": [
        "night sweats",
        "sweating at night",
        "excessive night sweating"
    ],

    "skin_rash": [
        "skin rash",
        "rash",
        "body rash",
        "skin irritation",
        "red spots on skin",
        "skin eruptions"
    ],

    "itching": [
        "itching",
        "itchy skin",
        "skin itching",
        "feeling itchy"
    ],

    "sore_throat": [
        "sore throat",
        "throat pain",
        "painful throat",
        "difficulty swallowing"
    ],

    "runny_nose": [
        "runny nose",
        "running nose",
        "nose discharge"
    ],

    "nasal_congestion": [
        "blocked nose",
        "stuffy nose",
        "nasal congestion"
    ],

    "sneezing": [
        "sneezing",
        "frequent sneezing"
    ],

    "chills": [
        "chills",
        "shivering",
        "body chills",
        "feeling cold"
    ],

    "blurred_vision": [
        "blurred vision",
        "blurry vision",
        "poor vision",
        "vision is blurry"
    ],

    "frequent_urination": [
        "frequent urination",
        "urinating frequently",
        "passing urine frequently",
        "frequent passing of urine"
    ],

    "excessive_thirst": [
        "excessive thirst",
        "very thirsty",
        "increased thirst",
        "always thirsty"
    ],

    "painful_urination": [
        "painful urination",
        "pain when urinating",
        "burning urination",
        "burning when passing urine",
        "pain while passing urine"
    ],

    "blood_in_urine": [
        "blood in urine",
        "bloody urine",
        "red urine"
    ],

    "swelling": [
        "swelling",
        "body swelling",
        "swollen body",
        "swollen legs",
        "swollen feet"
    ],

    "palpitations": [
        "palpitations",
        "heart palpitations",
        "racing heartbeat",
        "fast heartbeat",
        "heart beating fast"
    ],

    "confusion": [
        "confusion",
        "confused",
        "mental confusion",
        "difficulty thinking clearly"
    ],

    "seizures": [
        "seizure",
        "seizures",
        "convulsions",
        "convulsion",
        "fits",
        "having fits"
    ],

    "fainting": [
        "fainting",
        "fainted",
        "passing out",
        "loss of consciousness"
    ],

    "bleeding": [
        "bleeding",
        "unusual bleeding",
        "excessive bleeding",
        "bleeding from the body"
    ],

    "yellow_skin": [
        "yellow skin",
        "yellow eyes",
        "yellowing of the eyes",
        "yellowing of the skin",
        "jaundice"
    ],

    "constipation": [
        "constipation",
        "difficulty passing stool",
        "hard stool",
        "unable to pass stool"
    ],

    "insomnia": [
        "insomnia",
        "difficulty sleeping",
        "cannot sleep",
        "unable to sleep",
        "poor sleep"
    ],

    "depression_symptoms": [
        "persistent sadness",
        "feeling sad all the time",
        "loss of interest",
        "feeling hopeless"
    ],

}


# ============================================================
# 2. TEXT CLEANING
# ============================================================

def clean_text(value: Any) -> str:
    """
    Convert input into normalized lowercase text.
    """

    if value is None:
        return ""

    text = str(value).strip().lower()

    text = re.sub(r"[^a-z0-9\s\-']", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# 3. BUILD REVERSE SYMPTOM LOOKUP
# ============================================================

def build_symptom_lookup():

    lookup = {}

    for standard_name, aliases in SYMPTOM_ALIASES.items():

        lookup[clean_text(standard_name.replace("_", " "))] = (
            standard_name
        )

        for alias in aliases:

            lookup[clean_text(alias)] = standard_name

    return lookup


SYMPTOM_LOOKUP = build_symptom_lookup()


# ============================================================
# 4. SPLIT USER INPUT
# ============================================================

def split_symptom_input(value: Any) -> list:
    """
    Split ordinary symptom descriptions into individual phrases.
    """

    if value is None:
        return []

    if isinstance(value, (list, tuple, set)):

        phrases = []

        for item in value:
            phrases.extend(split_symptom_input(item))

        return phrases

    text = str(value).strip()

    if not text:
        return []

    # Split on punctuation and common conjunctions.
    parts = re.split(
        r"[,;\n]+|\s+and\s+|\s+also\s+|\s+plus\s+",
        text,
        flags=re.IGNORECASE
    )

    cleaned = []

    for part in parts:

        part = clean_text(part)

        if not part:
            continue

        # Remove common introductory phrases.
        part = re.sub(
            r"^(i have|i am having|i feel|i experience|"
            r"experiencing|suffering from|suffering|"
            r"my symptoms are|symptoms include)\s+",
            "",
            part
        )

        part = part.strip()

        if part:
            cleaned.append(part)

    return cleaned


# ============================================================
# 5. DETECT NEGATIVE SYMPTOMS
# ============================================================

def detect_negative_symptom(phrase: str):
    """
    Identify phrases indicating that a symptom is absent.

    Example:
        'no fever' -> fever is absent
        'without headache' -> headache is absent
    """

    negative_patterns = [
        r"^no\s+(.+)$",
        r"^without\s+(.+)$",
        r"^not\s+having\s+(.+)$",
        r"^do\s+not\s+have\s+(.+)$",
        r"^don't\s+have\s+(.+)$",
        r"^does\s+not\s+have\s+(.+)$",
        r"^doesn't\s+have\s+(.+)$",
        r"^never\s+experienced\s+(.+)$"
    ]

    for pattern in negative_patterns:

        match = re.match(pattern, phrase)

        if match:

            symptom_phrase = clean_text(match.group(1))

            return symptom_phrase

    return None


# ============================================================
# 6. RECOGNIZE SYMPTOMS
# ============================================================

def recognize_symptom(phrase: str):
    """
    Convert a symptom description into its standard identifier.
    """

    phrase = clean_text(phrase)

    if not phrase:
        return None

    # Direct lookup.
    if phrase in SYMPTOM_LOOKUP:

        return SYMPTOM_LOOKUP[phrase]

    # Check common introductory wording.
    prefixes = [
        "having ",
        "have ",
        "experiencing ",
        "feeling ",
        "feel ",
        "suffering from "
    ]

    for prefix in prefixes:

        if phrase.startswith(prefix):

            shortened = phrase[len(prefix):].strip()

            if shortened in SYMPTOM_LOOKUP:

                return SYMPTOM_LOOKUP[shortened]

    return None


# ============================================================
# 7. MAIN SYMPTOM PROCESSOR
# ============================================================

def process_symptoms(symptoms: Any) -> dict:
    """
    Process patient-provided symptom information.

    Accepted examples:

        process_symptoms("Fever, headache and vomiting")

        process_symptoms([
            "Fever",
            "Headache",
            "Body weakness"
        ])

    Returns normalized symptom information.
    """

    phrases = split_symptom_input(symptoms)

    recognized = []

    unrecognized = []

    absent = []

    original_inputs = []

    for phrase in phrases:

        original_inputs.append(phrase)

        # Check for negative symptoms.
        negative_phrase = detect_negative_symptom(phrase)

        if negative_phrase:

            normalized_negative = recognize_symptom(
                negative_phrase
            )

            if normalized_negative:

                absent.append(normalized_negative)

            else:

                unrecognized.append(phrase)

            continue

        # Recognize positive symptoms.
        normalized = recognize_symptom(phrase)

        if normalized:

            recognized.append(normalized)

        else:

            unrecognized.append(phrase)

    # Remove duplicate entries.
    recognized = list(dict.fromkeys(recognized))

    absent = list(dict.fromkeys(absent))

    unrecognized = list(dict.fromkeys(unrecognized))

    # A symptom must not be simultaneously classified
    # as present and absent.
    absent = [
        symptom
        for symptom in absent
        if symptom not in recognized
    ]

    warnings = []

    if not phrases:

        warnings.append(
            "No symptom information was provided."
        )

    if unrecognized:

        warnings.append(
            "Some descriptions were not recognized. "
            "They have been preserved for review."
        )

    if not recognized:

        warnings.append(
            "No recognized positive symptoms were identified."
        )

    return {

        "success": bool(recognized),

        "recognized_symptoms": recognized,

        "absent_symptoms": absent,

        "unrecognized_symptoms": unrecognized,

        "original_inputs": original_inputs,

        "total_recognized": len(recognized),

        "total_absent": len(absent),

        "total_unrecognized": len(unrecognized),

        "warnings": warnings

    }


# ============================================================
# 8. GET SYMPTOM DISPLAY NAMES
# ============================================================

def get_symptom_display_name(symptom: str) -> str:
    """
    Convert an internal symptom identifier into readable text.
    """

    if not symptom:

        return ""

    return symptom.replace("_", " ").title()


# ============================================================
# 9. FORMAT PROCESSED SYMPTOMS
# ============================================================

def format_symptom_results(result: dict) -> dict:
    """
    Prepare symptom results for display in Streamlit.
    """

    recognized = result.get(
        "recognized_symptoms", []
    )

    absent = result.get(
        "absent_symptoms", []
    )

    unrecognized = result.get(
        "unrecognized_symptoms", []
    )

    return {

        "recognized": [
            get_symptom_display_name(item)
            for item in recognized
        ],

        "absent": [
            get_symptom_display_name(item)
            for item in absent
        ],

        "unrecognized": unrecognized,

        "total": len(recognized)

    }


# ============================================================
# 10. TEST THE PROCESSOR
# ============================================================

if __name__ == "__main__":

    sample = (
        "I have fever, headache, vomiting, "
        "body weakness and no cough."
    )

    result = process_symptoms(sample)

    print("\nJAK HEALTH INTELLIGENCE")

    print("SYMPTOM PROCESSING RESULTS")

    print("-" * 45)

    print("\nRecognized symptoms:")

    for symptom in result["recognized_symptoms"]:

        print("-", get_symptom_display_name(symptom))

    print("\nAbsent symptoms:")

    for symptom in result["absent_symptoms"]:

        print("-", get_symptom_display_name(symptom))

    print("\nUnrecognized symptoms:")

    for symptom in result["unrecognized_symptoms"]:

        print("-", symptom)

    print("\nWarnings:")

    for warning in result["warnings"]:

        print("-", warning)