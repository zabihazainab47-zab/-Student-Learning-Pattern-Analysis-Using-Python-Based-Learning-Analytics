# Development Changelog & Reframing Record
## Student Learning Pattern Analysis

This document details the progressive stages of reframing, architecture upgrades, and code improvements undertaken from the second-version undergraduate Final Year Project.

---

## Stage 1: File-by-File Audit & Safety Backup
* **Preservation & Backup:** Created a complete, untouched archive of all original assets in `backup_original_project/` and `data/raw/`.
* **Codebase Audit:** Inspected original backend (`api.py`, `database.py`, `run_pipeline.py`), frontend (`index (2).html`), database (`fyp.db`), and datasets. Identified scale discrepancies, flat table schema limitations, and circular target leakage in the legacy ML pipeline.

---

## Stage 2: Database Architecture Normalization
* **Relational Schema:** Designed and implemented a normalized 6-table relational SQLite architecture (`users`, `teachers`, `classes`, `students`, `teacher_classes`, `assessment_records`) with active foreign key enforcement and uniqueness constraints.
* **Assessment Data Model:** Formulated the exact mid-semester assessment model:
  * Midterm Exam ($0\text{--}30$ marks)
  * Assignment ($0\text{--}3$ marks)
  * Presentation ($0\text{--}3$ marks)
  * Attendance ($0\text{--}4$ marks, strictly as marks out of 4, not a percentage)
  * Derived Sessional ($0\text{--}10$) and Mid-Semester Total ($0\text{--}40$)
* **Data Integrity:** Missing values are stored explicitly as `NULL`. Incomplete records are prevented from calculating partial totals.

---

## Stage 3: Authentication & Role-Based Access Control (RBAC)
* **Cryptographic Security:** Implemented Bcrypt password hashing (`passlib`) and signed HMAC-SHA256 JWT tokens (`python-jose`).
* **Backend Authorization Scoping:**
  * **Administrator:** System-wide management of teachers, classes, students, and global data.
  * **Teacher:** Scoped strictly to assigned classes via the `teacher_classes` junction table.
  * **Student:** Read-only access restricted strictly to their own student identity.

---

## Stage 4: Domain Services & CSV Pipeline
* **Assessment Service (`assessment_service.py`):** Handles mark entry, strict boundary validation, and derived totals computation.
* **Analytics Service (`analytics_service.py`):** Calculates dynamic descriptive statistics (averages, distributions, highest/lowest, incomplete counts) directly from database records.
* **Insight Service (`insight_service.py`):** Generates evidence-based support insights (incomplete records, component divergence, low component scores) without predictive labeling.
* **CSV Service (`csv_service.py`):** Implements robust CSV import with per-row validation and error reporting; exports sanitized CSV marksheets scoped to user permissions.

---

## Stage 5: User Interface Modularization
* **Separation of Concerns:** Deconstructed the monolithic single-file SPA into dedicated dashboards and subpages:
  * Teacher Dashboard (`dashboards/teacher.html`)
  * Student Progress View (`dashboards/student.html`)
  * Administrator Console (`dashboards/admin.html`)
  * Dedicated pages for Students, Details, Assessments, Insights, and CSV Data Management.
* **Accessible Visualizations:** Integrated lightweight Chart.js charts displaying score distributions, component comparisons, and individual progress breakdowns.

---

## Stage 6: Machine Learning Audit & Critical Evaluation
* **Audit Scripts:** Authored `ml/preprocessing.py`, `ml/feature_analysis.py`, `ml/evaluate.py`, and `ml/train.py`.
* **Empirical Findings:** Formally verified $100\%$ deterministic target leakage between features and rule-generated labels. Benchmarked against a Majority Baseline using 5-Fold Stratified Cross-Validation.
* **Ethical Repositioning:** Replaced ungrounded automated failure risk prediction with transparent, human-centred educational decision support.

---

## Stage 7: Automated Test Suite & Documentation
* **Automated Unit Testing:** Created comprehensive tests covering assessment calculations, authentication, permissions, analytics, CSV processing, and ML audit reproducibility.
* **Portfolio Documentation:** Authored complete project documentation including system architecture diagrams, database ER diagrams, data dictionary, ML evaluation report, and ethics framework.
