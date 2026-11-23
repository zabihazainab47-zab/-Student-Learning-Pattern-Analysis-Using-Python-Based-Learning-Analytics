"""
dashboard_routes.py — Dashboard analytics, visualisations data, and support insights
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth import get_current_user
from backend.permissions import (
    check_student_record_access,
    check_teacher_class_access,
    require_roles,
)
from backend.services.analytics_service import get_class_dashboard_analytics
from backend.services.assessment_service import get_student_assessment
from backend.services.insight_service import (
    generate_class_support_insights,
    generate_student_observations,
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/class/{class_id}")
def get_class_analytics(
    class_id: int,
    current_user: dict = Depends(require_roles("administrator", "teacher")),
):
    """
    Get full class-level performance analytics for the teacher dashboard.
    Enforces teacher-class assignment boundaries.
    """
    check_teacher_class_access(current_user, class_id)
    analytics = get_class_dashboard_analytics(class_id)
    return analytics


@router.get("/insights/class/{class_id}")
def get_class_insights(
    class_id: int,
    current_user: dict = Depends(require_roles("administrator", "teacher")),
):
    """
    Get evidence-based support insights for students in an assigned class.
    Identifies incomplete records, component divergence, low component marks.
    """
    check_teacher_class_access(current_user, class_id)
    insights = generate_class_support_insights(class_id)
    return {
        "class_id": class_id,
        "total_insights": len(insights),
        "insights": insights,
    }


@router.get("/student/{student_id}/progress")
def get_student_progress_page(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get individual student progress page:
    - Assessment breakdown (Mid 30, Assignment 3, Presentation 3, Attendance 4)
    - Sessional total (out of 10) and total marks (out of 40)
    - Evidence-based progress observations
    Students can ONLY access their own progress page.
    """
    check_student_record_access(current_user, student_id)
    assessment = get_student_assessment(student_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Student assessment record not found.")

    observations = generate_student_observations(assessment)

    # Component ratios for radar/bar charts
    components_breakdown = [
        {
            "component": "Midterm Examination",
            "score": assessment.get("midterm_marks"),
            "max": 30.0,
            "pct": round((assessment["midterm_marks"] / 30.0 * 100), 1) if assessment.get("midterm_marks") is not None else None,
        },
        {
            "component": "Assignment",
            "score": assessment.get("assignment_marks"),
            "max": 3.0,
            "pct": round((assessment["assignment_marks"] / 3.0 * 100), 1) if assessment.get("assignment_marks") is not None else None,
        },
        {
            "component": "Presentation",
            "score": assessment.get("presentation_marks"),
            "max": 3.0,
            "pct": round((assessment["presentation_marks"] / 3.0 * 100), 1) if assessment.get("presentation_marks") is not None else None,
        },
        {
            "component": "Attendance",
            "score": assessment.get("attendance_marks"),
            "max": 4.0,
            "pct": round((assessment["attendance_marks"] / 4.0 * 100), 1) if assessment.get("attendance_marks") is not None else None,
        },
    ]

    return {
        "student_profile": {
            "student_id": assessment["student_id"],
            "student_name": assessment["student_name"],
            "class_name": assessment["class_name"],
            "section": assessment["section"],
            "academic_session": assessment["academic_session"],
        },
        "assessment": {
            "midterm_marks": assessment.get("midterm_marks"),
            "assignment_marks": assessment.get("assignment_marks"),
            "presentation_marks": assessment.get("presentation_marks"),
            "attendance_marks": assessment.get("attendance_marks"),
            "sessional_total": assessment.get("sessional_total"),
            "total_marks": assessment.get("total_marks"),
            "is_complete": assessment.get("is_complete", False),
            "missing_components": assessment.get("missing_components", []),
            "updated_at": assessment.get("updated_at"),
            "updated_by": assessment.get("updated_by"),
        },
        "components_breakdown": components_breakdown,
        "observations": observations,
    }
