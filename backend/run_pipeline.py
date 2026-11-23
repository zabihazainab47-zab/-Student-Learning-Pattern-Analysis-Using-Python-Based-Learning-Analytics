"""
run_pipeline.py — ML pipeline for Student Learning Pattern Analysis
- Loads CSV dataset
- Trains Random Forest classifier
- Calculates engagement scores and risk flags
- Saves model and loads data into SQLite database
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

# ── Paths ─────────────────────────────────────────────────────────
ROOT       = Path(__file__).resolve().parent.parent
DATA_PATH  = ROOT / "data" / "student_learning_dataset_500.csv"
MODEL_DIR  = ROOT / "models"
OUTPUT_DIR = ROOT / "outputs"
DB_PATH    = ROOT / "fyp.db"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def calculate_engagement_score(row):
    """Weighted engagement score from attendance, study hours, assignment, presentation."""
    eng = (
        (row["Attendance_Percent"] / 100) * 30 +
        (min(row["Weekly_Study_Hours"], 20) / 20) * 20 +
        (row["Assignment_Score"] / 20) * 25 +
        (row["Presentation_Score"] / 10) * 25
    )
    return round(min(eng, 100), 1)


def assign_pattern_label(row):
    """Rule-based pattern label matching SDD requirements."""
    gpa  = row["GPA"]
    att  = row["Attendance_Percent"]
    eng  = row["Engagement_Score"]
    study = row["Weekly_Study_Hours"]
    total = row["Total_Marks"]

    if gpa >= 3.5 and att >= 85 and eng >= 75:
        return "Consistent Learner"
    elif att < 50 and study <= 4:
        return "Procrastinator"
    elif gpa < 2.0 or total < 50:
        return "High-Risk Student"
    elif study >= 12 and gpa < 3.0:
        return "Struggling but Trying"
    else:
        return "Average Performer"


def run_pipeline():
    print("[Pipeline] Starting ML pipeline...")

    # ── Load data ──────────────────────────────────────────────────
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    print(f"[Pipeline] Loaded {len(df)} rows, {df['Roll_No'].nunique()} unique students")

    # ── Feature engineering ────────────────────────────────────────
    df["Engagement_Score"] = df.apply(calculate_engagement_score, axis=1)
    df["Pattern_Label"]    = df.apply(assign_pattern_label, axis=1)
    df["At_Risk"]          = ((df["GPA"] < 2.0) | (df["Attendance_Percent"] < 60) | (df["Total_Marks"] < 50)).astype(int)

    # ── Features and target ────────────────────────────────────────
    FEATURES = [
        "Mid_Marks", "Assignment_Score", "Presentation_Score",
        "Final_Marks", "Total_Marks", "GPA",
        "Attendance_Percent", "Weekly_Study_Hours", "Engagement_Score"
    ]
    TARGET = "Pattern_Label"

    X = df[FEATURES].fillna(0)
    y = df[TARGET]

    # ── Encode labels ──────────────────────────────────────────────
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    # ── Scale features ─────────────────────────────────────────────
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # ── Train/test split ───────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )

    # ── Train Random Forest ────────────────────────────────────────
    print("[Pipeline] Training Random Forest classifier...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight="balanced"
    )
    model.fit(X_train, y_train)

    # ── Evaluate ───────────────────────────────────────────────────
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report   = classification_report(
        y_test, y_pred,
        target_names=label_encoder.classes_,
        output_dict=True
    )

    print(f"[Pipeline] Accuracy: {accuracy:.2%}")
    print(f"[Pipeline] Classes: {list(label_encoder.classes_)}")

    # ── Save model artifacts ───────────────────────────────────────
    with open(MODEL_DIR / "rf_model.pkl",       "wb") as f: pickle.dump(model, f)
    with open(MODEL_DIR / "scaler.pkl",         "wb") as f: pickle.dump(scaler, f)
    with open(MODEL_DIR / "label_encoder.pkl",  "wb") as f: pickle.dump(label_encoder, f)

    print("[Pipeline] Model saved to models/")

    # ── Build dashboard JSON ───────────────────────────────────────
    pattern_counts = df["Pattern_Label"].value_counts().to_dict()
    at_risk_count  = int(df["At_Risk"].sum())
    sem_trend = (
        df.groupby("Semester")["GPA"]
        .mean().round(2)
        .reset_index()
        .rename(columns={"GPA":"avg_gpa"})
        .to_dict(orient="records")
    )
    top_at_risk = (
        df[df["At_Risk"] == 1]
        [["Roll_No","Student_Name","GPA","Attendance_Percent","Total_Marks","Pattern_Label"]]
        .drop_duplicates("Roll_No")
        .head(10)
        .to_dict(orient="records")
    )

    feature_importance = dict(zip(
        FEATURES,
        [round(float(v), 4) for v in model.feature_importances_]
    ))

    dashboard = {
        "overview": {
            "total_students":    int(df["Roll_No"].nunique()),
            "total_records":     int(len(df)),
            "at_risk_count":     at_risk_count,
            "avg_gpa":           round(float(df["GPA"].mean()), 2),
            "avg_attendance":    round(float(df["Attendance_Percent"].mean()), 1),
            "avg_engagement":    round(float(df["Engagement_Score"].mean()), 1),
        },
        "model": {
            "type":              "Random Forest Classifier",
            "accuracy":          round(accuracy, 4),
            "features":          FEATURES,
            "feature_importance": feature_importance,
            "classes":           list(label_encoder.classes_),
            "classification_report": report,
        },
        "pattern_distribution": pattern_counts,
        "gpa_trend":            sem_trend,
        "top_at_risk":          top_at_risk,
        "generated_at":         pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    out_file = OUTPUT_DIR / "dashboard.json"
    out_file.write_text(json.dumps(dashboard, indent=2), encoding="utf-8")
    print(f"[Pipeline] Dashboard saved to {out_file}")

    # ── Load into database ─────────────────────────────────────────
    print("[Pipeline] Loading data into SQLite database...")
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from database import init_db, load_csv_to_db

    init_db()

    # Save processed CSV temporarily
    processed_path = ROOT / "data" / "processed_dataset.csv"
    df.to_csv(processed_path, index=False)
    load_csv_to_db(str(processed_path))

    print("[Pipeline] ✓ Pipeline complete!")
    print(f"  Total students:  {dashboard['overview']['total_students']}")
    print(f"  At-risk:         {at_risk_count}")
    print(f"  Avg GPA:         {dashboard['overview']['avg_gpa']}")
    print(f"  Model accuracy:  {accuracy:.2%}")
    print(f"  Patterns: {pattern_counts}")

    return dashboard


if __name__ == "__main__":
    run_pipeline()
