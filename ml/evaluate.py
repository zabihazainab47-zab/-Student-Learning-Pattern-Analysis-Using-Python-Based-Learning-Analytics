"""
evaluate.py — Rigorous scientific evaluation comparing ML model with naive baselines
Demonstrates that high accuracy stems from rule replication rather than genuine pattern discovery.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_score

from ml.preprocessing import load_original_data, prepare_features_and_target


def run_model_evaluation() -> dict:
    df = load_original_data()
    X, y, scaler, encoder = prepare_features_and_target(df)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # 1. Baseline: Dummy Classifier (predicts majority class)
    dummy = DummyClassifier(strategy="most_frequent")
    dummy_scores = cross_val_score(dummy, X, y, cv=cv, scoring="accuracy")
    dummy_f1 = cross_val_score(dummy, X, y, cv=cv, scoring="f1_macro")

    # 2. Random Forest Classifier
    rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42, class_weight="balanced")
    rf_scores = cross_val_score(rf, X, y, cv=cv, scoring="accuracy")
    rf_f1 = cross_val_score(rf, X, y, cv=cv, scoring="f1_macro")

    # Fit single fold for detailed report
    rf.fit(X, y)
    y_pred = rf.predict(X)
    report = classification_report(y, y_pred, target_names=encoder.classes_, output_dict=True)

    results = {
        "dataset_size": len(df),
        "num_features": X.shape[1],
        "classes": list(encoder.classes_),
        "baseline_majority_accuracy": round(float(np.mean(dummy_scores)), 4),
        "baseline_majority_macro_f1": round(float(np.mean(dummy_f1)), 4),
        "random_forest_cv_accuracy_mean": round(float(np.mean(rf_scores)), 4),
        "random_forest_cv_accuracy_std": round(float(np.std(rf_scores)), 4),
        "random_forest_cv_macro_f1": round(float(np.mean(rf_f1)), 4),
        "classification_report": report,
        "evaluation_summary": (
            f"Random Forest CV Accuracy: {np.mean(rf_scores):.2%} (Macro F1: {np.mean(rf_f1):.2f}). "
            f"Baseline Majority Accuracy: {np.mean(dummy_scores):.2%}. "
            "The model achieves exceptional accuracy because the target label was deterministically created "
            "from the input features (GPA, Attendance, Total Marks). It acts as a surrogate for the heuristic rule."
        ),
    }

    return results


def main():
    print("=" * 70)
    print("STUDENT LEARNING PATTERN ANALYSIS — MODEL BENCHMARKING & EVALUATION")
    print("=" * 70)

    results = run_model_evaluation()
    print(f"Dataset Size: {results['dataset_size']} records")
    print(f"Target Classes: {results['classes']}")
    print(f"\n[Baseline] Majority Class Classifier:")
    print(f"  Accuracy: {results['baseline_majority_accuracy']:.2%}")
    print(f"  Macro F1: {results['baseline_majority_macro_f1']:.4f}")

    print(f"\n[Model] Random Forest (5-Fold Stratified CV):")
    print(f"  Accuracy: {results['random_forest_cv_accuracy_mean']:.2%} (+/- {results['random_forest_cv_accuracy_std']:.2%})")
    print(f"  Macro F1: {results['random_forest_cv_macro_f1']:.4f}")

    print(f"\n[Scientific Finding]:")
    print(f"  {results['evaluation_summary']}")


if __name__ == "__main__":
    main()
