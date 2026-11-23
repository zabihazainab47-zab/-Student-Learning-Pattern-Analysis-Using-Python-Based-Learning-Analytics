"""
preprocessing.py — Data loading, cleaning, and leakage inspection for ML evaluation
Audits the original dataset and prepares features for baseline comparison.
"""

from pathlib import Path
from typing import Tuple
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "raw" / "original_uploaded_dataset.csv"
DATA_500_PATH = ROOT / "data" / "raw" / "original_student_learning_dataset_500.csv"


def load_original_data() -> pd.DataFrame:
    """Load the original 165-record uploaded dataset."""
    if DATA_PATH.exists():
        return pd.read_csv(DATA_PATH)
    elif DATA_500_PATH.exists():
        return pd.read_csv(DATA_500_PATH)
    else:
        raise FileNotFoundError("Raw original dataset not found in data/raw/")


def check_dataset_duplicates(df: pd.DataFrame) -> dict:
    """Check for student ID duplication and train/test leakage vulnerabilities."""
    id_col = "roll_no" if "roll_no" in df.columns else "Roll_No"
    total_records = len(df)
    unique_students = df[id_col].nunique()
    has_repeated_students = total_records > unique_students

    return {
        "total_records": total_records,
        "unique_students": unique_students,
        "repetition_ratio": round(total_records / unique_students, 2),
        "leakage_risk": (
            "HIGH: Same student identities repeat across semesters. "
            "Random train/test splits cause identical student profiles to leak between train and test sets."
            if has_repeated_students else "LOW: Student IDs appear unique in this single-semester slice."
        ),
    }


def prepare_features_and_target(
    df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.Series, StandardScaler, LabelEncoder]:
    """Extract features and target from the original dataset."""
    features = [
        "mid_marks", "assignment_score", "presentation_score",
        "final_marks", "total_marks", "gpa",
        "attendance_percent", "weekly_study_hours", "engagement_score"
    ]
    # Handle casing
    actual_features = []
    for f in features:
        if f in df.columns:
            actual_features.append(f)
        elif f.capitalize() in df.columns:
            actual_features.append(f.capitalize())
        elif f.title() in df.columns:
            actual_features.append(f.title())

    target_col = "pattern_label" if "pattern_label" in df.columns else "Pattern_Label"

    X = df[actual_features].copy().fillna(0)
    y = df[target_col].copy()

    scaler = StandardScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=actual_features)

    encoder = LabelEncoder()
    y_encoded = encoder.fit_transform(y)

    return X_scaled, y_encoded, scaler, encoder
