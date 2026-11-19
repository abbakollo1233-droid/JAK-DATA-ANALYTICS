"""
JAK Health Intelligence
Medical Warning Sign and Urgency Assessment

Features:
- Emergency warning sign identification.
- Urgency classification.
- Multiple warning sign detection.
- Incomplete information support.
- Clear safety recommendations.

IMPORTANT:
This is a conservative safety-support module.
It is not a medical diagnosis or a substitute
for professional clinical assessment.

The rules require review by qualified clinicians
before deployment in a healthcare setting.
"""

from typing import Any


# ============================================================
# 1. EMERGENCY WARNING SIGNS
# ============================================================

EMERGENCY_SYMPTOMS = {

    "chest_pain": (
        "Chest pain can sometimes indicate a serious "
        "medical emergency."
    ),

    "shortness_of_breath": (
        "Difficulty breathing may require immediate "
        "medical assessment."
    ),

    "seizures": (
        "A seizure, particularly a first seizure or "
        "a prolonged seizure, requires urgent assessment."
    ),

    "fainting": (
        "Loss of consciousness requires medical assessment."
    ),

    "confusion": (
        "New or sudden confusion may indicate a serious "
        "medical condition."
    ),

    "bleeding": (
        "Severe or uncontrolled bleeding requires "
        "immediate medical attention."
    ),

}


# ============================================================
# 2. OTHER CONCERNING SYMPTOMS
# ============================================================

CONCERNING_SYMPTOMS = {

    "fever": (
        "Fever may require assessment depending on its "
        "severity, duration and accompanying symptoms."
    ),

    "vomiting": (
        "Persistent vomiting can cause dehydration."
    ),

    "blood_in_urine": (
        "Blood in urine should be medically investigated."
    ),

    "yellow_skin": (
        "Yellowing of the skin or eyes requires medical "
        "assessment."
    ),

    "weight_loss": (
        "Unexplained weight loss should be investigated."
    ),

    "night_sweats": (
        "Persistent night sweats may require investigation."
    ),

    "blurred_vision": (
        "New or sudden vision changes require prompt "
        "medical assessment."
    ),

    "swelling": (
        "Unexplained swelling may require medical assessment."
    ),

    "palpitations": (
        "Persistent or severe palpitations require assessment."
    ),

    "abdominal_pain": (
        "Severe or persistent abdominal pain requires "
        "medical assessment."
    ),

}


# ============================================================
# 3. EMERGENCY COMBINATIONS
# ============================================================

EMERGENCY_COMBINATIONS = [

    {
        "symptoms": {
            "chest_pain",
            "shortness_of_breath"
        },

        "message": (
            "Chest pain together with difficulty breathing "
            "may indicate a medical emergency."
        )
    },

    {
        "symptoms": {
            "confusion",
            "fever"
        },

        "message": (
            "Fever accompanied by new confusion requires "
            "immediate medical assessment."
        )
    },

    {
        "symptoms": {
            "fainting",
            "chest_pain"
        },

        "message": (
            "Fainting with chest pain requires immediate "
            "medical assessment."
        )
    },

]


# ============================================================
# 4. URGENCY LEVELS
# ============================================================

URGENCY_LEVELS = {

    "emergency": {
        "label": "Emergency",
        "priority": 4,
        "instruction": (
            "Seek emergency medical care now. "
            "Do not wait for an online prediction."
        )
    },

    "urgent": {
        "label": "Urgent",
        "priority": 3,
        "instruction": (
            "Arrange prompt medical assessment."
        )
    },

    "medical_review": {
        "label": "Medical Review Recommended",
        "priority": 2,
        "instruction": (
            "Arrange an assessment with a qualified "
            "healthcare professional."
        )
    },

    "routine": {
        "label": "Routine Review",
        "priority": 1,
        "instruction": (
            "Seek medical advice if symptoms persist, "
            "worsen or cause concern."
        )
    },

    "insufficient_information": {
        "label": "Insufficient Information",
        "priority": 0,
        "instruction": (
            "Provide more information or seek professional "
            "assessment if you are concerned."
        )
    }

}


# ============================================================
# 5. NORMALIZE SYMPTOMS
# ============================================================

def normalize_symptoms(symptoms: Any) -> set:
    """
    Convert symptom input into a normalized set.
    """

    if symptoms is None:
        return set()

    if isinstance(symptoms, dict):

        return {
            str(key).strip().lower()
            for key, value in symptoms.items()
            if value
        }

    if isinstance(symptoms, str):

        symptoms = [
            item.strip()
            for item in symptoms.split(",")
            if item.strip()
        ]

    normalized = set()

    for symptom in symptoms:

        value = str(symptom).strip().lower()

        value = value.replace(" ", "_")

        if value:
            normalized.add(value)

    return normalized


# ============================================================
# 6. CHECK EMERGENCY WARNING SIGNS
# ============================================================

def check_emergency_symptoms(symptoms: set) -> list:
    """
    Identify individual emergency warning signs.
    """

    findings = []

    for symptom in symptoms:

        if symptom in EMERGENCY_SYMPTOMS:

            findings.append({

                "symptom": symptom,

                "message": EMERGENCY_SYMPTOMS[symptom],

                "level": "emergency"

            })

    return findings


# ============================================================
# 7. CHECK CONCERNING SYMPTOMS
# ============================================================

def check_concerning_symptoms(symptoms: set) -> list:
    """
    Identify symptoms that may need medical review.
    """

    findings = []

    for symptom in symptoms:

        if symptom in CONCERNING_SYMPTOMS:

            findings.append({

                "symptom": symptom,

                "message": CONCERNING_SYMPTOMS[symptom],

                "level": "medical_review"

            })

    return findings


# ============================================================
# 8. CHECK EMERGENCY COMBINATIONS
# ============================================================

def check_emergency_combinations(symptoms: set) -> list:
    """
    Identify concerning combinations of symptoms.
    """

    findings = []

    for rule in EMERGENCY_COMBINATIONS:

        required = rule["symptoms"]

        if required.issubset(symptoms):

            findings.append({

                "symptoms": sorted(required),

                "message": rule["message"],

                "level": "emergency"

            })

    return findings


# ============================================================
# 9. DETERMINE URGENCY
# ============================================================

def determine_urgency(
    emergency_findings: list,
    concerning_findings: list,
    symptom_count: int
) -> str:
    """
    Determine the conservative urgency category.

    This is not a clinically validated triage algorithm.
    """

    if emergency_findings:

        return "emergency"

    if symptom_count == 0:

        return "insufficient_information"

    if concerning_findings:

        return "medical_review"

    return "routine"


# ============================================================
# 10. MAIN RISK ASSESSMENT FUNCTION
# ============================================================

def assess_patient_risk(
    symptoms: Any,
    age: Any = None,
    pregnancy: Any = None,
    symptom_duration: Any = None
) -> dict:
    """
    Assess warning signs using available information.

    Parameters
    ----------
    symptoms:
        List, set, dictionary or comma-separated symptoms.

    age:
        Optional patient age.

    pregnancy:
        Optional pregnancy information.

    symptom_duration:
        Optional duration of symptoms.

    Returns
    -------
    Dictionary containing warning signs and urgency.

    NOTE:
    Age, pregnancy and symptom duration are retained
    for future clinician-reviewed rules. They do not
    currently determine urgency in this version.
    """

    normalized = normalize_symptoms(
        symptoms
    )

    # --------------------------------------------------------
    # Emergency warning signs
    # --------------------------------------------------------

    emergency_findings = check_emergency_symptoms(
        normalized
    )

    # --------------------------------------------------------
    # Other concerning symptoms
    # --------------------------------------------------------

    concerning_findings = check_concerning_symptoms(
        normalized
    )

    # --------------------------------------------------------
    # Symptom combinations
    # --------------------------------------------------------

    combination_findings = check_emergency_combinations(
        normalized
    )

    # --------------------------------------------------------
    # Determine urgency
    # --------------------------------------------------------

    all_emergency_findings = (
        emergency_findings + combination_findings
    )

    urgency = determine_urgency(
        all_emergency_findings,
        concerning_findings,
        len(normalized)
    )

    urgency_information = URGENCY_LEVELS[urgency]

    # --------------------------------------------------------
    # Build warnings
    # --------------------------------------------------------

    warnings = []

    if emergency_findings:

        warnings.append(
            "One or more emergency warning signs "
            "were identified."
        )

    if combination_findings:

        warnings.append(
            "A potentially serious combination of symptoms "
            "was identified."
        )

    if concerning_findings:

        warnings.append(
            "Some symptoms require medical review."
        )

    if not normalized:

        warnings.append(
            "No symptoms were provided."
        )

    warnings.append(
        "This automated assessment cannot rule out "
        "a medical emergency."
    )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    return {

        "success": True,

        "urgency": urgency,

        "urgency_label": urgency_information["label"],

        "priority": urgency_information["priority"],

        "instruction": urgency_information["instruction"],

        "emergency_findings": emergency_findings,

        "combination_findings": combination_findings,

        "concerning_findings": concerning_findings,

        "symptoms_checked": sorted(normalized),

        "total_symptoms": len(normalized),

        "age_provided": age is not None,

        "pregnancy_information_provided": (
            pregnancy is not None
        ),

        "duration_provided": symptom_duration is not None,

        "warnings": warnings

    }


# ============================================================
# 11. DISPLAY SUMMARY
# ============================================================

def get_risk_summary(result: dict) -> dict:
    """
    Prepare a short summary for the healthcare page.
    """

    return {

        "urgency": result.get(
            "urgency_label",
            "Unknown"
        ),

        "instruction": result.get(
            "instruction",
            ""
        ),

        "emergency_count": len(
            result.get(
                "emergency_findings",
                []
            )
        ),

        "concerning_count": len(
            result.get(
                "concerning_findings",
                []
            )
        ),

        "warning_count": len(
            result.get(
                "warnings",
                []
            )
        )

    }


# ============================================================
# 12. MODULE TEST
# ============================================================

if __name__ == "__main__":

    sample_symptoms = [

        "chest_pain",

        "shortness_of_breath",

        "fever"

    ]

    result = assess_patient_risk(
        symptoms=sample_symptoms,
        age=35
    )

    print("\nJAK HEALTH INTELLIGENCE")

    print("WARNING SIGN ASSESSMENT")

    print("-" * 45)

    print(
        "Urgency:",
        result["urgency_label"]
    )

    print(
        "\nInstruction:",
        result["instruction"]
    )

    print("\nEmergency findings:")

    for finding in result["emergency_findings"]:

        print(
            "-",
            finding["message"]
        )

    print("\nWarnings:")

    for warning in result["warnings"]:

        print(
            "-",
            warning
        )