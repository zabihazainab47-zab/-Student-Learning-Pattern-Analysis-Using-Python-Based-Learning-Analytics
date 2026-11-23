# Data Dictionary
## Student Learning Pattern Analysis

This data dictionary formally defines all analytical and administrative attributes utilized in the **Student Learning Pattern Analysis** platform.

---

## 1. Mid-Semester Analytical Attributes

| Field Name | Storage Type | Allowable Range | Nullable? | Description |
|---|:---:|:---:|:---:|---|
| `midterm_marks` | `REAL` | $0.0 \text{--} 30.0$ | Yes | Formal mid-semester written examination mark. Max 30 marks. |
| `assignment_marks` | `REAL` | $0.0 \text{--} 3.0$ | Yes | Continuous coursework assessment mark. Max 3 marks. |
| `presentation_marks` | `REAL` | $0.0 \text{--} 3.0$ | Yes | Classroom oral presentation and technical communication mark. Max 3 marks. |
| `attendance_marks` | `REAL` | $0.0 \text{--} 4.0$ | Yes | Lecture attendance score. Entered as **marks out of 4**, NOT as a percentage. |
| `sessional_total` | Derived (`REAL`) | $0.0 \text{--} 10.0$ | Yes | Sum of assignment, presentation, and attendance. `NULL` if any component is missing. |
| `total_marks` | Derived (`REAL`) | $0.0 \text{--} 40.0$ | Yes | Cumulative mid-semester total: $\text{Midterm} + \text{Sessional}$. `NULL` if any component is missing. |

---

## 2. Administrative & Identity Attributes

| Field Name | Entity / Table | Storage Type | Description |
|---|---|:---:|---|
| `id` | All tables | `INTEGER` | Surrogate primary key with automatic increment. |
| `username` | `users` | `TEXT` | Unique alphanumeric identifier for authentication. For students, matches `student_id`. |
| `password_hash` | `users` | `TEXT` | One-way cryptographic hash generated via Bcrypt (`passlib`). |
| `role` | `users` | `TEXT` | Access level: strictly one of `'administrator'`, `'teacher'`, `'student'`. |
| `status` | `users` | `TEXT` | Account lifecycle state: `'active'`, `'inactive'`, `'suspended'`. |
| `teacher_name` | `teachers` | `TEXT` | Full academic name and title of the instructor (e.g., "Dr. Mustafa Hameed"). |
| `class_name` | `classes` | `TEXT` | Departmental degree program (e.g., "BSIT", "BSCS"). |
| `section` | `classes` | `TEXT` | Cohort section division (e.g., "Section A", "Section B"). |
| `academic_session` | `classes` | `TEXT` | Academic year and intake period (e.g., "2025-2026"). |
| `student_id` | `students` | `TEXT` | University-issued student registration code (e.g., "FA22-BIT-A-001"). Unique. |
| `student_name` | `students` | `TEXT` | Full registered student name. |
| `updated_at` | `assessment_records` | `TIMESTAMP` | Timestamp of last mark modification. |
| `updated_by` | `assessment_records` | `TEXT` | Username and role of the authenticated user who recorded or imported marks. |

---

## 3. Excluded Fields from Historical Prototype

The following legacy attributes were audited and intentionally **excluded** from the revised mid-semester platform:
* **Gender:** Excluded to eliminate potential demographic bias in descriptive grouping.
* **Weekly Study Hours:** Unverified self-reported survey metric with no institutional validation.
* **GPA:** Formerly synthesized using stochastic random sampling; not reflective of true mid-semester performance.
* **Final Examination Marks:** Mid-semester analytics strictly occur prior to final examinations.
* **Predictive Risk Labels:** Replaced with interpretable, evidence-based pedagogical insights.
