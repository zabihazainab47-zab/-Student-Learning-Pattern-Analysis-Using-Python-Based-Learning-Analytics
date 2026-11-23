"""
class_routes.py — Academic class management and class-level retrieval
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth import get_current_user
from backend.database import db_session
from backend.permissions import require_roles
from backend.schemas import ClassCreate, ClassResponse

router = APIRouter(prefix="/api/classes", tags=["Classes"])


@router.get("", response_model=List[ClassResponse])
def list_classes(current_user: dict = Depends(get_current_user)):
    """
    List accessible classes:
    - Administrators: all classes in the system.
    - Teachers: only classes assigned to the authenticated teacher.
    - Students: their enrolled class only.
    """
    role = current_user.get("role")
    with db_session() as conn:
        cur = conn.cursor()

        if role in ("administrator", "admin"):
            cur.execute("""
                SELECT c.*, COUNT(s.id) as student_count
                FROM classes c
                LEFT JOIN students s ON c.id = s.class_id
                GROUP BY c.id
                ORDER BY c.class_name, c.section;
            """)
        elif role == "teacher":
            assigned_ids = current_user.get("assigned_class_ids", [])
            if not assigned_ids:
                return []
            placeholders = ",".join(["?"] * len(assigned_ids))
            cur.execute(f"""
                SELECT c.*, COUNT(s.id) as student_count
                FROM classes c
                LEFT JOIN students s ON c.id = s.class_id
                WHERE c.id IN ({placeholders})
                GROUP BY c.id
                ORDER BY c.class_name, c.section;
            """, assigned_ids)
        elif role == "student":
            class_id = current_user.get("class_id")
            if not class_id:
                return []
            cur.execute("""
                SELECT c.*, COUNT(s.id) as student_count
                FROM classes c
                LEFT JOIN students s ON c.id = s.class_id
                WHERE c.id = ?
                GROUP BY c.id;
            """, (class_id,))
        else:
            return []

        rows = cur.fetchall()
        return [
            ClassResponse(
                id=r["id"],
                class_name=r["class_name"],
                section=r["section"],
                academic_session=r["academic_session"],
                student_count=r["student_count"],
            )
            for r in rows
        ]


@router.post("", response_model=ClassResponse, dependencies=[Depends(require_roles("administrator"))])
def create_class(payload: ClassCreate):
    """Create a new class and section (Administrator only)."""
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM classes WHERE class_name = ? AND section = ? AND academic_session = ?;
        """, (payload.class_name, payload.section, payload.academic_session))
        if cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Class '{payload.class_name} {payload.section}' ({payload.academic_session}) already exists.",
            )

        cur.execute("""
            INSERT INTO classes (class_name, section, academic_session)
            VALUES (?, ?, ?);
        """, (payload.class_name, payload.section, payload.academic_session))
        new_id = cur.lastrowid

    return ClassResponse(
        id=new_id,
        class_name=payload.class_name,
        section=payload.section,
        academic_session=payload.academic_session,
        student_count=0,
    )
