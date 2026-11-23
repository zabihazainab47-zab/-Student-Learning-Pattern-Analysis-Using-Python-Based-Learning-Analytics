"""
student_routes.py — Student CRUD and scoped listings
Enforces role-based visibility and student self-access isolation.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.auth import get_current_user
from backend.database import db_session
from backend.permissions import check_student_record_access, require_roles
from backend.schemas import StudentCreate, StudentResponse, StudentUpdate
from backend.utils.security import hash_password

router = APIRouter(prefix="/api/students", tags=["Students"])


@router.get("", response_model=List[StudentResponse])
def list_students(
    class_id: Optional[int] = Query(None, description="Filter by class ID"),
    search: Optional[str] = Query(None, description="Search by student ID or name"),
    current_user: dict = Depends(get_current_user),
):
    """
    List students with permission scoping:
    - Students: return only their own profile.
    - Teachers: return students strictly within their assigned classes.
    - Administrators: return students across any class.
    """
    role = current_user.get("role")

    if role == "student":
        student_id = current_user.get("student_id")
        if not student_id:
            return []
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT s.id, s.student_id, s.student_name, s.class_id, s.user_id,
                       c.class_name, c.section, c.academic_session
                FROM students s
                JOIN classes c ON s.class_id = c.id
                WHERE s.student_id = ?;
            """, (student_id,))
            row = cur.fetchone()
            return [StudentResponse(**dict(row))] if row else []

    with db_session() as conn:
        cur = conn.cursor()
        query = """
            SELECT s.id, s.student_id, s.student_name, s.class_id, s.user_id,
                   c.class_name, c.section, c.academic_session
            FROM students s
            JOIN classes c ON s.class_id = c.id
        """
        conditions = []
        params = []

        # Teacher scoping
        if role == "teacher":
            assigned_ids = current_user.get("assigned_class_ids", [])
            if not assigned_ids:
                return []
            if class_id:
                if class_id not in assigned_ids:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied. Class is not assigned to you.",
                    )
                conditions.append("s.class_id = ?")
                params.append(class_id)
            else:
                placeholders = ",".join(["?"] * len(assigned_ids))
                conditions.append(f"s.class_id IN ({placeholders})")
                params.extend(assigned_ids)
        elif class_id:
            conditions.append("s.class_id = ?")
            params.append(class_id)

        # Search filter
        if search:
            conditions.append("(s.student_id LIKE ? OR s.student_name LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY c.class_name, c.section, s.student_id ASC;"
        cur.execute(query, params)
        rows = cur.fetchall()

        return [StudentResponse(**dict(r)) for r in rows]


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get individual student profile.
    Strictly forbids students from viewing other students' profiles.
    """
    student_record = check_student_record_access(current_user, student_id)
    return StudentResponse(
        id=student_record["id"],
        student_id=student_record["student_id"],
        student_name=student_record["student_name"],
        class_id=student_record["class_id"],
        class_name=student_record["class_name"],
        section=student_record["section"],
        academic_session=student_record["academic_session"],
        user_id=student_record["user_id"],
    )


@router.post("", response_model=StudentResponse, dependencies=[Depends(require_roles("administrator"))])
def create_student(payload: StudentCreate):
    """Create a new student record and optional student user login (Administrator only)."""
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM students WHERE student_id = ?;", (payload.student_id,))
        if cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Student ID '{payload.student_id}' already exists.",
            )

        cur.execute("SELECT * FROM classes WHERE id = ?;", (payload.class_id,))
        cls_row = cur.fetchone()
        if not cls_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Class ID {payload.class_id} does not exist.",
            )

        # Optional user account
        user_id = None
        if payload.create_user_account:
            cur.execute("SELECT id FROM users WHERE username = ?;", (payload.student_id,))
            u_row = cur.fetchone()
            if not u_row:
                pwd_hash = hash_password(payload.default_password or "student123")
                cur.execute("""
                    INSERT INTO users (username, password_hash, role, status)
                    VALUES (?, ?, 'student', 'active');
                """, (payload.student_id, pwd_hash))
                user_id = cur.lastrowid
            else:
                user_id = u_row["id"]

        cur.execute("""
            INSERT INTO students (student_id, student_name, class_id, user_id)
            VALUES (?, ?, ?, ?);
        """, (payload.student_id, payload.student_name, payload.class_id, user_id))
        new_student_db_id = cur.lastrowid

        # Initialize empty assessment record
        cur.execute("""
            INSERT OR IGNORE INTO assessment_records (student_id, updated_by)
            VALUES (?, 'admin_creation');
        """, (new_student_db_id,))

    return StudentResponse(
        id=new_student_db_id,
        student_id=payload.student_id,
        student_name=payload.student_name,
        class_id=payload.class_id,
        class_name=cls_row["class_name"],
        section=cls_row["section"],
        academic_session=cls_row["academic_session"],
        user_id=user_id,
    )


@router.put("/{student_id}", response_model=StudentResponse, dependencies=[Depends(require_roles("administrator"))])
def update_student(student_id: str, payload: StudentUpdate):
    """Update student basic information (Administrator only)."""
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM students WHERE student_id = ?;", (student_id,))
        s_row = cur.fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail=f"Student ID '{student_id}' not found.")

        updates = []
        params = []
        if payload.student_name is not None:
            updates.append("student_name = ?")
            params.append(payload.student_name)
        if payload.class_id is not None:
            cur.execute("SELECT id FROM classes WHERE id = ?;", (payload.class_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=400, detail="Target class ID does not exist.")
            updates.append("class_id = ?")
            params.append(payload.class_id)

        if updates:
            params.append(student_id)
            cur.execute(f"UPDATE students SET {', '.join(updates)} WHERE student_id = ?;", params)

        cur.execute("""
            SELECT s.*, c.class_name, c.section, c.academic_session
            FROM students s
            JOIN classes c ON s.class_id = c.id
            WHERE s.student_id = ?;
        """, (student_id,))
        updated = cur.fetchone()
        return StudentResponse(**dict(updated))


@router.delete("/{student_id}", dependencies=[Depends(require_roles("administrator"))])
def delete_student(student_id: str):
    """Delete a student and cascade associated assessments and logins (Administrator only)."""
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, user_id FROM students WHERE student_id = ?;", (student_id,))
        s_row = cur.fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Student not found.")

        user_id = s_row["user_id"]
        cur.execute("DELETE FROM students WHERE student_id = ?;", (student_id,))
        if user_id:
            cur.execute("DELETE FROM users WHERE id = ?;", (user_id,))

    return {"message": f"Student '{student_id}' and associated records successfully deleted."}
