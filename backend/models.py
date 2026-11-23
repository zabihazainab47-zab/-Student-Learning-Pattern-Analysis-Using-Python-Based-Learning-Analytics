"""
models.py — Data models and schema definitions for Student Learning Pattern Analysis
Reflects the 6-table normalized relational schema.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: int
    username: str
    password_hash: str
    role: str  # 'administrator', 'teacher', 'student'
    status: str = "active"
    created_at: Optional[str] = None


@dataclass
class Teacher:
    id: int
    user_id: int
    teacher_name: str


@dataclass
class AcademicClass:
    id: int
    class_name: str
    section: str
    academic_session: str


@dataclass
class Student:
    id: int
    student_id: str
    student_name: str
    class_id: int
    user_id: Optional[int] = None


@dataclass
class TeacherClass:
    id: int
    teacher_id: int
    class_id: int


@dataclass
class AssessmentRecord:
    id: int
    student_id: int
    midterm_marks: Optional[float]
    assignment_marks: Optional[float]
    presentation_marks: Optional[float]
    attendance_marks: Optional[float]
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None
