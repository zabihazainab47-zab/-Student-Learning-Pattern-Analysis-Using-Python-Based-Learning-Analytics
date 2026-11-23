"""
auth_routes.py — Authentication endpoints: login, token issuance, and profile check
"""

from fastapi import APIRouter, Depends, HTTPException, status
from backend.auth import authenticate_user, get_current_user
from backend.schemas import LoginRequest, TokenResponse
from backend.utils.security import create_access_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    """Authenticate with username and password, returns signed Bearer JWT token."""
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    # Context payload for token
    token_data = {
        "sub": user["username"],
        "user_id": user["id"],
        "role": user["role"],
    }
    access_token = create_access_token(token_data)

    # Fetch display info
    from backend.auth import get_teacher_by_user_id, get_student_by_user_id
    display_name = user["username"]
    teacher_id = None
    student_id = None

    if user["role"] == "teacher":
        t = get_teacher_by_user_id(user["id"])
        if t:
            display_name = t["teacher_name"]
            teacher_id = t["id"]
    elif user["role"] == "student":
        s = get_student_by_user_id(user["id"])
        if s:
            display_name = s["student_name"]
            student_id = s["student_id"]
    else:
        display_name = "Administrator"

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user["role"],
        user_id=user["id"],
        username=user["username"],
        display_name=display_name,
        student_id=student_id,
        teacher_id=teacher_id,
    )


@router.get("/me")
def get_authenticated_profile(current_user: dict = Depends(get_current_user)):
    """Return user profile and permission scope."""
    return current_user
