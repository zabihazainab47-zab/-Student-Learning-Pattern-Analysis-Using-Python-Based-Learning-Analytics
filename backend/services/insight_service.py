"""
insight_service.py — Human-centred, evidence-based academic support insights
Generates traceable observations from actual assessment records without reductionist labeling.
"""

from typing import Any, Dict, List, Optional
from backend.config import ASSESSMENT_LIMITS
from backend.services.assessment_service import get_class_assessments, get_student_assessment


def generate_student_observations(assessment: Dict[str, Any]) -> List[str]:
    """
    Generate evidence-based academic feedback for an individual student.
    Strictly traceable to numeric marks. Avoids psychological diagnoses or fixed labels.
    """
    observations = []

    mid = assessment.get("midterm_marks")
    assign = assessment.get("assignment_marks")
    pres = assessment.get("presentation_marks")
    att = assessment.get("attendance_marks")
    total = assessment.get("total_marks")
    is_complete = assessment.get("is_complete", False)
    missing = assessment.get("missing_components", [])

    # 1. Missing component observations
    if not is_complete:
        missing_names = ", ".join([m.capitalize() for m in missing])
        observations.append(
            f"Assessment record is incomplete: {missing_names} mark(s) are currently unrecorded. "
            "Please ensure all required assessment components are submitted and recorded."
        )

    # 2. Component ratios (percentage of component maximum)
    ratios = {}
    if mid is not None:
        ratios["midterm"] = (mid / ASSESSMENT_LIMITS["midterm_max"]) * 100
    if assign is not None:
        ratios["assignment"] = (assign / ASSESSMENT_LIMITS["assignment_max"]) * 100
    if pres is not None:
        ratios["presentation"] = (pres / ASSESSMENT_LIMITS["presentation_max"]) * 100
    if att is not None:
        ratios["attendance"] = (att / ASSESSMENT_LIMITS["attendance_max"]) * 100

    if ratios:
        min_comp = min(ratios, key=ratios.get)
        max_comp = max(ratios, key=ratios.get)
        min_pct = ratios[min_comp]
        max_pct = ratios[max_comp]

        # Component divergence check (e.g. difference > 30 percentage points)
        if (max_pct - min_pct) >= 30.0:
            observations.append(
                f"Noticeable component divergence: {min_comp.capitalize()} ({min_pct:.0f}% of component max) is "
                f"significantly lower than your performance in {max_comp} ({max_pct:.0f}% of max). "
                f"Discuss targeted improvement strategies for {min_comp} with your course instructor."
            )

        # Low attendance check (<= 50% of attendance marks)
        if att is not None and att < 2.0:
            observations.append(
                f"Class attendance is recorded at {att:.1f}/4.0 marks. "
                "Regular attendance and classroom engagement are strongly recommended."
            )

        # Low assignment check
        if assign is not None and assign < 1.5:
            observations.append(
                f"Assignment marks are {assign:.1f}/3.0. "
                "Review the assignment feedback and consider consulting the instructor for guidance on future coursework."
            )

        # Low presentation check
        if pres is not None and pres < 1.5:
            observations.append(
                f"Presentation score is {pres:.1f}/3.0. "
                "Practice sessions and structured slide preparation may help strengthen presentation delivery."
            )

        # Strong consistent performance
        if is_complete and all(pct >= 80.0 for pct in ratios.values()):
            observations.append(
                "Consistent performance demonstrated across all four mid-semester assessment components. "
                "Maintain your disciplined study pattern."
            )

    if not observations:
        observations.append(
            "Academic performance is progressing steadily within expected mid-semester ranges. "
            "Continue engaging actively in lecture and tutorial sessions."
        )

    return observations


def generate_class_support_insights(class_id: int) -> List[Dict[str, Any]]:
    """
    Generate evidence-based support insights for an entire class to aid instructor decision-making.
    Identifies:
    1. Incomplete records requiring mark entries
    2. Component divergence (e.g. high midterm, low sessional or vice versa)
    3. Low component-specific scores (e.g. low attendance, low assignment)
    4. Students whose total mid-semester score falls below 50% (< 20/40)
    """
    assessments = get_class_assessments(class_id)
    insights = []

    for a in assessments:
        stu_id = a["student_id"]
        stu_name = a["student_name"]
        cls_name = a["class_name"]
        section = a["section"]
        mid = a["midterm_marks"]
        assign = a["assignment_marks"]
        pres = a["presentation_marks"]
        att = a["attendance_marks"]
        sessional = a["sessional_total"]
        total = a["total_marks"]
        missing = a["missing_components"]

        # 1. Incomplete records
        if not a["is_complete"]:
            missing_str = ", ".join([m.capitalize() for m in missing])
            insights.append({
                "student_id": stu_id,
                "student_name": stu_name,
                "class_name": cls_name,
                "section": section,
                "insight_type": "Incomplete Assessment Record",
                "category": "Data Completeness",
                "severity": "High",
                "description": f"Missing components: {missing_str}. Complete total cannot be derived.",
                "recommendation": "Review attendance sheets or grade books to record the missing assessment mark.",
                "data_trace": {
                    "midterm": mid,
                    "assignment": assign,
                    "presentation": pres,
                    "attendance": att,
                    "missing": missing,
                },
            })

        # 2. Overall marks below 50% (total < 20/40)
        if a["is_complete"] and total is not None and total < 20.0:
            insights.append({
                "student_id": stu_id,
                "student_name": stu_name,
                "class_name": cls_name,
                "section": section,
                "insight_type": "Total Marks Below 50%",
                "category": "Overall Performance",
                "severity": "Attention",
                "description": f"Total mid-semester marks: {total:.1f}/40.0. Student is currently performing below the midpoint.",
                "recommendation": "Offer an academic advisory consultation to explore course understanding and tutorial support.",
                "data_trace": {
                    "total_marks": total,
                    "midterm": mid,
                    "sessional": sessional,
                },
            })

        # 3. Component divergence: High Midterm (>= 22/30) but Low Sessional (< 5.0/10)
        if mid is not None and sessional is not None:
            mid_pct = (mid / ASSESSMENT_LIMITS["midterm_max"]) * 100
            sess_pct = (sessional / ASSESSMENT_LIMITS["sessional_max"]) * 100
            if mid_pct >= 75.0 and sess_pct < 50.0:
                insights.append({
                    "student_id": stu_id,
                    "student_name": stu_name,
                    "class_name": cls_name,
                    "section": section,
                    "insight_type": "Component Divergence: Strong Exam, Low Sessional",
                    "category": "Engagement Pattern",
                    "severity": "Moderate",
                    "description": f"Scored {mid:.1f}/30 on midterm ({mid_pct:.0f}%), but only {sessional:.1f}/10 on sessional coursework ({sess_pct:.0f}%).",
                    "recommendation": "Inquire whether the student faced hurdles submitting coursework on time despite strong exam mastery.",
                    "data_trace": {
                        "midterm_marks": mid,
                        "sessional_total": sessional,
                        "assignment": assign,
                        "presentation": pres,
                        "attendance": att,
                    },
                })
            elif sess_pct >= 80.0 and mid_pct < 50.0:
                insights.append({
                    "student_id": stu_id,
                    "student_name": stu_name,
                    "class_name": cls_name,
                    "section": section,
                    "insight_type": "Component Divergence: Active Sessional, Exam Difficulty",
                    "category": "Exam Preparation",
                    "severity": "Moderate",
                    "description": f"Maintains strong sessional marks ({sessional:.1f}/10, {sess_pct:.0f}%), but scored {mid:.1f}/30 ({mid_pct:.0f}%) on midterm examination.",
                    "recommendation": "Discuss exam preparation techniques, time management during timed tests, or review difficult exam questions.",
                    "data_trace": {
                        "midterm_marks": mid,
                        "sessional_total": sessional,
                    },
                })

        # 4. Low Attendance Concern (< 2.0/4 marks)
        if att is not None and att < 2.0:
            insights.append({
                "student_id": stu_id,
                "student_name": stu_name,
                "class_name": cls_name,
                "section": section,
                "insight_type": "Attendance Concern",
                "category": "Attendance & Participation",
                "severity": "Attention",
                "description": f"Attendance is recorded at {att:.1f}/4.0 marks ({att/4*100:.0f}%).",
                "recommendation": "Check in with the student regarding lecture attendance and offer class notes or makeup opportunities.",
                "data_trace": {
                    "attendance_marks": att,
                },
            })

    return insights
