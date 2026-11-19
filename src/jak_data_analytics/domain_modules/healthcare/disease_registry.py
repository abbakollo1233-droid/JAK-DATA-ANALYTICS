"""
JAK Health Intelligence
Disease Registry

Central registry of diseases and medical conditions supported
or planned for the JAK Health Intelligence module.

IMPORTANT:
Registration does not mean that a clinically validated prediction
model is already available for that disease.
"""

from copy import deepcopy


DISEASE_REGISTRY = {

    # ==========================================
    # 1. METABOLIC DISEASES
    # ==========================================

    "diabetes": {
        "name": "Diabetes",
        "category": "Metabolic Diseases",
        "description": "Risk assessment for diabetes and related metabolic conditions.",
        "conditions": [
            "Type 1 Diabetes",
            "Type 2 Diabetes",
            "Prediabetes",
            "Gestational Diabetes",
        ],
        "assessment_type": "Clinical and laboratory data",
        "required_data": [
            "age",
            "glucose",
            "bmi",
            "blood_pressure",
        ],
        "model_status": "planned",
    },

    "obesity": {
        "name": "Obesity",
        "category": "Metabolic Diseases",
        "description": "Assessment of weight-related health risks.",
        "conditions": [
            "Overweight",
            "Obesity",
            "Severe Obesity",
        ],
        "assessment_type": "Clinical measurements",
        "required_data": [
            "age",
            "weight",
            "height",
        ],
        "model_status": "planned",
    },

    "metabolic_syndrome": {
        "name": "Metabolic Syndrome",
        "category": "Metabolic Diseases",
        "description": "Assessment of combined metabolic risk factors.",
        "conditions": [
            "Metabolic Syndrome",
        ],
        "assessment_type": "Clinical and laboratory data",
        "required_data": [
            "waist_circumference",
            "blood_pressure",
            "glucose",
            "triglycerides",
            "hdl",
        ],
        "model_status": "planned",
    },

    # ==========================================
    # 2. CARDIOVASCULAR DISEASES
    # ==========================================

    "heart_disease": {
        "name": "Heart Disease",
        "category": "Cardiovascular Diseases",
        "description": "Assessment of cardiovascular disease risk.",
        "conditions": [
            "Coronary Artery Disease",
            "Heart Failure",
            "Coronary Heart Disease",
            "Other Cardiovascular Conditions",
        ],
        "assessment_type": "Clinical and cardiac measurements",
        "required_data": [
            "age",
            "blood_pressure",
            "cholesterol",
            "heart_rate",
        ],
        "model_status": "planned",
    },

    "hypertension": {
        "name": "Hypertension",
        "category": "Cardiovascular Diseases",
        "description": "Assessment of high blood pressure.",
        "conditions": [
            "Primary Hypertension",
            "Secondary Hypertension",
        ],
        "assessment_type": "Blood pressure measurements",
        "required_data": [
            "systolic_pressure",
            "diastolic_pressure",
        ],
        "model_status": "planned",
    },

    "stroke": {
        "name": "Stroke",
        "category": "Cardiovascular Diseases",
        "description": "Assessment of stroke risk using appropriate clinical data.",
        "conditions": [
            "Ischaemic Stroke",
            "Haemorrhagic Stroke",
        ],
        "assessment_type": "Clinical assessment",
        "required_data": [
            "age",
            "blood_pressure",
            "diabetes_history",
            "smoking_history",
        ],
        "model_status": "planned",
    },

    # ==========================================
    # 3. KIDNEY DISEASES
    # ==========================================

    "kidney_disease": {
        "name": "Kidney Disease",
        "category": "Kidney Diseases",
        "description": "Assessment of kidney function and disease risk.",
        "conditions": [
            "Chronic Kidney Disease",
            "Acute Kidney Injury",
            "Kidney Failure",
        ],
        "assessment_type": "Clinical and laboratory data",
        "required_data": [
            "age",
            "creatinine",
            "blood_urea",
            "egfr",
            "urine_protein",
        ],
        "model_status": "planned",
    },

    # ==========================================
    # 4. LIVER DISEASES
    # ==========================================

    "liver_disease": {
        "name": "Liver Disease",
        "category": "Liver Diseases",
        "description": "Assessment of liver-related conditions.",
        "conditions": [
            "Fatty Liver Disease",
            "Liver Cirrhosis",
            "Liver Fibrosis",
            "Hepatitis-Related Liver Disease",
        ],
        "assessment_type": "Clinical and laboratory data",
        "required_data": [
            "alt",
            "ast",
            "bilirubin",
            "albumin",
            "age",
        ],
        "model_status": "planned",
    },

    "hepatitis": {
        "name": "Hepatitis",
        "category": "Liver Diseases",
        "description": "Support for hepatitis screening and laboratory data analysis.",
        "conditions": [
            "Hepatitis A",
            "Hepatitis B",
            "Hepatitis C",
            "Hepatitis D",
            "Hepatitis E",
        ],
        "assessment_type": "Laboratory testing",
        "required_data": [
            "hepatitis_test_results",
        ],
        "model_status": "planned",
    },

    # ==========================================
    # 5. INFECTIOUS DISEASES
    # ==========================================

    "malaria": {
        "name": "Malaria",
        "category": "Infectious Diseases",
        "description": "Analysis of malaria-related clinical and laboratory data.",
        "conditions": [
            "Plasmodium falciparum Malaria",
            "Other Plasmodium Infections",
        ],
        "assessment_type": "Laboratory and clinical data",
        "required_data": [
            "malaria_test_result",
            "temperature",
            "symptoms",
        ],
        "model_status": "planned",
    },

    "tuberculosis": {
        "name": "Tuberculosis",
        "category": "Infectious Diseases",
        "description": "Tuberculosis screening support and laboratory data analysis.",
        "conditions": [
            "Pulmonary Tuberculosis",
            "Extrapulmonary Tuberculosis",
        ],
        "assessment_type": "Clinical and laboratory data",
        "required_data": [
            "cough_duration",
            "chest_imaging",
            "sputum_test",
        ],
        "model_status": "planned",
    },

    "hiv": {
        "name": "HIV",
        "category": "Infectious Diseases",
        "description": "Support for analysis of HIV screening and laboratory results.",
        "conditions": [
            "HIV Infection",
        ],
        "assessment_type": "Approved laboratory testing",
        "required_data": [
            "approved_hiv_test_result",
        ],
        "model_status": "planned",
    },

    "typhoid": {
        "name": "Typhoid Fever",
        "category": "Infectious Diseases",
        "description": "Analysis of relevant clinical and laboratory information.",
        "conditions": [
            "Typhoid Fever",
        ],
        "assessment_type": "Clinical and laboratory data",
        "required_data": [
            "temperature",
            "blood_culture",
            "symptoms",
        ],
        "model_status": "planned",
    },

    # ==========================================
    # 6. BLOOD DISEASES
    # ==========================================

    "anaemia": {
        "name": "Anaemia",
        "category": "Blood Diseases",
        "description": "Assessment of anaemia-related laboratory findings.",
        "conditions": [
            "Iron Deficiency Anaemia",
            "Vitamin Deficiency Anaemia",
            "Haemolytic Anaemia",
        ],
        "assessment_type": "Blood laboratory results",
        "required_data": [
            "haemoglobin",
            "haematocrit",
            "mcv",
            "ferritin",
        ],
        "model_status": "planned",
    },

    "sickle_cell": {
        "name": "Sickle Cell Disease",
        "category": "Blood Diseases",
        "description": "Support for analysis of sickle cell screening and confirmed test results.",
        "conditions": [
            "Sickle Cell Disease",
            "Sickle Cell Trait",
        ],
        "assessment_type": "Laboratory and genetic testing",
        "required_data": [
            "haemoglobin_electrophoresis",
        ],
        "model_status": "planned",
    },

    # ==========================================
    # 7. CANCERS
    # ==========================================

    "breast_cancer": {
        "name": "Breast Cancer",
        "category": "Cancer",
        "description": "Breast cancer risk and screening data analysis.",
        "conditions": [
            "Breast Cancer",
        ],
        "assessment_type": "Imaging and clinical data",
        "required_data": [
            "age",
            "imaging_findings",
            "biopsy_results",
        ],
        "model_status": "planned",
    },

    "cervical_cancer": {
        "name": "Cervical Cancer",
        "category": "Cancer",
        "description": "Analysis of cervical screening and laboratory results.",
        "conditions": [
            "Cervical Cancer",
        ],
        "assessment_type": "Screening and laboratory data",
        "required_data": [
            "hpv_test",
            "pap_smear_result",
        ],
        "model_status": "planned",
    },

    "prostate_cancer": {
        "name": "Prostate Cancer",
        "category": "Cancer",
        "description": "Analysis of prostate screening and clinical data.",
        "conditions": [
            "Prostate Cancer",
        ],
        "assessment_type": "Clinical and laboratory data",
        "required_data": [
            "age",
            "psa",
            "clinical_findings",
        ],
        "model_status": "planned",
    },

    "lung_cancer": {
        "name": "Lung Cancer",
        "category": "Cancer",
        "description": "Analysis of lung cancer screening and imaging data.",
        "conditions": [
            "Lung Cancer",
        ],
        "assessment_type": "Imaging and clinical data",
        "required_data": [
            "age",
            "smoking_history",
            "imaging_findings",
        ],
        "model_status": "planned",
    },

    "colorectal_cancer": {
        "name": "Colorectal Cancer",
        "category": "Cancer",
        "description": "Analysis of colorectal screening and clinical information.",
        "conditions": [
            "Colon Cancer",
            "Rectal Cancer",
        ],
        "assessment_type": "Screening and clinical data",
        "required_data": [
            "age",
            "family_history",
            "screening_results",
        ],
        "model_status": "planned",
    },

    # ==========================================
    # 8. RESPIRATORY DISEASES
    # ==========================================

    "asthma": {
        "name": "Asthma",
        "category": "Respiratory Diseases",
        "description": "Analysis of asthma-related clinical information.",
        "conditions": [
            "Allergic Asthma",
            "Non-Allergic Asthma",
        ],
        "assessment_type": "Clinical and lung function data",
        "required_data": [
            "symptoms",
            "peak_flow",
            "spirometry",
        ],
        "model_status": "planned",
    },

    "copd": {
        "name": "COPD",
        "category": "Respiratory Diseases",
        "description": "Analysis of chronic obstructive pulmonary disease data.",
        "conditions": [
            "Chronic Bronchitis",
            "Emphysema",
        ],
        "assessment_type": "Clinical and lung function data",
        "required_data": [
            "age",
            "smoking_history",
            "spirometry",
        ],
        "model_status": "planned",
    },

    "pneumonia": {
        "name": "Pneumonia",
        "category": "Respiratory Diseases",
        "description": "Analysis of pneumonia-related clinical and imaging data.",
        "conditions": [
            "Bacterial Pneumonia",
            "Viral Pneumonia",
            "Other Pneumonia",
        ],
        "assessment_type": "Clinical and imaging data",
        "required_data": [
            "temperature",
            "oxygen_saturation",
            "chest_imaging",
        ],
        "model_status": "planned",
    },

    # ==========================================
    # 9. NEUROLOGICAL DISEASES
    # ==========================================

    "parkinsons": {
        "name": "Parkinson's Disease",
        "category": "Neurological Diseases",
        "description": "Analysis of neurological and movement-related data.",
        "conditions": [
            "Parkinson's Disease",
        ],
        "assessment_type": "Clinical and neurological data",
        "required_data": [
            "age",
            "movement_assessment",
            "neurological_findings",
        ],
        "model_status": "planned",
    },

    "alzheimers": {
        "name": "Alzheimer's Disease",
        "category": "Neurological Diseases",
        "description": "Analysis of cognitive assessment and relevant clinical data.",
        "conditions": [
            "Alzheimer's Disease",
            "Mild Cognitive Impairment",
        ],
        "assessment_type": "Cognitive and clinical data",
        "required_data": [
            "age",
            "cognitive_assessment",
            "clinical_findings",
        ],
        "model_status": "planned",
    },

    "epilepsy": {
        "name": "Epilepsy",
        "category": "Neurological Diseases",
        "description": "Analysis of seizure-related clinical and EEG data.",
        "conditions": [
            "Epilepsy",
        ],
        "assessment_type": "Neurological and EEG data",
        "required_data": [
            "seizure_history",
            "eeg_findings",
            "clinical_findings",
        ],
        "model_status": "planned",
    },

    # ==========================================
    # 10. SKIN DISEASES
    # ==========================================

    "eczema": {
        "name": "Eczema",
        "category": "Skin Diseases",
        "description": "Analysis of skin condition information and images.",
        "conditions": [
            "Atopic Dermatitis",
            "Contact Dermatitis",
        ],
        "assessment_type": "Clinical and image data",
        "required_data": [
            "skin_image",
            "symptoms",
            "medical_history",
        ],
        "model_status": "planned",
    },

    "psoriasis": {
        "name": "Psoriasis",
        "category": "Skin Diseases",
        "description": "Analysis of psoriasis-related clinical and image data.",
        "conditions": [
            "Plaque Psoriasis",
            "Other Psoriasis Types",
        ],
        "assessment_type": "Clinical and image data",
        "required_data": [
            "skin_image",
            "symptoms",
            "medical_history",
        ],
        "model_status": "planned",
    },

    # ==========================================
    # 11. EYE DISEASES
    # ==========================================

    "glaucoma": {
        "name": "Glaucoma",
        "category": "Eye Diseases",
        "description": "Analysis of eye examination and imaging information.",
        "conditions": [
            "Open-Angle Glaucoma",
            "Angle-Closure Glaucoma",
        ],
        "assessment_type": "Ophthalmic examination",
        "required_data": [
            "intraocular_pressure",
            "optic_nerve_imaging",
            "visual_field_test",
        ],
        "model_status": "planned",
    },

    "diabetic_retinopathy": {
        "name": "Diabetic Retinopathy",
        "category": "Eye Diseases",
        "description": "Analysis of retinal images and diabetes-related eye findings.",
        "conditions": [
            "Non-Proliferative Diabetic Retinopathy",
            "Proliferative Diabetic Retinopathy",
        ],
        "assessment_type": "Retinal image analysis",
        "required_data": [
            "retinal_image",
            "diabetes_history",
        ],
        "model_status": "planned",
    },

    # ==========================================
    # 12. PREGNANCY-RELATED CONDITIONS
    # ==========================================

    "preeclampsia": {
        "name": "Pre-eclampsia",
        "category": "Pregnancy-Related Conditions",
        "description": "Assessment of pre-eclampsia risk using appropriate antenatal data.",
        "conditions": [
            "Pre-eclampsia",
        ],
        "assessment_type": "Clinical and antenatal data",
        "required_data": [
            "blood_pressure",
            "urine_protein",
            "gestational_age",
        ],
        "model_status": "planned",
    },

    "gestational_diabetes": {
        "name": "Gestational Diabetes",
        "category": "Pregnancy-Related Conditions",
        "description": "Analysis of pregnancy-related glucose testing.",
        "conditions": [
            "Gestational Diabetes",
        ],
        "assessment_type": "Clinical and laboratory data",
        "required_data": [
            "gestational_age",
            "glucose",
            "pregnancy_history",
        ],
        "model_status": "planned",
    },
}


# ==========================================
# REGISTRY FUNCTIONS
# ==========================================

def get_all_diseases():
    """Return all registered diseases."""
    return deepcopy(DISEASE_REGISTRY)


def get_disease(disease_code):
    """Return information about one disease."""
    disease = DISEASE_REGISTRY.get(disease_code)

    if disease is None:
        return None

    return deepcopy(disease)


def get_disease_categories():
    """Return all unique disease categories."""
    return sorted({
        disease["category"]
        for disease in DISEASE_REGISTRY.values()
    })


def get_diseases_by_category(category):
    """Return diseases belonging to a selected category."""
    return {
        code: deepcopy(disease)
        for code, disease in DISEASE_REGISTRY.items()
        if disease["category"].lower() == category.lower()
    }


def search_diseases(search_term):
    """Search diseases by name, category, description or condition."""
    search_term = search_term.strip().lower()

    if not search_term:
        return {}

    results = {}

    for code, disease in DISEASE_REGISTRY.items():

        searchable_text = " ".join([
            code,
            disease["name"],
            disease["category"],
            disease["description"],
            *disease["conditions"],
        ]).lower()

        if search_term in searchable_text:
            results[code] = deepcopy(disease)

    return results


def get_registered_disease_count():
    """Return the total number of registered disease entries."""
    return len(DISEASE_REGISTRY)


def get_model_status(disease_code):
    """Return the development status of a disease model."""
    disease = get_disease(disease_code)

    if disease is None:
        return "not_registered"

    return disease["model_status"]


def get_diseases_by_status(status):
    """Return diseases with a particular model status."""
    return {
        code: deepcopy(disease)
        for code, disease in DISEASE_REGISTRY.items()
        if disease["model_status"] == status
    }


# ==========================================
# MEDICAL SAFETY INFORMATION
# ==========================================

MEDICAL_DISCLAIMER = (
    "JAK Health Intelligence provides medical data analysis and "
    "screening support. Its outputs are not confirmed medical "
    "diagnoses. Predictions must not replace professional medical "
    "assessment, laboratory testing, imaging or treatment."
)


SUPPORTED_ASSESSMENT_TYPES = [
    "Clinical and laboratory data",
    "Clinical measurements",
    "Blood pressure measurements",
    "Laboratory testing",
    "Approved laboratory testing",
    "Imaging and clinical data",
    "Screening and laboratory data",
    "Clinical and lung function data",
    "Clinical and image data",
    "Ophthalmic examination",
    "Retinal image analysis",
    "Clinical and antenatal data",
    "Neurological and EEG data",
]