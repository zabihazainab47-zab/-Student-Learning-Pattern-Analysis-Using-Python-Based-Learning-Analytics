# Data Governance & Lineage Guide
## Student Learning Pattern Analysis

This document details the data organization, lineage, academic assessment scales, and ethical handling of datasets within the **Student Learning Pattern Analysis** system.

---

## 1. Directory Structure

```
data/
├── raw/
│   ├── original_uploaded_dataset.csv            # 165 raw historical student records
│   ├── original_student_learning_dataset_500.csv # 656 repeated records (164 unique students)
│   └── original_processed_dataset.csv           # Pipeline snapshot from legacy system
│
├── synthetic/
│   └── synthetic_student_assessments.csv        # 90 synthetic records on the revised 40-mark scale
│
├── processed/                                   # Cleaned outputs and user CSV exports
└── README.md                                    # This data governance guide
```

---

## 2. Assessment Scale Evolution & Separation

### Legacy System Scale (Preserved in `data/raw/`)
The original project utilized an exploratory 100-mark cumulative grading scale:
* **Midterm Examination:** 0–30 marks
* **Assignment Score:** 0–20 marks
* **Presentation Score:** 0–10 marks
* **Final Examination:** 0–40 marks
* **Attendance:** Recorded as a percentage ($0\text{--}100\%$)
* **Total Marks:** $0\text{--}100$ marks
* **Derived Metrics:** GPA ($0.0\text{--}4.0$, generated stochastically via `np.random.uniform`), Weekly Study Hours, Engagement Score ($0\text{--}100$).

> [!WARNING]
> In accordance with strict development requirements, **raw legacy data is never silently converted or resized** to match new assessment components. It is preserved strictly as a historical benchmark in `data/raw/` and within the root `backup_original_project/` folder.

---

### Revised Mid-Semester Assessment Scale (Active in `fyp.db` & `data/synthetic/`)
The improved application focuses strictly on **timely mid-semester educational analytics**:

| Assessment Component | Range | Max Marks | Input Type | Validation Rules |
|---|:---:|:---:|:---:|---|
| **Midterm Examination** | $0\text{--}30$ | 30 | Numeric | Strictly $\ge 0$ and $\le 30$. Nullable. |
| **Assignment** | $0\text{--}3$ | 3 | Numeric | Strictly $\ge 0$ and $\le 3$. Nullable. |
| **Presentation** | $0\text{--}3$ | 3 | Numeric | Strictly $\ge 0$ and $\le 3$. Nullable. |
| **Attendance** | $0\text{--}4$ | 4 | Numeric | Strictly marks out of 4 (NOT percentage). Nullable. |
| **Sessional Total** | $0\text{--}10$ | 10 | Derived | $\text{Assignment} + \text{Presentation} + \text{Attendance}$. Null if any component is missing. |
| **Overall Midterm Total** | $0\text{--}40$ | 40 | Derived | $\text{Midterm} + \text{Sessional}$. Null if any component is missing. |

### Critical Rules
1. **Attendance is Marks Out of 4**: Entering a percentage (e.g., $85\%$) is rejected during input validation and CSV processing.
2. **Missing Values Remain `NULL`**: Incomplete marks are never imputed or replaced with zero.
3. **Derived Totals Require Full Submissions**: Totals are calculated only when all four assessment marks are recorded.

---

## 3. Synthetic Demonstration Dataset

To safely showcase the application in public demonstrations and academic portfolios without exposing real student privacy or distorting historical marks, a dedicated reproducible synthetic demonstration dataset was generated (`scripts/create_demo_data.py`):

* **Cohort Size:** 90 student records across 3 academic classes:
  * `BSIT - Section A` (30 students, `FA22-BIT-A-001` to `030`)
  * `BSIT - Section B` (30 students, `FA22-BIT-B-001` to `030`)
  * `BSCS - Section A` (30 students, `FA22-BCS-A-001` to `030`)
* **Distribution Characteristics:** Realistic grade spreads reflecting high achievement ($30\%$), steady consistency ($40\%$), component divergence ($15\%$), and students requiring academic support ($15\%$).
* **Intentional Missing Records:** Approximately $10\%$ of students feature intentional `NULL` marks in selected components to allow instructors to evaluate incomplete record tracking and evidence-based alerts.
