"""
test_csv.py — Unit tests for CSV import validation, error reporting, and export scoping
"""

import unittest
from backend.services.csv_service import export_students_csv, import_students_csv


class TestCSVProcessing(unittest.TestCase):

    def setUp(self):
        self.admin_user = {
            "user_id": 1,
            "username": "admin",
            "role": "administrator",
        }
        self.teacher1_user = {
            "user_id": 2,
            "username": "teacher1",
            "role": "teacher",
            "assigned_class_ids": [1, 3],  # Class 1 (BSIT-A), Class 3 (BSCS-A)
        }

    def test_valid_csv_import(self):
        """Valid CSV rows are imported and counts are reported."""
        csv_data = """student_id,student_name,class,section,midterm,assignment,presentation,attendance
CSV-TEST-001,Test Student One,BSIT,Section A,24.5,2.5,2.5,3.5
CSV-TEST-002,Test Student Two,BSIT,Section A,21.0,2.0,2.0,3.0
"""
        result = import_students_csv(csv_data, user=self.admin_user, overwrite=True)
        self.assertEqual(result["total_rows"], 2)
        self.assertEqual(result["imported_count"], 2)
        self.assertEqual(result["skipped_count"], 0)
        self.assertEqual(result["errors"], [])

    def test_invalid_marks_rejected_with_exact_reason(self):
        """Out-of-range marks (e.g. midterm > 30, attendance as percentage) must be rejected."""
        csv_data = """student_id,student_name,class,section,midterm,assignment,presentation,attendance
CSV-INV-001,Midterm Too High,BSIT,Section A,35.0,2.0,2.0,3.0
CSV-INV-002,Attendance As Percent,BSIT,Section A,22.0,2.0,2.0,85.0
CSV-INV-003,Assignment Out of Range,BSIT,Section A,20.0,5.0,2.0,3.0
"""
        result = import_students_csv(csv_data, user=self.admin_user, overwrite=True)
        self.assertEqual(result["imported_count"], 0)
        self.assertEqual(result["skipped_count"], 3)
        self.assertEqual(len(result["errors"]), 3)
        self.assertTrue(any("midterm" in e.lower() for e in result["errors"]))
        self.assertTrue(any("attendance" in e.lower() for e in result["errors"]))
        self.assertTrue(any("assignment" in e.lower() for e in result["errors"]))

    def test_batch_duplicate_id_detection(self):
        """Duplicate student IDs within the same CSV batch must be flagged and skipped."""
        csv_data = """student_id,student_name,class,section,midterm,assignment,presentation,attendance
CSV-DUP-001,Original Name,BSIT,Section A,20,2,2,3
CSV-DUP-001,Duplicate Row,BSIT,Section A,22,2,2,3
"""
        result = import_students_csv(csv_data, user=self.admin_user, overwrite=True)
        self.assertEqual(result["imported_count"], 1)
        self.assertEqual(result["skipped_count"], 1)
        self.assertTrue(any("Duplicate student ID" in e for e in result["errors"]))

    def test_teacher_import_permission_enforcement(self):
        """Teacher cannot import students into an unassigned class."""
        # Teacher 1 is assigned to BSIT Section A (id 1) and BSCS Section A (id 3), NOT BSIT Section B (id 2)
        csv_data = """student_id,student_name,class,section,midterm,assignment,presentation,attendance
CSV-UNASSIGNED,Forbidden Import,BSIT,Section B,25,2,2,3
"""
        result = import_students_csv(csv_data, user=self.teacher1_user, overwrite=True)
        self.assertEqual(result["imported_count"], 0)
        self.assertEqual(result["skipped_count"], 1)
        self.assertTrue(any("Permission denied" in e for e in result["errors"]))

    def test_export_does_not_expose_auth_secrets(self):
        """Exported CSV must only contain academic assessment fields; never passwords or hashes."""
        csv_out = export_students_csv(self.admin_user)
        self.assertIn("student_id,student_name,class,section,midterm,assignment,presentation,attendance", csv_out)
        self.assertNotIn("password", csv_out.lower())
        self.assertNotIn("hash", csv_out.lower())
        self.assertNotIn("token", csv_out.lower())


if __name__ == "__main__":
    unittest.main()
