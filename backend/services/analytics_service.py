"""
analytics_service.py — Descriptive academic analytics computed from actual database records
Strictly avoids hardcoded statistics; supports incomplete record handling.
"""

from typing import Any, Dict, List, Optional
from backend.config import ASSESSMENT_LIMITS
from backend.database import db_session
from backend.services.assessment_service import get_class_assessments


def get_class_dashboard_analytics(class_id: int) -> Dict[str, Any]:
    """
    Compute comprehensive mid-semester analytics for a given class:
    - Enrolled student count
    - Average total marks (from complete records only)
    - Highest & lowest mid-semester scores
    - Component-wise averages and percentage of maximum
    - Performance score distribution
    - Number of incomplete records
    """
    assessments = get_class_assessments(class_id)
    total_enrolled = len(assessments)

    if total_enrolled == 0:
        return {
            "class_id": class_id,
            "total_enrolled": 0,
            "complete_records_count": 0,
            "incomplete_records_count": 0,
            "average_total_marks": None,
            "highest_total_marks": None,
            "lowest_total_marks": None,
            "component_averages": {
                "midterm": {"average": None, "max": ASSESSMENT_LIMITS["midterm_max"], "pct": None},
                "assignment": {"average": None, "max": ASSESSMENT_LIMITS["assignment_max"], "pct": None},
                "presentation": {"average": None, "max": ASSESSMENT_LIMITS["presentation_max"], "pct": None},
                "attendance": {"average": None, "max": ASSESSMENT_LIMITS["attendance_max"], "pct": None},
                "sessional": {"average": None, "max": ASSESSMENT_LIMITS["sessional_max"], "pct": None},
            },
            "score_distribution": {
                "0–19.9": 0,
                "20–27.9": 0,
                "28–34.9": 0,
                "35–40.0": 0,
            },
            "support_needed_count": 0,
        }

    # Partition complete vs incomplete records
    complete_records = [a for a in assessments if a["is_complete"]]
    incomplete_records = [a for a in assessments if not a["is_complete"]]

    complete_count = len(complete_records)
    incomplete_count = len(incomplete_records)

    # Total score stats (only from complete records)
    if complete_count > 0:
        totals = [r["total_marks"] for r in complete_records]
        avg_total = round(sum(totals) / complete_count, 2)
        highest_total = max(totals)
        lowest_total = min(totals)
    else:
        avg_total = None
        highest_total = None
        lowest_total = None

    # Component-wise averages (from non-null entries)
    def calc_comp_avg(comp_key: str, max_val: float):
        vals = [r[comp_key] for r in assessments if r[comp_key] is not None]
        if not vals:
            return {"average": None, "max": max_val, "pct": None}
        avg = round(sum(vals) / len(vals), 2)
        pct = round((avg / max_val) * 100, 1)
        return {"average": avg, "max": max_val, "pct": pct}

    mid_stats = calc_comp_avg("midterm_marks", ASSESSMENT_LIMITS["midterm_max"])
    assign_stats = calc_comp_avg("assignment_marks", ASSESSMENT_LIMITS["assignment_max"])
    pres_stats = calc_comp_avg("presentation_marks", ASSESSMENT_LIMITS["presentation_max"])
    att_stats = calc_comp_avg("attendance_marks", ASSESSMENT_LIMITS["attendance_max"])

    # Sessional averages (where sessional_total is calculated)
    sessional_vals = [r["sessional_total"] for r in assessments if r["sessional_total"] is not None]
    if sessional_vals:
        sessional_avg = round(sum(sessional_vals) / len(sessional_vals), 2)
        sessional_pct = round((sessional_avg / ASSESSMENT_LIMITS["sessional_max"]) * 100, 1)
    else:
        sessional_avg = None
        sessional_pct = None

    # Performance distribution (4 bins across 0-40)
    # Bins: 0-19.9 (<50%), 20-27.9 (50-69%), 28-34.9 (70-87%), 35-40 (88-100%)
    dist = {
        "0–19.9": 0,
        "20–27.9": 0,
        "28–34.9": 0,
        "35–40.0": 0,
    }
    for r in complete_records:
        tot = r["total_marks"]
        if tot < 20.0:
            dist["0–19.9"] += 1
        elif tot < 28.0:
            dist["20–27.9"] += 1
        elif tot < 35.0:
            dist["28–34.9"] += 1
        else:
            dist["35–40.0"] += 1

    # Count of students who may benefit from support (low midterm, low sessional, or incomplete)
    support_count = 0
    for a in assessments:
        if not a["is_complete"]:
            support_count += 1
        elif a["total_marks"] < 20.0 or (a["midterm_marks"] and a["midterm_marks"] < 15.0) or (a["sessional_total"] and a["sessional_total"] < 5.0):
            support_count += 1

    # Class details
    class_info = None
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT class_name, section, academic_session FROM classes WHERE id = ?;", (class_id,))
        c_row = cur.fetchone()
        if c_row:
            class_info = dict(c_row)

    return {
        "class_id": class_id,
        "class_info": class_info,
        "total_enrolled": total_enrolled,
        "complete_records_count": complete_count,
        "incomplete_records_count": incomplete_count,
        "average_total_marks": avg_total,
        "highest_total_marks": highest_total,
        "lowest_total_marks": lowest_total,
        "component_averages": {
            "midterm": mid_stats,
            "assignment": assign_stats,
            "presentation": pres_stats,
            "attendance": att_stats,
            "sessional": {
                "average": sessional_avg,
                "max": ASSESSMENT_LIMITS["sessional_max"],
                "pct": sessional_pct,
            },
        },
        "score_distribution": dist,
        "support_needed_count": support_count,
    }
