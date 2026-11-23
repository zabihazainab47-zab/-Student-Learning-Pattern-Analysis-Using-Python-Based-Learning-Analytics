"""
assessment_service.py — Business logic for student assessments
Handles mid-semester mark entries, validation, calculation, and retrieval.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status

from backend.database import db_session, get_connection
from backend.utils.validators import compute_totals, validate_assessment_record


def get_student_assessment(student_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve full assessment record with derived totals for a student."""
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT s.id as student_db_id, s.student_id, s.student_name, s.class_id,
                   c.class_name, c.section, c.academic_session,
                   a.id as assessment_id, a.midterm_marks, a.assignment_marks,
                   a.presentation_marks, a.attendance_marks, a.updated_at, a.updated_by
            FROM students s
            JOIN classes c ON s.class_id = c.id
            LEFT JOIN assessment_records a ON s.id = a.student_id
            WHERE s.student_id = ?;
        """, (student_id,))
        row = cur.fetchone()
        if not row:
            return None

        data = dict(row)
        totals = compute_totals(
            data["midterm_marks"],
            data["assignment_marks"],
            data["presentation_marks"],
            data["attendance_marks"],
        )
        data.update(totals)
        return data


def get_class_assessments(class_id: int) -> List[Dict[str, Any]]:
    """Retrieve all student assessment records for a specific class."""
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT s.id as student_db_id, s.student_id, s.student_name, s.class_id,
                   c.class_name, c.section, c.academic_session,
                   a.id as assessment_id, a.midterm_marks, a.assignment_marks,
                   a.presentation_marks, a.attendance_marks, a.updated_at, a.updated_by
            FROM students s
            JOIN classes c ON s.class_id = c.id
            LEFT JOIN assessment_records a ON s.id = a.student_id
            WHERE s.class_id = ?
            ORDER BY s.student_id ASC;
        """, (class_id,))
        rows = cur.fetchall()

        result = []
        for r in rows:
            item = dict(r)
            totals = compute_totals(
                item["midterm_marks"],
                item["assignment_marks"],
                item["presentation_marks"],
                item["attendance_marks"],
            )
            item.update(totals)
            result.append(item)
        return result


def update_student_assessment(
    student_id: str,
    midterm: Optional[float],
    assignment: Optional[float],
    presentation: Optional[float],
    attendance: Optional[float],
    updated_by: str,
) -> Dict[str, Any]:
    """
    Update mid-semester assessment marks for a student.
    Strictly validates all 4 components (Mid 0-30, Assign 0-3, Pres 0-3, Att 0-4).
    Rejects out-of-range values. Missing marks are stored as NULL.
    """
    valid_marks = validate_assessment_record(midterm, assignment, presentation, attendance)

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM students WHERE student_id = ?;", (student_id,))
        s_row = cur.fetchone()
        if not s_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student ID '{student_id}' does not exist.",
            )
        student_db_id = s_row["id"]

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
            valid_marks["midterm_marks"],
            valid_marks["assignment_marks"],
            valid_marks["presentation_marks"],
            valid_marks["attendance_marks"],
            updated_by,
        ))

    return get_student_assessment(student_id)
