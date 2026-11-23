"""
train.py — Experimental model training pipeline with documented limitations
Trains Random Forest model on historical features and serializes artifacts to ml/models/.
"""

import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sklearn.ensemble import RandomForestClassifier
from ml.preprocessing import load_original_data, prepare_features_and_target

MODELS_DIR = ROOT / "ml" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def train_and_save():
    print("[ML Train] Loading original dataset for model audit...")
    df = load_original_data()
    X, y, scaler, encoder = prepare_features_and_target(df)

    print(f"[ML Train] Training Random Forest on {len(df)} records across {X.shape[1]} features...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(X, y)

    # Save artifacts
    with open(MODELS_DIR / "rf_model.pkl", "wb") as f:
        pickle.dump(model, f)
    with open(MODELS_DIR / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    with open(MODELS_DIR / "label_encoder.pkl", "wb") as f:
        pickle.dump(encoder, f)

    print(f"[ML Train] ✓ Artifacts saved to: {MODELS_DIR}")
    print("[ML Train] Note: Model retained strictly as an experimental comparative artifact.")


if __name__ == "__main__":
    train_and_save()
