"""
validators.py — Assessment data validation and calculation logic
"""

from typing import Dict, Optional, Tuple, Any
from backend.config import ASSESSMENT_LIMITS


def validate_component_mark(
    component_name: str,
    value: Optional[float],
    min_val: float,
    max_val: float,
    allow_null: bool = True
) -> Optional[float]:
    """
    Validate a single assessment component mark.
    Rejects values outside range. Returns float or None.
    Does NOT silently change values.
    """
    if value is None or value == "":
        if not allow_null:
            raise ValueError(f"{component_name} cannot be null or empty.")
        return None

    try:
        val_float = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{component_name} must be a valid numeric mark, got '{value}'.")

    if val_float < min_val or val_float > max_val:
        raise ValueError(
            f"{component_name} mark must be between {min_val} and {max_val}. Got {val_float}."
        )

    return round(val_float, 2)


def validate_assessment_record(
    midterm: Optional[float],
    assignment: Optional[float],
    presentation: Optional[float],
    attendance: Optional[float],
) -> Dict[str, Optional[float]]:
    """
    Validate the four mid-semester assessment components:
    - Midterm: 0–30
    - Assignment: 0–3
    - Presentation: 0–3
    - Attendance: 0–4 (marks out of 4, NOT percentage)

    Returns validated dictionary of marks.
    Raises ValueError on invalid values.
    """
    valid_midterm = validate_component_mark(
        "Midterm examination", midterm, 0.0, ASSESSMENT_LIMITS["midterm_max"], allow_null=True
    )
    valid_assignment = validate_component_mark(
        "Assignment", assignment, 0.0, ASSESSMENT_LIMITS["assignment_max"], allow_null=True
    )
    valid_presentation = validate_component_mark(
        "Presentation", presentation, 0.0, ASSESSMENT_LIMITS["presentation_max"], allow_null=True
    )
    valid_attendance = validate_component_mark(
        "Attendance", attendance, 0.0, ASSESSMENT_LIMITS["attendance_max"], allow_null=True
    )

    return {
        "midterm_marks": valid_midterm,
        "assignment_marks": valid_assignment,
        "presentation_marks": valid_presentation,
        "attendance_marks": valid_attendance,
    }


def compute_totals(
    midterm: Optional[float],
    assignment: Optional[float],
    presentation: Optional[float],
    attendance: Optional[float],
) -> Dict[str, Any]:
    """
    Calculates sessional marks and total marks.
    Rule:
    - Sessional = Assignment + Presentation + Attendance (Max 10)
    - Total = Midterm + Assignment + Presentation + Attendance (Max 40)
    - Missing marks must remain NULL. Do not treat missing marks as zero.
    - Do not calculate a complete total when any of the 4 required assessment components are missing.
    """
    components = [midterm, assignment, presentation, attendance]
    has_missing = any(c is None for c in components)

    # Sessional calculation (assignment + presentation + attendance)
    sessional_components = [assignment, presentation, attendance]
    sessional_has_missing = any(c is None for c in sessional_components)
    sessional_total = (
        round(assignment + presentation + attendance, 2)
        if not sessional_has_missing
        else None
    )

    # Complete mid-semester total (out of 40)
    complete_total = (
        round(midterm + assignment + presentation + attendance, 2)
        if not has_missing
        else None
    )

    # Check that computed total does not exceed 40
    if complete_total is not None and complete_total > ASSESSMENT_LIMITS["total_max"]:
        raise ValueError(
            f"Calculated total ({complete_total}) exceeds maximum of {ASSESSMENT_LIMITS['total_max']}."
        )

    return {
        "sessional_total": sessional_total,
        "total_marks": complete_total,
        "is_complete": not has_missing,
        "missing_components": [
            name
            for name, val in [
                ("midterm", midterm),
                ("assignment", assignment),
                ("presentation", presentation),
                ("attendance", attendance),
            ]
            if val is None
        ],
    }
