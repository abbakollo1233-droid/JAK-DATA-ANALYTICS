"""
JAK Data Analytics
Application Constants

This file stores shared values used throughout
the JAK Data Analytics application.
"""


# =====================================
# APPLICATION INFORMATION
# =====================================

APP_NAME = "JAK Data Analytics"

APP_SHORT_NAME = "JAK"

APP_VERSION = "1.0.0"

APP_TAGLINE = (
    "Universal Data Analysis and Predictive Intelligence Platform"
)


# =====================================
# APPLICATION THEME COLORS
# =====================================

COLORS = {
    "primary": "#2563EB",
    "secondary": "#14B8A6",
    "background": "#F8FAFC",
    "sidebar": "#101828",
    "card": "#FFFFFF",
    "text": "#1E293B",
    "muted": "#667085",
    "success": "#16A34A",
    "warning": "#F59E0B",
    "danger": "#DC2626",
    "border": "#EAECF0",
}


# =====================================
# SUPPORTED DATA FILES
# =====================================

SUPPORTED_FILE_FORMATS = [
    ".csv",
    ".xlsx",
    ".xls",
    ".json",
    ".parquet",
]


# =====================================
# DATASET INFORMATION
# =====================================

MAX_UPLOAD_SIZE_MB = 200

DEFAULT_ROWS_PER_PAGE = 25

MAX_PREVIEW_ROWS = 100


# =====================================
# USER ACCOUNT ROLES
# =====================================

USER_ROLES = [
    "user",
    "admin",
    "super_admin",
]


# =====================================
# DATASET STATUS
# =====================================

DATASET_STATUS = {
    "uploaded": "Uploaded",
    "processing": "Processing",
    "completed": "Completed",
    "failed": "Failed",
}


# =====================================
# ANALYSIS TYPES
# =====================================

ANALYSIS_TYPES = [
    "Data Profiling",
    "Data Cleaning",
    "Statistical Analysis",
    "Data Visualization",
    "Machine Learning",
    "Forecasting",
    "Anomaly Detection",
    "Recommendations",
]


# =====================================
# MACHINE LEARNING TASKS
# =====================================

ML_TASKS = [
    "Classification",
    "Regression",
    "Clustering",
    "Anomaly Detection",
    "Time Series Forecasting",
]


# =====================================
# DATE AND TIME
# =====================================

DEFAULT_TIMEZONE = "Africa/Lagos"

DATE_FORMAT = "%Y-%m-%d"

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"