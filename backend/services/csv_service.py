"""
csv_service.py — Robust CSV import and export service
Validates mid-semester components, enforces class-scoping permissions, reports detailed row errors.
"""

import csv
import io
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status

from backend.config import ASSESSMENT_LIMITS
from backend.database import db_session, get_connection
from backend.utils.security import hash_password
from backend.utils.validators import compute_totals, validate_assessment_record

REQUIRED_COLUMNS = [
    "student_id", "student_name", "class", "section",
    "midterm", "assignment", "presentation", "attendance"
]


def parse_and_validate_csv_row(
    row: Dict[str, str],
    row_num: int,
    user: Dict[str, Any]
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Validate a single CSV row against column rules, mark limits, and teacher permissions.
    Returns (cleaned_record_dict, error_message).
    """
    student_id = row.get("student_id", "").strip()
    student_name = row.get("student_name", "").strip()
    class_name = row.get("class", "").strip()
    section = row.get("section", "").strip()

    if not student_id:
        return None, f"Row {row_num}: Missing 'student_id'."
    if not student_name:
        return None, f"Row {row_num}: Missing 'student_name'."
    if not class_name:
        return None, f"Row {row_num}: Missing 'class'."
    if not section:
        return None, f"Row {row_num}: Missing 'section'."

    # Mark validation
    def parse_mark(val_str: str, name: str, min_v: float, max_v: float) -> Tuple[Optional[float], Optional[str]]:
        if val_str is None or val_str.strip() == "":
            return None, None
        try:
            val = float(val_str.strip())
        except ValueError:
            return None, f"Row {row_num}: '{name}' must be numeric, got '{val_str}'."
        if val < min_v or val > max_v:
            return None, f"Row {row_num}: '{name}' mark {val} is outside allowed range ({min_v}–{max_v})."
        return round(val, 2), None

    mid, err = parse_mark(row.get("midterm", ""), "midterm", 0.0, ASSESSMENT_LIMITS["midterm_max"])
    if err: return None, err

    assign, err = parse_mark(row.get("assignment", ""), "assignment", 0.0, ASSESSMENT_LIMITS["assignment_max"])
    if err: return None, err

    pres, err = parse_mark(row.get("presentation", ""), "presentation", 0.0, ASSESSMENT_LIMITS["presentation_max"])
    if err: return None, err

    att, err = parse_mark(row.get("attendance", ""), "attendance", 0.0, ASSESSMENT_LIMITS["attendance_max"])
    if err: return None, err

    return {
        "student_id": student_id,
        "student_name": student_name,
        "class_name": class_name,
        "section": section,
        "midterm": mid,
        "assignment": assign,
        "presentation": pres,
        "attendance": att,
    }, None


def import_students_csv(
    csv_content: str,
    user: Dict[str, Any],
    overwrite: bool = False,
    academic_session: str = "2025-2026",
) -> Dict[str, Any]:
    """
    Import students and assessment records from CSV content.
    Returns summary with imported count, skipped count, and list of error details.
    """
    reader = csv.DictReader(io.StringIO(csv_content))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file appears empty or unreadable.")

    # Check required columns (case-insensitive strip)
    clean_fieldnames = [f.strip().lower() for f in reader.fieldnames if f]
    for req in REQUIRED_COLUMNS:
        if req not in clean_fieldnames:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required CSV column: '{req}'. Required columns: {', '.join(REQUIRED_COLUMNS)}.",
            )

    rows = list(reader)
    if not rows:
        return {
            "total_rows": 0,
            "imported_count": 0,
            "skipped_count": 0,
            "errors": [],
            "message": "CSV file contains header only, no student rows.",
        }

    successful = 0
    skipped = 0
    errors = []
    seen_in_batch = set()

    is_admin = user.get("role") in ("administrator", "admin")
    assigned_class_ids = set(user.get("assigned_class_ids", []))

    with db_session() as conn:
        cur = conn.cursor()

        for idx, r in enumerate(rows, start=2):  # Start at row 2 (row 1 is header)
            # Normalize keys to lower
            row_dict = {k.strip().lower(): v for k, v in r.items() if k}
            cleaned, err = parse_and_validate_csv_row(row_dict, idx, user)
            if err:
                errors.append(err)
                skipped += 1
                continue

            stu_id = cleaned["student_id"]
            if stu_id in seen_in_batch:
                errors.append(f"Row {idx}: Duplicate student ID '{stu_id}' in CSV batch.")
                skipped += 1
                continue
            seen_in_batch.add(stu_id)

            # Class lookup or creation
            cur.execute("""
                SELECT id FROM classes WHERE class_name = ? AND section = ? AND academic_session = ?;
            """, (cleaned["class_name"], cleaned["section"], academic_session))
            cls_row = cur.fetchone()

            if not cls_row:
                if not is_admin:
                    errors.append(
                        f"Row {idx}: Class '{cleaned['class_name']} - {cleaned['section']}' does not exist, and only administrators can create new classes."
                    )
                    skipped += 1
                    continue
                cur.execute("""
                    INSERT INTO classes (class_name, section, academic_session)
                    VALUES (?, ?, ?);
                """, (cleaned["class_name"], cleaned["section"], academic_session))
                class_id = cur.lastrowid
            else:
                class_id = cls_row["id"]

            # Permission check: Teachers can only import to their assigned classes
            if not is_admin and class_id not in assigned_class_ids:
                errors.append(
                    f"Row {idx}: Permission denied. You are not assigned to teach class '{cleaned['class_name']} {cleaned['section']}'."
                )
                skipped += 1
                continue

            # Student existence check
            cur.execute("SELECT id, class_id FROM students WHERE student_id = ?;", (stu_id,))
            s_row = cur.fetchone()

            if s_row:
                student_db_id = s_row["id"]
                if not overwrite:
                    errors.append(
                        f"Row {idx}: Student ID '{stu_id}' already exists in database. Skipped to prevent accidental overwrite."
                    )
                    skipped += 1
                    continue
                # Update student name and class if overwriting
                cur.execute("""
                    UPDATE students SET student_name = ?, class_id = ? WHERE id = ?;
                """, (cleaned["student_name"], class_id, student_db_id))
            else:
                # Create user account for student
                cur.execute("SELECT id FROM users WHERE username = ?;", (stu_id,))
                u_row = cur.fetchone()
                if not u_row:
                    default_pwd_hash = hash_password("student123")
                    cur.execute("""
                        INSERT INTO users (username, password_hash, role, status)
                        VALUES (?, ?, 'student', 'active');
                    """, (stu_id, default_pwd_hash))
                    user_id = cur.lastrowid
                else:
                    user_id = u_row["id"]

                cur.execute("""
                    INSERT INTO students (student_id, student_name, class_id, user_id)
                    VALUES (?, ?, ?, ?);
                """, (stu_id, cleaned["student_name"], class_id, user_id))
                student_db_id = cur.lastrowid

            # Insert or update assessment record
            cur.execute("""
                INSERT INTO assessment_records
                (student_id, midterm_marks, assignment_marks, presentation_marks, attendance_marks, updated_at, updated_by)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                ON CONFLICT(student_id) DO UPDATE SET
                    midterm_marks = excluded.midterm_marks,
                    assignment_marks = excluded.assignment_marks,
                    presentation_marks = excluded.presentation_marks,
                    attendance_marks = excluded.attendance_marks,
                    updated_at = CURRENT_TIMESTAMP,
                    updated_by = excluded.updated_by;
            """, (
                student_db_id,
                cleaned["midterm"],
                cleaned["assignment"],
                cleaned["presentation"],
                cleaned["attendance"],
                f"csv_import ({user['username']})",
            ))

            successful += 1

    return {
        "total_rows": len(rows),
        "imported_count": successful,
        "skipped_count": skipped,
        "errors": errors,
        "message": f"CSV processing complete: {successful} record(s) imported, {skipped} skipped.",
    }


def export_students_csv(user: Dict[str, Any], class_id: Optional[int] = None) -> str:
    """
    Generate CSV string of student assessment records for permitted classes only.
    Does NOT export authentication passwords, hashes, or tokens.
    """
    role = user.get("role")
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT s.student_id, s.student_name, c.class_name as class, c.section,
               a.midterm_marks as midterm, a.assignment_marks as assignment,
               a.presentation_marks as presentation, a.attendance_marks as attendance
        FROM students s
        JOIN classes c ON s.class_id = c.id
        LEFT JOIN assessment_records a ON s.id = a.student_id
    """
    params = []
    conditions = []

    if role in ("administrator", "admin"):
        if class_id:
            conditions.append("s.class_id = ?")
            params.append(class_id)
    elif role == "teacher":
        assigned_ids = user.get("assigned_class_ids", [])
        if not assigned_ids:
            conn.close()
            return "student_id,student_name,class,section,midterm,assignment,presentation,attendance\n"
        if class_id:
            if class_id not in assigned_ids:
                conn.close()
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot export class records outside your assigned classes.",
                )
            conditions.append("s.class_id = ?")
            params.append(class_id)
        else:
            placeholders = ",".join(["?"] * len(assigned_ids))
            conditions.append(f"s.class_id IN ({placeholders})")
            params.extend(assigned_ids)
    elif role == "student":
        conditions.append("s.student_id = ?")
        params.append(user.get("student_id", ""))
    else:
        conn.close()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized.")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY c.class_name, c.section, s.student_id ASC;"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(REQUIRED_COLUMNS)

    for r in rows:
        writer.writerow([
            r["student_id"],
            r["student_name"],
            r["class"],
            r["section"],
            r["midterm"] if r["midterm"] is not None else "",
            r["assignment"] if r["assignment"] is not None else "",
            r["presentation"] if r["presentation"] is not None else "",
            r["attendance"] if r["attendance"] is not None else "",
        ])

    return output.getvalue()
