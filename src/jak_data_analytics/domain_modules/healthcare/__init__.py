"""
JAK Health Intelligence

Healthcare and disease-screening module for
JAK Data Analytics.

Provides:
- Disease registry
- Medical data validation
- Machine-learning prediction engine

All disease predictions are experimental unless
independently clinically validated.
"""

from .disease_registry import (
    DISEASE_REGISTRY,
    MEDICAL_DISCLAIMER,
    get_all_diseases,
    get_disease,
    get_disease_categories,
    get_diseases_by_category,
    search_diseases,
    get_registered_disease_count,
    get_model_status,
    get_diseases_by_status,
)

from .medical_data_validation import (
    validate_numeric_value,
    validate_blood_pressure,
    validate_required_fields,
    validate_medical_record,
    validate_medical_dataset,
    calculate_bmi,
    generate_validation_report,
)

from .disease_prediction_engine import (
    train_disease_model,
    predict_disease_model,
    get_model_information,
    compare_disease_models,
    get_medical_model_safety_status,
    SUPPORTED_ALGORITHMS,
)


__all__ = [
    "DISEASE_REGISTRY",
    "MEDICAL_DISCLAIMER",

    "get_all_diseases",
    "get_disease",
    "get_disease_categories",
    "get_diseases_by_category",
    "search_diseases",
    "get_registered_disease_count",
    "get_model_status",
    "get_diseases_by_status",

    "validate_numeric_value",
    "validate_blood_pressure",
    "validate_required_fields",
    "validate_medical_record",
    "validate_medical_dataset",
    "calculate_bmi",
    "generate_validation_report",

    "train_disease_model",
    "predict_disease_model",
    "get_model_information",
    "compare_disease_models",
    "get_medical_model_safety_status",
    "SUPPORTED_ALGORITHMS",
]