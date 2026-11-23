# Machine Learning Evaluation & Critical Methodology Report
## Student Learning Pattern Analysis

---

## 1. Executive Summary

This report presents a rigorous scientific audit of the machine learning pipeline developed in the second-version undergraduate Final Year Project. In preparing the system for the **Erasmus Mundus Artificial Intelligence and Sustainable Societies (AISS)** portfolio, the ML functionality was examined for target leakage, train/test contamination, class imbalance, and scientific validity.

---

## 2. Evaluation Against Eight Methodological Criteria

### Criterion 1: Label Creation Logic
An inspection of [`backend/run_pipeline.py`](file:///c:/Users/hajis/Downloads/Student%20Learning%20Pattern%20Analysis/backend/run_pipeline.py#L44-L62) confirmed that `Pattern_Label` and `At_Risk` were generated using deterministic programmatic if-else conditions:

```python
if gpa >= 3.5 and attendance >= 85 and engagement >= 75:
    return "Consistent Learner"
elif attendance < 50 and study_hours <= 4:
    return "Procrastinator"
elif gpa < 2.0 or total_marks < 50:
    return "High-Risk Student"
elif study_hours >= 12 and gpa < 3.0:
    return "Struggling but Trying"
else:
    return "Average Performer"
```

Furthermore, in [`backend/api.py`](file:///c:/Users/hajis/Downloads/Student%20Learning%20Pattern%20Analysis/backend/api.py#L141-L146), `GPA` was synthesized using stochastic sampling (`np.random.uniform`) conditional on total marks.

### Criterion 2: Target Leakage Assessment
The input features provided to the Random Forest classifier were:
`["Mid_Marks", "Assignment_Score", "Presentation_Score", "Final_Marks", "Total_Marks", "GPA", "Attendance_Percent", "Weekly_Study_Hours", "Engagement_Score"]`

Notice that `GPA`, `Attendance_Percent`, `Total_Marks`, and `Weekly_Study_Hours`—the exact mathematical components of the target rules—were fed directly as training features.

The empirical leakage audit in [`ml/feature_analysis.py`](file:///c:/Users/hajis/Downloads/Student%20Learning%20Pattern%20Analysis/ml/feature_analysis.py) proves a **$100.0\%$ deterministic identity** between the heuristic rules and the target labels. The classifier was not discovering latent educational failure; it was merely acting as an over-parameterized approximation of a deterministic if-statement.

### Criterion 3: Record Duplication & Train/Test Leakage
In the extended dataset (`data/student_learning_dataset_500.csv`, 656 rows), there were only **164 unique student roll numbers**. Each student identity was repeated ~4 times across semesters with correlated scores. When random train/test splits are performed on repeated student records without grouping by student ID, identical student behavioral profiles leak between training and testing sets, producing artificially inflated test scores.

### Criterion 4: Class Imbalance
In the 165-record cohort, the risk distribution is severely skewed:
* Not At-Risk ($0$): **150 records ($90.9\%$)**
* At-Risk ($1$): **15 records ($9.1\%$)**

Standard accuracy metrics are misleading under a 10:1 class imbalance. A trivial baseline predicting $0$ for every student achieves $90.9\%$ accuracy without learning any patterns.

### Criterion 5: Comparison With Baselines
Using 5-fold Stratified Cross-Validation ([`ml/evaluate.py`](file:///c:/Users/hajis/Downloads/Student%20Learning%20Pattern%20Analysis/ml/evaluate.py)), the Random Forest classifier was benchmarked against a naive Majority Class Dummy Baseline:

| Model / Baseline | 5-Fold Stratified CV Accuracy | Macro F1-Score | Methodological Assessment |
|---|:---:|:---:|---|
| **Majority Class Baseline** | $40.61\%$ | $0.1444$ | Naive prediction of the most frequent pattern (`Consistent Learner`). |
| **Random Forest Classifier** | $97.58\% \pm 2.05\%$ | $0.9632$ | High accuracy reflects exact memorization of heuristic rules, not empirical predictive power. |

### Criterion 6: Appropriate Evaluation Metrics
Rather than relying solely on raw overall accuracy, Macro-averaged Precision, Recall, and F1-Scores were computed to ensure that minority classes (`High-Risk Student`) are appropriately weighted.

### Criterion 7: Documented Limitations
1. **Absence of Real Empirical Outcome Labels:** The original dataset did not contain verified institutional outcomes (e.g., official dropouts, academic probation notices, degree completion).
2. **Circular Heuristics:** Because target labels were created by the researcher's rules rather than institutional records, evaluating predictive power against those rules is circular.
3. **Incompatibility with Mid-Semester Analytics:** In the revised mid-semester framework, Final Marks and GPA are omitted, rendering the historical 9-feature model unusable for live deployment.

### Criterion 8: Reproducibility
The ML audit scripts ([`ml/preprocessing.py`](file:///c:/Users/hajis/Downloads/Student%20Learning%20Pattern%20Analysis/ml/preprocessing.py), [`ml/feature_analysis.py`](file:///c:/Users/hajis/Downloads/Student%20Learning%20Pattern%20Analysis/ml/feature_analysis.py), [`ml/evaluate.py`](file:///c:/Users/hajis/Downloads/Student%20Learning%20Pattern%20Analysis/ml/evaluate.py), [`ml/train.py`](file:///c:/Users/hajis/Downloads/Student%20Learning%20Pattern%20Analysis/ml/train.py)) and automated tests ([`tests/test_ml.py`](file:///c:/Users/hajis/Downloads/Student%20Learning%20Pattern%20Analysis/tests/test_ml.py)) allow independent, reproducible verification of these findings with fixed seeds.

---

## 3. Pedagogical & Ethical Conclusion

Automating deterministic labels such as *"High-Risk Student"* or *"Likely to Fail"* risks introducing confirmation bias into academic grading, stigmatizing students, and creating self-fulfilling prophecies. 

The **Student Learning Pattern Analysis** system repositions machine learning from an ungrounded predictive authority to an **investigative diagnostic tool**. The core application prioritizes descriptive analytics, component-wise breakdowns, and transparent support indicators, ensuring that instructors retain final, informed authority over educational decisions.
