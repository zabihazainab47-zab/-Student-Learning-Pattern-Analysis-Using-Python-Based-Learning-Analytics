"""
schemas.py — Pydantic models for request/response serialization and validation
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ── Auth Schemas ───────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    username: str
    display_name: str
    student_id: Optional[str] = None
    teacher_id: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    status: str
    created_at: Optional[str] = None


# ── Class Schemas ──────────────────────────────────────────────────

class ClassCreate(BaseModel):
    class_name: str
    section: str
    academic_session: str


class ClassResponse(BaseModel):
    id: int
    class_name: str
    section: str
    academic_session: str
    student_count: Optional[int] = 0


# ── Teacher Schemas ────────────────────────────────────────────────

class TeacherCreate(BaseModel):
    username: str
    password: str
    teacher_name: str
    assigned_class_ids: Optional[List[int]] = []


class TeacherResponse(BaseModel):
    id: int
    user_id: int
    teacher_name: str
    username: str
    assigned_classes: List[ClassResponse] = []


class TeacherClassAssignRequest(BaseModel):
    teacher_id: int
    class_ids: List[int]


# ── Student Schemas ────────────────────────────────────────────────

class StudentCreate(BaseModel):
    student_id: str
    student_name: str
    class_id: int
    create_user_account: bool = True
    default_password: Optional[str] = "student123"


class StudentUpdate(BaseModel):
    student_name: Optional[str] = None
    class_id: Optional[int] = None


class StudentResponse(BaseModel):
    id: int
    student_id: str
    student_name: str
    class_id: int
    class_name: str
    section: str
    academic_session: str
    user_id: Optional[int] = None


# ── Assessment Schemas ─────────────────────────────────────────────

class AssessmentUpdate(BaseModel):
    midterm_marks: Optional[float] = Field(None, ge=0.0, le=30.0)
    assignment_marks: Optional[float] = Field(None, ge=0.0, le=3.0)
    presentation_marks: Optional[float] = Field(None, ge=0.0, le=3.0)
    attendance_marks: Optional[float] = Field(None, ge=0.0, le=4.0)


class AssessmentResponse(BaseModel):
    id: Optional[int] = None
    student_id: str
    student_name: str
    class_id: int
    class_name: str
    section: str
    academic_session: str
    midterm_marks: Optional[float] = None
    assignment_marks: Optional[float] = None
    presentation_marks: Optional[float] = None
    attendance_marks: Optional[float] = None
    sessional_total: Optional[float] = None
    total_marks: Optional[float] = None
    is_complete: bool
    missing_components: List[str] = []
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None


# ── Dashboard & Analytics Schemas ──────────────────────────────────

class ComponentAverage(BaseModel):
    component: str
    average: Optional[float]
    maximum: float
    percentage_of_max: Optional[float]


class DashboardStatsResponse(BaseModel):
    class_id: Optional[int] = None
    class_name: Optional[str] = None
    section: Optional[str] = None
    total_enrolled: int
    complete_records_count: int
    incomplete_records_count: int
    average_total_marks: Optional[float]
    highest_total_marks: Optional[float]
    lowest_total_marks: Optional[float]
    component_averages: Dict[str, ComponentAverage]
    score_distribution: Dict[str, int]
    support_needed_count: int


# ── Support Insight Schemas ────────────────────────────────────────

class SupportInsight(BaseModel):
    student_id: str
    student_name: str
    class_name: str
    section: str
    insight_type: str  # 'incomplete_record', 'low_component', 'component_divergence', 'low_sessional'
    description: str
    recommendation: str
    data_trace: Dict[str, Any]
