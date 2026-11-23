"""
permissions.py — Role-based authorization and class/student scoping checks
"""

from typing import Any, Callable, Dict, List, Optional
from fastapi import Depends, HTTPException, status
from backend.auth import get_current_user
from backend.database import get_connection


def require_roles(*allowed_roles: str) -> Callable:
    """Dependency factory ensuring user has one of the required roles."""
    def role_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = user.get("role")
        # Support both 'admin' and 'administrator' alias
        normalized_role = "administrator" if user_role == "admin" else user_role
        normalized_allowed = [
            "administrator" if r == "admin" else r for r in allowed_roles
        ]
        if normalized_role not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_roles}. Your role: '{user_role}'.",
            )
        return user
    return role_checker


def check_teacher_class_access(user: Dict[str, Any], class_id: int) -> bool:
    """
    Ensure teacher can only view or manage records for their assigned classes.
    Administrators have global access.
    Raises 403 HTTPException if unauthorized.
    """
    role = user.get("role")
    if role in ("administrator", "admin"):
        return True

    if role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers or administrators can access class data.",
        )

    assigned_classes = user.get("assigned_class_ids", [])
    if class_id not in assigned_classes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Class ID {class_id} is not assigned to your instructor profile.",
        )

    return True


def check_student_record_access(user: Dict[str, Any], target_student_id: str) -> Dict[str, Any]:
    """
    Check if user is authorized to view a specific student's record.
    - Students: can ONLY access their own student_id.
    - Teachers: can ONLY access students in classes assigned to them.
    - Administrators: can access all student records.
    Returns the student database record if allowed, raises 403 or 404.
    """
    role = user.get("role")
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT s.*, c.class_name, c.section, c.academic_session
        FROM students s
        JOIN classes c ON s.class_id = c.id
        WHERE s.student_id = ?;
    """, (target_student_id,))
    student_row = cur.fetchone()
    conn.close()

    if not student_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student record with ID '{target_student_id}' not found.",
        )

    student_data = dict(student_row)

    if role in ("administrator", "admin"):
        return student_data

    if role == "student":
        user_student_id = user.get("student_id")
        if user_student_id != target_student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students are strictly prohibited from viewing other students' records.",
            )
        return student_data

    if role == "teacher":
        assigned_classes = user.get("assigned_class_ids", [])
        if student_data["class_id"] not in assigned_classes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. This student is in a class that is not assigned to you.",
            )
        return student_data

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Unauthorized access.",
    )
