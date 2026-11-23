"""
test_auth.py — Unit tests for authentication, password hashing, and token issuance
"""

import unittest
from backend.auth import authenticate_user
from backend.routers.auth_routes import login
from backend.schemas import LoginRequest
from backend.utils.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class TestAuthentication(unittest.TestCase):

    def test_password_hashing_and_verification(self):
        """Test bcrypt password hashing and verification."""
        pwd = "TestSecurePassword2026!"
        h = hash_password(pwd)
        self.assertNotEqual(pwd, h)
        self.assertTrue(verify_password(pwd, h))
        self.assertFalse(verify_password("wrong_password", h))

    def test_jwt_token_generation_and_decoding(self):
        """Test JWT token encoding and payload verification."""
        payload = {"sub": "test_user", "role": "teacher"}
        token = create_access_token(payload)
        self.assertIsInstance(token, str)

        decoded = decode_access_token(token)
        self.assertEqual(decoded["sub"], "test_user")
        self.assertEqual(decoded["role"], "teacher")

    def test_admin_authentication_success(self):
        """Administrator user authentication with seeded credentials."""
        user = authenticate_user("admin", "admin123")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "administrator")
        self.assertEqual(user["username"], "admin")

    def test_teacher_authentication_success(self):
        """Teacher authentication with seeded credentials."""
        user = authenticate_user("teacher1", "teach123")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "teacher")

    def test_student_authentication_success(self):
        """Student authentication with generated credentials."""
        user = authenticate_user("FA22-BIT-A-001", "student123")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "student")

    def test_invalid_credentials_rejected(self):
        """Invalid passwords or usernames must return None."""
        self.assertIsNone(authenticate_user("admin", "incorrect_password"))
        self.assertIsNone(authenticate_user("nonexistent_user", "pass123"))

    def test_login_router_endpoint(self):
        """Test login endpoint returning signed JWT token and user context."""
        req = LoginRequest(username="admin", password="admin123")
        resp = login(req)
        self.assertEqual(resp.role, "administrator")
        self.assertEqual(resp.username, "admin")
        self.assertTrue(len(resp.access_token) > 20)


if __name__ == "__main__":
    unittest.main()
