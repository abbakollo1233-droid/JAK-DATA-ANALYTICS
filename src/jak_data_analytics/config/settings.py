"""
JAK Data Analytics
Application Configuration
"""

import os
from pathlib import Path


# =====================================
# PROJECT DIRECTORIES
# =====================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

STORAGE_DIR = PROJECT_ROOT / "storage_dev"
DATASETS_DIR = STORAGE_DIR / "datasets"
REPORTS_DIR = STORAGE_DIR / "reports"
MODELS_DIR = STORAGE_DIR / "models"


# =====================================
# APPLICATION INFORMATION
# =====================================

APP_NAME = "JAK Data Analytics"
APP_VERSION = "1.0.0"

APP_DESCRIPTION = (
    "Universal Data Analysis and Predictive Intelligence Platform"
)


# =====================================
# ENVIRONMENT SETTINGS
# =====================================

ENVIRONMENT = os.getenv("JAK_ENVIRONMENT", "development")

DEBUG = ENVIRONMENT.lower() == "development"


# =====================================
# DATABASE SETTINGS
# =====================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///storage_dev/jak_dev.db"
)


# =====================================
# UPLOAD SETTINGS
# =====================================

MAX_UPLOAD_SIZE_MB = 200

ALLOWED_FILE_EXTENSIONS = [
    ".csv",
    ".xlsx",
    ".xls",
    ".json",
    ".parquet",
]


# =====================================
# CREATE STORAGE DIRECTORIES
# =====================================

for directory in [
    STORAGE_DIR,
    DATASETS_DIR,
    REPORTS_DIR,
    MODELS_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)