"""
test_permissions.py — Unit tests for role-based permissions and scoping constraints
"""

import unittest
from fastapi import HTTPException
from backend.permissions import check_student_record_access, check_teacher_class_access


class TestRolePermissions(unittest.TestCase):

    def setUp(self):
        # Sample simulated users
        self.admin_user = {
            "user_id": 1,
            "username": "admin",
            "role": "administrator",
        }
        self.teacher1_user = {
            "user_id": 2,
            "username": "teacher1",
            "role": "teacher",
            "teacher_id": 1,
            "assigned_class_ids": [1, 3],  # Assigned to Class 1 (BSIT-A) and 3 (BSCS-A)
        }
        self.teacher2_user = {
            "user_id": 3,
            "username": "teacher2",
            "role": "teacher",
            "teacher_id": 2,
            "assigned_class_ids": [2],     # Assigned to Class 2 (BSIT-B) only
        }
        self.student_user = {
            "user_id": 4,
            "username": "FA22-BIT-A-001",
            "role": "student",
            "student_id": "FA22-BIT-A-001",
            "class_id": 1,
        }

    def test_admin_has_global_class_access(self):
        """Admin can access any class ID."""
        self.assertTrue(check_teacher_class_access(self.admin_user, 1))
        self.assertTrue(check_teacher_class_access(self.admin_user, 2))
        self.assertTrue(check_teacher_class_access(self.admin_user, 999))

    def test_teacher_assigned_class_access_granted(self):
        """Teacher 1 can access class 1 and class 3."""
        self.assertTrue(check_teacher_class_access(self.teacher1_user, 1))
        self.assertTrue(check_teacher_class_access(self.teacher1_user, 3))

    def test_teacher_unassigned_class_access_forbidden(self):
        """Teacher 1 CANNOT access class 2 (assigned to Teacher 2). Raises HTTP 403."""
        with self.assertRaises(HTTPException) as ctx:
            check_teacher_class_access(self.teacher1_user, 2)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("not assigned", ctx.exception.detail)

    def test_student_cannot_access_class_level_data(self):
        """Students cannot access teacher class dashboards. Raises HTTP 403."""
        with self.assertRaises(HTTPException) as ctx:
            check_teacher_class_access(self.student_user, 1)
        self.assertEqual(ctx.exception.status_code, 403)

    def test_student_can_view_own_record(self):
        """Student can view their own student ID profile."""
        rec = check_student_record_access(self.student_user, "FA22-BIT-A-001")
        self.assertEqual(rec["student_id"], "FA22-BIT-A-001")

    def test_student_forbidden_from_viewing_other_student(self):
        """Student cannot view another student's record. Raises HTTP 403."""
        with self.assertRaises(HTTPException) as ctx:
            check_student_record_access(self.student_user, "FA22-BIT-A-002")
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("strictly prohibited", ctx.exception.detail)

    def test_teacher_can_view_student_in_assigned_class(self):
        """Teacher 1 can view student in class 1 (BSIT-A)."""
        rec = check_student_record_access(self.teacher1_user, "FA22-BIT-A-001")
        self.assertEqual(rec["student_id"], "FA22-BIT-A-001")

    def test_teacher_cannot_view_student_in_unassigned_class(self):
        """Teacher 1 cannot view student in class 2 (BSIT-B). Raises HTTP 403."""
        with self.assertRaises(HTTPException) as ctx:
            check_student_record_access(self.teacher1_user, "FA22-BIT-B-001")
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("not assigned to you", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
