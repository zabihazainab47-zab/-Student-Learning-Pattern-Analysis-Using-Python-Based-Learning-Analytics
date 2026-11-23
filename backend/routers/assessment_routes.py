"""
assessment_routes.py — Mid-semester assessment entry, update, and retrieval endpoints
Strictly enforces validation ranges and teacher-class permission boundaries.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth import get_current_user
from backend.permissions import check_student_record_access, check_teacher_class_access, require_roles
from backend.schemas import AssessmentResponse, AssessmentUpdate
from backend.services.assessment_service import (
    get_class_assessments,
    get_student_assessment,
    update_student_assessment,
)

router = APIRouter(prefix="/api/assessments", tags=["Assessments"])


@router.get("/{student_id}", response_model=AssessmentResponse)
def get_assessment(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get mid-semester assessment record for an individual student.
    - Students can only access their own record.
    - Teachers can only access students in their assigned classes.
    - Administrators can access any record.
    """
    # Permission verification
    check_student_record_access(current_user, student_id)

    record = get_student_assessment(student_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment record for student '{student_id}' not found.",
        )

    return AssessmentResponse(
        id=record.get("assessment_id"),
        student_id=record["student_id"],
        student_name=record["student_name"],
        class_id=record["class_id"],
        class_name=record["class_name"],
        section=record["section"],
        academic_session=record["academic_session"],
        midterm_marks=record.get("midterm_marks"),
        assignment_marks=record.get("assignment_marks"),
        presentation_marks=record.get("presentation_marks"),
        attendance_marks=record.get("attendance_marks"),
        sessional_total=record.get("sessional_total"),
        total_marks=record.get("total_marks"),
        is_complete=record.get("is_complete", False),
        missing_components=record.get("missing_components", []),
        updated_at=record.get("updated_at"),
        updated_by=record.get("updated_by"),
    )


@router.put("/{student_id}", response_model=AssessmentResponse)
def update_assessment(
    student_id: str,
    payload: AssessmentUpdate,
    current_user: dict = Depends(require_roles("administrator", "teacher")),
):
    """
    Enter or update mid-semester marks for a student.
    Teachers can only update marks for students in their assigned classes.
    Students can NEVER edit assessment records.
    Validation limits: Midterm (0-30), Assignment (0-3), Presentation (0-3), Attendance (0-4).
    """
    # Permission check for teacher assignment
    student_rec = check_student_record_access(current_user, student_id)
    if current_user.get("role") == "teacher":
        check_teacher_class_access(current_user, student_rec["class_id"])

    try:
        updated = update_student_assessment(
            student_id=student_id,
            midterm=payload.midterm_marks,
            assignment=payload.assignment_marks,
            presentation=payload.presentation_marks,
            attendance=payload.attendance_marks,
            updated_by=f"{current_user['username']} ({current_user['role']})",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    return AssessmentResponse(
        id=updated.get("assessment_id"),
        student_id=updated["student_id"],
        student_name=updated["student_name"],
        class_id=updated["class_id"],
        class_name=updated["class_name"],
        section=updated["section"],
        academic_session=updated["academic_session"],
        midterm_marks=updated.get("midterm_marks"),
        assignment_marks=updated.get("assignment_marks"),
        presentation_marks=updated.get("presentation_marks"),
        attendance_marks=updated.get("attendance_marks"),
        sessional_total=updated.get("sessional_total"),
        total_marks=updated.get("total_marks"),
        is_complete=updated.get("is_complete", False),
        missing_components=updated.get("missing_components", []),
        updated_at=updated.get("updated_at"),
        updated_by=updated.get("updated_by"),
    )


@router.get("/class/{class_id}", response_model=List[AssessmentResponse])
def get_class_assessment_list(
    class_id: int,
    current_user: dict = Depends(require_roles("administrator", "teacher")),
):
    """
    Retrieve all student assessment records for a specific class.
    Teachers are restricted to their assigned classes.
    """
    check_teacher_class_access(current_user, class_id)
    records = get_class_assessments(class_id)

    return [
        AssessmentResponse(
            id=r.get("assessment_id"),
            student_id=r["student_id"],
            student_name=r["student_name"],
            class_id=r["class_id"],
            class_name=r["class_name"],
            section=r["section"],
            academic_session=r["academic_session"],
            midterm_marks=r.get("midterm_marks"),
            assignment_marks=r.get("assignment_marks"),
            presentation_marks=r.get("presentation_marks"),
            attendance_marks=r.get("attendance_marks"),
            sessional_total=r.get("sessional_total"),
            total_marks=r.get("total_marks"),
            is_complete=r.get("is_complete", False),
            missing_components=r.get("missing_components", []),
            updated_at=r.get("updated_at"),
            updated_by=r.get("updated_by"),
        )
        for r in records
    ]
