"""
config.py — Central configuration for Student Learning Pattern Analysis
"""

import os
from pathlib import Path

# Base Paths
BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
SYNTHETIC_DATA_DIR = DATA_DIR / "synthetic"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = ROOT_DIR / "outputs"
MODELS_DIR = ROOT_DIR / "ml" / "models"
DB_PATH = ROOT_DIR / "fyp.db"

# Application Metadata
PROJECT_NAME = os.getenv("PROJECT_NAME", "Student Learning Pattern Analysis")
VERSION = "2.0.0"

# Security & JWT Configuration
# In production, set JWT_SECRET_KEY in the environment
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "slpa_secure_midsemester_key_2026_aiss")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "8"))

# CORS Configuration
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000,http://127.0.0.1:5500,http://localhost:5500,http://127.0.0.1:3000,http://localhost:3000"
    ).split(",")
    if origin.strip()
]

# Assessment Limits (Mid-Semester Structure)
ASSESSMENT_LIMITS = {
    "midterm_max": 30.0,
    "assignment_max": 3.0,
    "presentation_max": 3.0,
    "attendance_max": 4.0,
    "sessional_max": 10.0,  # assignment (3) + presentation (3) + attendance (4)
    "total_max": 40.0,
}
