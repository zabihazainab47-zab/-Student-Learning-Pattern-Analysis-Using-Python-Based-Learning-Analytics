"""
teacher_routes.py — Teacher management and class assignments (Administrator only)
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from backend.database import db_session
from backend.permissions import require_roles
from backend.schemas import ClassResponse, TeacherClassAssignRequest, TeacherCreate, TeacherResponse
from backend.utils.security import hash_password

router = APIRouter(prefix="/api/teachers", tags=["Teachers"], dependencies=[Depends(require_roles("administrator"))])


@router.get("", response_model=List[TeacherResponse])
def list_teachers():
    """List all teachers with their assigned classes."""
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT t.id, t.user_id, t.teacher_name, u.username
            FROM teachers t
            JOIN users u ON t.user_id = u.id
            ORDER BY t.teacher_name ASC;
        """)
        teachers_rows = cur.fetchall()

        result = []
        for t in teachers_rows:
            cur.execute("""
                SELECT c.id, c.class_name, c.section, c.academic_session, COUNT(s.id) as student_count
                FROM teacher_classes tc
                JOIN classes c ON tc.class_id = c.id
                LEFT JOIN students s ON c.id = s.class_id
                WHERE tc.teacher_id = ?
                GROUP BY c.id;
            """, (t["id"],))
            cls_rows = cur.fetchall()
            assigned = [
                ClassResponse(
                    id=c["id"],
                    class_name=c["class_name"],
                    section=c["section"],
                    academic_session=c["academic_session"],
                    student_count=c["student_count"],
                )
                for c in cls_rows
            ]

            result.append(TeacherResponse(
                id=t["id"],
                user_id=t["user_id"],
                teacher_name=t["teacher_name"],
                username=t["username"],
                assigned_classes=assigned,
            ))
        return result


@router.post("", response_model=TeacherResponse)
def create_teacher(payload: TeacherCreate):
    """Create a new teacher login account and assign initial classes."""
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = ?;", (payload.username,))
        if cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{payload.username}' is already in use.",
            )

        # Create user
        pwd_hash = hash_password(payload.password)
        cur.execute("""
            INSERT INTO users (username, password_hash, role, status)
            VALUES (?, ?, 'teacher', 'active');
        """, (payload.username, pwd_hash))
        user_id = cur.lastrowid

        # Create teacher record
        cur.execute("""
            INSERT INTO teachers (user_id, teacher_name)
            VALUES (?, ?);
        """, (user_id, payload.teacher_name))
        teacher_id = cur.lastrowid

        # Assign classes
        assigned_classes = []
        if payload.assigned_class_ids:
            for cid in payload.assigned_class_ids:
                cur.execute("""
                    INSERT OR IGNORE INTO teacher_classes (teacher_id, class_id)
                    VALUES (?, ?);
                """, (teacher_id, cid))
                cur.execute("SELECT * FROM classes WHERE id = ?;", (cid,))
                c_row = cur.fetchone()
                if c_row:
                    assigned_classes.append(ClassResponse(
                        id=c_row["id"],
                        class_name=c_row["class_name"],
                        section=c_row["section"],
                        academic_session=c_row["academic_session"],
                    ))

    return TeacherResponse(
        id=teacher_id,
        user_id=user_id,
        teacher_name=payload.teacher_name,
        username=payload.username,
        assigned_classes=assigned_classes,
    )


@router.post("/assign-classes")
def assign_classes_to_teacher(payload: TeacherClassAssignRequest):
    """Update assigned classes for a teacher."""
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM teachers WHERE id = ?;", (payload.teacher_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Teacher not found.")

        # Replace existing assignments
        cur.execute("DELETE FROM teacher_classes WHERE teacher_id = ?;", (payload.teacher_id,))
        for cid in payload.class_ids:
            cur.execute("""
                INSERT OR IGNORE INTO teacher_classes (teacher_id, class_id)
                VALUES (?, ?);
            """, (payload.teacher_id, cid))

    return {"message": "Teacher class assignments updated successfully.", "teacher_id": payload.teacher_id}
