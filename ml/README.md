# Machine Learning Audit & Critical Evaluation Module
## Student Learning Pattern Analysis

This directory contains the machine learning audit, feature leakage analysis, baseline benchmarking, and experimental training scripts for the **Student Learning Pattern Analysis** system.

---

## 1. Module Overview

| Script | Purpose |
|---|---|
| [`preprocessing.py`](file:///c:/Users/hajis/Downloads/Student%20Learning%20Pattern%20Analysis/ml/preprocessing.py) | Loads historical raw data, checks student ID repetition across semesters, and scales features. |
| [`feature_analysis.py`](file:///c:/Users/hajis/Downloads/Student%20Learning%20Pattern%20Analysis/ml/feature_analysis.py) | Mathematically verifies deterministic target leakage between features and rule-generated labels. |
| [`evaluate.py`](file:///c:/Users/hajis/Downloads/Student%20Learning%20Pattern%20Analysis/ml/evaluate.py) | Benchmarks the legacy Random Forest against a simple Majority Baseline using 5-Fold Stratified Cross-Validation and Macro F1 scores. |
| [`train.py`](file:///c:/Users/hajis/Downloads/Student%20Learning%20Pattern%20Analysis/ml/train.py) | Reproducibly trains and serializes comparative model artifacts to `ml/models/`. |

---

## 2. Key Methodological Findings

### A. Target Leakage (Rule Replication)
In the original implementation, `Pattern_Label` and `At_Risk` labels were generated via deterministic programmatic if/else rules operating on `GPA`, `Attendance_Percent`, `Total_Marks`, and `Weekly_Study_Hours`:

$$\text{At\_Risk} = \mathbb{I}(\text{GPA} < 2.0 \lor \text{Attendance} < 60\% \lor \text{Total} < 50)$$

A Random Forest classifier was subsequently trained using these exact same metrics as input features. The empirical audit in [`feature_analysis.py`](file:///c:/Users/hajis/Downloads/Student%20Learning%20Pattern%20Analysis/ml/feature_analysis.py) confirms a **$100.0\%$ deterministic identity** between the heuristic rules and the target labels. Consequently, the high accuracy of the classifier ($>98\%$) represents **rule approximation**, not genuine predictive discovery of student failure.

### B. Class Imbalance
The historical risk dataset exhibits a 10:1 class imbalance (150 safe vs 15 at-risk records). Accuracy alone is an invalid metric under such distribution skew.

### C. Shift to Human-Centred Decision Support
Because the revised application focuses exclusively on mid-semester support (eliminating Final Exam marks and simulated GPA), deterministic risk labelling has been decommissioned from the live user interface. Instead, the application surfaces **interpretable, descriptive analytics and component-level support insights**, empowering human instructors to exercise professional pedagogical judgement.
