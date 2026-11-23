"""
test_assessments.py — Unit tests for mid-semester assessment validation & calculations
"""

import unittest
from backend.utils.validators import validate_assessment_record, compute_totals, validate_component_mark


class TestAssessmentCalculations(unittest.TestCase):

    def test_exact_mid_semester_total(self):
        """Total = Midterm + Assignment + Presentation + Attendance (Max 40)."""
        midterm = 26.5
        assignment = 2.5
        presentation = 2.8
        attendance = 3.5

        records = validate_assessment_record(midterm, assignment, presentation, attendance)
        totals = compute_totals(
            records["midterm_marks"],
            records["assignment_marks"],
            records["presentation_marks"],
            records["attendance_marks"],
        )

        self.assertEqual(totals["sessional_total"], 8.8)  # 2.5 + 2.8 + 3.5 = 8.8
        self.assertEqual(totals["total_marks"], 35.3)     # 26.5 + 8.8 = 35.3
        self.assertTrue(totals["is_complete"])
        self.assertEqual(totals["missing_components"], [])

    def test_perfect_score_maximum_40(self):
        """Testing exact boundaries for maximum score: 30 + 3 + 3 + 4 = 40."""
        records = validate_assessment_record(30.0, 3.0, 3.0, 4.0)
        totals = compute_totals(
            records["midterm_marks"],
            records["assignment_marks"],
            records["presentation_marks"],
            records["attendance_marks"],
        )
        self.assertEqual(totals["sessional_total"], 10.0)
        self.assertEqual(totals["total_marks"], 40.0)
        self.assertTrue(totals["is_complete"])

    def test_missing_marks_remain_null(self):
        """
        Missing marks must remain NULL and not be treated as zero.
        Complete total must NOT be calculated when any required component is missing.
        """
        # Missing assignment and presentation
        records = validate_assessment_record(22.0, None, None, 3.0)
        totals = compute_totals(
            records["midterm_marks"],
            records["assignment_marks"],
            records["presentation_marks"],
            records["attendance_marks"],
        )

        self.assertIsNone(totals["total_marks"])
        self.assertIsNone(totals["sessional_total"])
        self.assertFalse(totals["is_complete"])
        self.assertIn("assignment", totals["missing_components"])
        self.assertIn("presentation", totals["missing_components"])

    def test_missing_single_component_prevents_total(self):
        """If only attendance is missing, complete total is None."""
        records = validate_assessment_record(25.0, 2.5, 2.5, None)
        totals = compute_totals(
            records["midterm_marks"],
            records["assignment_marks"],
            records["presentation_marks"],
            records["attendance_marks"],
        )
        self.assertIsNone(totals["total_marks"])
        self.assertFalse(totals["is_complete"])
        self.assertEqual(totals["missing_components"], ["attendance"])

    def test_invalid_midterm_out_of_range(self):
        """Midterm marks > 30 or < 0 must be rejected."""
        with self.assertRaises(ValueError):
            validate_assessment_record(30.5, 2.0, 2.0, 3.0)
        with self.assertRaises(ValueError):
            validate_assessment_record(-1.0, 2.0, 2.0, 3.0)

    def test_invalid_assignment_out_of_range(self):
        """Assignment marks > 3 or < 0 must be rejected."""
        with self.assertRaises(ValueError):
            validate_assessment_record(20.0, 3.5, 2.0, 3.0)
        with self.assertRaises(ValueError):
            validate_assessment_record(20.0, -0.5, 2.0, 3.0)

    def test_invalid_presentation_out_of_range(self):
        """Presentation marks > 3 or < 0 must be rejected."""
        with self.assertRaises(ValueError):
            validate_assessment_record(20.0, 2.0, 4.0, 3.0)

    def test_invalid_attendance_percentage_rejected(self):
        """
        Attendance must be entered as marks out of 4, NOT as a percentage.
        E.g. entering 85 for attendance must be rejected!
        """
        with self.assertRaises(ValueError):
            validate_assessment_record(20.0, 2.0, 2.0, 85.0)

    def test_non_numeric_marks_rejected(self):
        """String or invalid symbols must raise ValueError."""
        with self.assertRaises(ValueError):
            validate_assessment_record("invalid", 2.0, 2.0, 3.0)


if __name__ == "__main__":
    unittest.main()
