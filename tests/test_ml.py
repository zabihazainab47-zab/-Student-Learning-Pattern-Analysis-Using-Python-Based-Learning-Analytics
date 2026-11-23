"""
test_ml.py — Unit tests verifying reproducible ML audit and evaluation pipeline
"""

import unittest
from ml.evaluate import run_model_evaluation
from ml.feature_analysis import analyze_target_leakage
from ml.preprocessing import check_dataset_duplicates, load_original_data


class TestMachineLearningAudit(unittest.TestCase):

    def test_original_dataset_loads(self):
        """Original raw dataset loads properly from data/raw/."""
        df = load_original_data()
        self.assertGreater(len(df), 100)
        self.assertIn("mid_marks", [c.lower() for c in df.columns])

    def test_target_leakage_detected(self):
        """Audit correctly identifies deterministic relationship between features and target labels."""
        df = load_original_data()
        audit = analyze_target_leakage(df)
        self.assertEqual(audit["pattern_rule_deterministic_match_pct"], 100.0)
        self.assertIn("CIRCULAR TARGET LEAKAGE", audit["verdict"])

    def test_evaluation_pipeline_reproducible(self):
        """Evaluation runs and returns benchmark metrics against baseline."""
        results = run_model_evaluation()
        self.assertIn("baseline_majority_accuracy", results)
        self.assertIn("random_forest_cv_accuracy_mean", results)
        self.assertGreater(results["random_forest_cv_accuracy_mean"], results["baseline_majority_accuracy"])
        self.assertIn("classification_report", results)


if __name__ == "__main__":
    unittest.main()
