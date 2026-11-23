"""
auth.py — Authentication dependency and user verification
"""

from typing import Any, Dict, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.database import (
    get_connection,
    get_student_by_user_id,
    get_teacher_assigned_class_ids,
    get_teacher_by_user_id,
    get_user_by_username,
)
from backend.utils.security import decode_access_token, verify_password

security = HTTPBearer()


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user against database with bcrypt password verification."""
    user = get_user_by_username(username)
    if not user:
        return None
    if user.get("status") != "active":
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """FastAPI dependency to extract and validate authenticated user from Bearer JWT."""
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired authentication token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: str = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_username(username)
    if not user or user.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Attach profile metadata based on role
    user_context = {
        "user_id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "status": user["status"],
    }

    if user["role"] == "teacher":
        teacher = get_teacher_by_user_id(user["id"])
        if teacher:
            user_context["teacher_id"] = teacher["id"]
            user_context["display_name"] = teacher["teacher_name"]
            user_context["assigned_class_ids"] = get_teacher_assigned_class_ids(teacher["id"])
        else:
            user_context["teacher_id"] = None
            user_context["display_name"] = user["username"]
            user_context["assigned_class_ids"] = []

    elif user["role"] == "student":
        student = get_student_by_user_id(user["id"])
        if student:
            user_context["student_db_id"] = student["id"]
            user_context["student_id"] = student["student_id"]
            user_context["display_name"] = student["student_name"]
            user_context["class_id"] = student["class_id"]
        else:
            user_context["student_id"] = None
            user_context["display_name"] = user["username"]

    else:
        # administrator
        user_context["display_name"] = "Administrator"

    return user_context
