"""
create_demo_data.py — Generate documented synthetic demonstration data
Generates realistic mid-semester academic records (Mid 0-30, Assignment 0-3, Presentation 0-3, Attendance 0-4)
with intentional, realistic incomplete assessment records for support insight demonstration.
"""

import csv
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.config import DB_PATH, SYNTHETIC_DATA_DIR
from backend.database import get_connection, init_db
from backend.utils.security import hash_password
from backend.utils.validators import validate_assessment_record, compute_totals


# First and last names for realistic student names
FIRST_NAMES = [
    "Ahmad", "Ali", "Fatima", "Ayesha", "Zainab", "Bilal", "Hamza", "Hassan",
    "Hussein", "Maryam", "Sana", "Usman", "Omar", "Sara", "Khadija", "Mustafa",
    "Zubair", "Ibrahim", "Tariq", "Hiba", "Zahra", "Nadia", "Farhan", "Mahnoor",
    "Saad", "Waleed", "Anum", "Amna", "Daniyal", "Laiba", "Kashif", "Mehwish"
]

LAST_NAMES = [
    "Khan", "Malik", "Ahmed", "Chaudhry", "Raza", "Bhatti", "Shah", "Siddiqui",
    "Qureshi", "Farooq", "Tariq", "Hussain", "Iqbal", "Sheikh", "Mirza", "Akram"
]


def generate_synthetic_data(num_records_per_class: int = 30) -> list:
    """Generate synthetic student records across 3 demonstration classes."""
    random.seed(42)  # For reproducible demonstration data

    classes = [
        {"class_name": "BSIT", "section": "Section A", "session": "2025-2026", "prefix": "FA22-BIT-A"},
        {"class_name": "BSIT", "section": "Section B", "session": "2025-2026", "prefix": "FA22-BIT-B"},
        {"class_name": "BSCS", "section": "Section A", "session": "2025-2026", "prefix": "FA22-BCS-A"},
    ]

    records = []
    used_names = set()

    for cls in classes:
        for i in range(1, num_records_per_class + 1):
            student_id = f"{cls['prefix']}-{i:03d}"
            while True:
                fname = random.choice(FIRST_NAMES)
                lname = random.choice(LAST_NAMES)
                name = f"{fname} {lname}"
                if (name, cls['class_name'], cls['section']) not in used_names:
                    used_names.add((name, cls['class_name'], cls['section']))
                    break

            # Assessment marks generation
            # Categorize students into realistic learning patterns:
            # 1. High performers (~30%)
            # 2. Consistent performers (~40%)
            # 3. Component-divergent students (~15%, e.g. high midterm but low sessional, or vice versa)
            # 4. Students needing support (~15%, low overall marks or low component)
            # Plus intentional incomplete records (~10% across the board)

            r_val = random.random()
            is_incomplete = (i in (3, 7, 14))  # Intentional incomplete records for demonstration

            if r_val < 0.30:
                # Strong across components
                mid = round(random.uniform(24.0, 29.5), 1)
                assign = round(random.uniform(2.5, 3.0), 1)
                pres = round(random.uniform(2.5, 3.0), 1)
                att = round(random.uniform(3.5, 4.0), 1)
            elif r_val < 0.70:
                # Solid average
                mid = round(random.uniform(18.0, 24.0), 1)
                assign = round(random.uniform(1.8, 2.5), 1)
                pres = round(random.uniform(1.8, 2.5), 1)
                att = round(random.uniform(2.5, 3.5), 1)
            elif r_val < 0.85:
                # Component divergence (e.g. high midterm, low assignment/presentation)
                if random.choice([True, False]):
                    mid = round(random.uniform(23.0, 27.0), 1)
                    assign = round(random.uniform(0.8, 1.4), 1)
                    pres = round(random.uniform(0.8, 1.3), 1)
                    att = round(random.uniform(2.0, 3.0), 1)
                else:
                    mid = round(random.uniform(11.0, 15.0), 1)
                    assign = round(random.uniform(2.5, 3.0), 1)
                    pres = round(random.uniform(2.4, 3.0), 1)
                    att = round(random.uniform(3.5, 4.0), 1)
            else:
                # Needs support
                mid = round(random.uniform(9.0, 15.0), 1)
                assign = round(random.uniform(0.8, 1.6), 1)
                pres = round(random.uniform(0.8, 1.5), 1)
                att = round(random.uniform(1.2, 2.4), 1)

            # Incomplete marks handling
            if is_incomplete:
                if i % 3 == 0:
                    assign = None
                elif i % 3 == 1:
                    pres = None
                else:
                    mid = None

            records.append({
                "student_id": student_id,
                "student_name": name,
                "class_name": cls["class_name"],
                "section": cls["section"],
                "academic_session": cls["session"],
                "midterm": mid,
                "assignment": assign,
                "presentation": pres,
                "attendance": att,
            })

    return records


def export_synthetic_csv(records: list, csv_path: Path):
    """Write synthetic dataset to CSV matching import/export specification."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "student_id", "student_name", "class", "section",
        "midterm", "assignment", "presentation", "attendance"
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)
        for r in records:
            writer.writerow([
                r["student_id"],
                r["student_name"],
                r["class_name"],
                r["section"],
                r["midterm"] if r["midterm"] is not None else "",
                r["assignment"] if r["assignment"] is not None else "",
                r["presentation"] if r["presentation"] is not None else "",
                r["attendance"] if r["attendance"] is not None else "",
            ])
    print(f"[Demo Data] Wrote {len(records)} synthetic demonstration records to: {csv_path}")


def populate_db(records: list, db_path: Path = DB_PATH):
    """Insert demonstration classes, students, assessment records, and user logins into SQLite."""
    init_db(db_path)
    conn = get_connection(db_path)
    cur = conn.cursor()

    # Pre-hash student password
    student_pwd_hash = hash_password("student123")

    inserted_students = 0
    for r in records:
        # 1. Find or create class
        cur.execute("""
            SELECT id FROM classes WHERE class_name = ? AND section = ? AND academic_session = ?;
        """, (r["class_name"], r["section"], r["academic_session"]))
        cls_row = cur.fetchone()
        if not cls_row:
            cur.execute("""
                INSERT INTO classes (class_name, section, academic_session)
                VALUES (?, ?, ?);
            """, (r["class_name"], r["section"], r["academic_session"]))
            class_id = cur.lastrowid
        else:
            class_id = cls_row["id"]

        # 2. Create student user account
        cur.execute("SELECT id FROM users WHERE username = ?;", (r["student_id"],))
        user_row = cur.fetchone()
        if not user_row:
            cur.execute("""
                INSERT INTO users (username, password_hash, role, status)
                VALUES (?, ?, 'student', 'active');
            """, (r["student_id"], student_pwd_hash))
            user_id = cur.lastrowid
        else:
            user_id = user_row["id"]

        # 3. Create student record
        cur.execute("SELECT id FROM students WHERE student_id = ?;", (r["student_id"],))
        s_row = cur.fetchone()
        if not s_row:
            cur.execute("""
                INSERT INTO students (student_id, student_name, class_id, user_id)
                VALUES (?, ?, ?, ?);
            """, (r["student_id"], r["student_name"], class_id, user_id))
            student_db_id = cur.lastrowid
        else:
            student_db_id = s_row["id"]

        # 4. Insert or update assessment record
        valid_marks = validate_assessment_record(
            r["midterm"], r["assignment"], r["presentation"], r["attendance"]
        )
        cur.execute("""
            INSERT OR REPLACE INTO assessment_records
            (student_id, midterm_marks, assignment_marks, presentation_marks, attendance_marks, updated_by)
            VALUES (?, ?, ?, ?, ?, 'system_demo_generator');
        """, (
            student_db_id,
            valid_marks["midterm_marks"],
            valid_marks["assignment_marks"],
            valid_marks["presentation_marks"],
            valid_marks["attendance_marks"],
        ))

        inserted_students += 1

    conn.commit()
    conn.close()
    print(f"[Demo Data] Loaded {inserted_students} demonstration students and assessments into {db_path}.")


def main():
    SYNTHETIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
    csv_file = SYNTHETIC_DATA_DIR / "synthetic_student_assessments.csv"
    records = generate_synthetic_data(num_records_per_class=30)
    export_synthetic_csv(records, csv_file)
    populate_db(records, DB_PATH)


if __name__ == "__main__":
    main()
