"""
database.py — SQLite relational database layer for Student Learning Pattern Analysis
Normalized 6-table schema supporting RBAC, class-level scoping, and mid-semester assessment.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

from backend.config import DB_PATH
from backend.utils.security import hash_password
from backend.utils.validators import compute_totals, validate_assessment_record


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Return an SQLite connection with foreign keys enabled and Row factory."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_session(db_path: Path = DB_PATH) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite transactions."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Path = DB_PATH) -> None:
    """Create all relational tables, constraints, indexes, and seed default roles."""
    with db_session(db_path) as conn:
        cur = conn.cursor()

        # ── 1. Users ───────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    UNIQUE NOT NULL,
                password_hash TEXT    NOT NULL,
                role          TEXT    NOT NULL CHECK(role IN ('administrator', 'teacher', 'student')),
                status        TEXT    DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'suspended')),
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # ── 2. Teachers ────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS teachers (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER UNIQUE NOT NULL,
                teacher_name  TEXT    NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # ── 3. Classes ─────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                class_name        TEXT    NOT NULL,
                section           TEXT    NOT NULL,
                academic_session  TEXT    NOT NULL,
                UNIQUE(class_name, section, academic_session)
            );
        """)

        # ── 4. Students ────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id    TEXT    UNIQUE NOT NULL,
                student_name  TEXT    NOT NULL,
                class_id      INTEGER NOT NULL,
                user_id       INTEGER UNIQUE,
                FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
        """)

        # ── 5. Teacher Classes (Teacher-Class Assignment) ──────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS teacher_classes (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id    INTEGER NOT NULL,
                class_id      INTEGER NOT NULL,
                UNIQUE(teacher_id, class_id),
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
                FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
            );
        """)

        # ── 6. Assessment Records ──────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS assessment_records (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id          INTEGER UNIQUE NOT NULL,
                midterm_marks       REAL CHECK(midterm_marks IS NULL OR (midterm_marks >= 0 AND midterm_marks <= 30)),
                assignment_marks    REAL CHECK(assignment_marks IS NULL OR (assignment_marks >= 0 AND assignment_marks <= 3)),
                presentation_marks  REAL CHECK(presentation_marks IS NULL OR (presentation_marks >= 0 AND presentation_marks <= 3)),
                attendance_marks    REAL CHECK(attendance_marks IS NULL OR (attendance_marks >= 0 AND attendance_marks <= 4)),
                updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by          TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            );
        """)

        # ── Indexes ────────────────────────────────────────────────
        cur.execute("CREATE INDEX IF NOT EXISTS idx_students_class ON students(class_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_assessment_student ON assessment_records(student_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_teacher_classes_teacher ON teacher_classes(teacher_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_teacher_classes_class ON teacher_classes(class_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")

        # ── Seed Default Administrator and Teachers ─────────────────
        # Admin account
        cur.execute("SELECT id FROM users WHERE username = 'admin';")
        if not cur.fetchone():
            pwd_hash = hash_password("admin123")
            cur.execute(
                "INSERT INTO users (username, password_hash, role, status) VALUES (?, ?, 'administrator', 'active');",
                ("admin", pwd_hash)
            )

        # Classes
        default_classes = [
            ("BSIT", "Section A", "2025-2026"),
            ("BSIT", "Section B", "2025-2026"),
            ("BSCS", "Section A", "2025-2026"),
        ]
        class_ids = {}
        for cname, sec, sess in default_classes:
            cur.execute("""
                INSERT OR IGNORE INTO classes (class_name, section, academic_session)
                VALUES (?, ?, ?);
            """, (cname, sec, sess))
            cur.execute("""
                SELECT id FROM classes WHERE class_name = ? AND section = ? AND academic_session = ?;
            """, (cname, sec, sess))
            class_ids[(cname, sec)] = cur.fetchone()["id"]

        # Default Teachers
        teachers_to_seed = [
            ("teacher1", "teach123", "Dr. Mustafa Hameed", [("BSIT", "Section A"), ("BSCS", "Section A")]),
            ("teacher2", "teach456", "Ms. Samra Riaz", [("BSIT", "Section B")]),
        ]

        for username, pwd, tname, assigned_cls in teachers_to_seed:
            cur.execute("SELECT id FROM users WHERE username = ?;", (username,))
            user_row = cur.fetchone()
            if not user_row:
                cur.execute(
                    "INSERT INTO users (username, password_hash, role, status) VALUES (?, ?, 'teacher', 'active');",
                    (username, hash_password(pwd))
                )
                user_id = cur.lastrowid
            else:
                user_id = user_row["id"]

            cur.execute("SELECT id FROM teachers WHERE user_id = ?;", (user_id,))
            t_row = cur.fetchone()
            if not t_row:
                cur.execute(
                    "INSERT INTO teachers (user_id, teacher_name) VALUES (?, ?);",
                    (user_id, tname)
                )
                teacher_id = cur.lastrowid
            else:
                teacher_id = t_row["id"]

            # Assign to classes
            for cls_key in assigned_cls:
                cls_id = class_ids.get(cls_key)
                if cls_id:
                    cur.execute("""
                        INSERT OR IGNORE INTO teacher_classes (teacher_id, class_id)
                        VALUES (?, ?);
                    """, (teacher_id, cls_id))


# ── Query Helper Functions ──────────────────────────────────────────

def get_user_by_username(username: str, db_path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve user record by username."""
    with db_session(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?;", (username,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int, db_path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve user record by user ID."""
    with db_session(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, username, role, status, created_at FROM users WHERE id = ?;", (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_teacher_by_user_id(user_id: int, db_path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
    """Get teacher details from user_id."""
    with db_session(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM teachers WHERE user_id = ?;", (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_teacher_assigned_class_ids(teacher_id: int, db_path: Path = DB_PATH) -> List[int]:
    """Get list of class_ids assigned to a teacher."""
    with db_session(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT class_id FROM teacher_classes WHERE teacher_id = ?;", (teacher_id,))
        return [row["class_id"] for row in cur.fetchall()]


def get_student_by_user_id(user_id: int, db_path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
    """Get student record associated with a user_id."""
    with db_session(db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT s.*, c.class_name, c.section, c.academic_session
            FROM students s
            JOIN classes c ON s.class_id = c.id
            WHERE s.user_id = ?;
        """, (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_student_by_student_id(student_id: str, db_path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
    """Get student profile and assessment data by university student_id."""
    with db_session(db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT s.id as id, s.student_id, s.student_name, s.class_id, s.user_id,
                   c.class_name, c.section, c.academic_session,
                   a.midterm_marks, a.assignment_marks, a.presentation_marks, a.attendance_marks,
                   a.updated_at, a.updated_by
            FROM students s
            JOIN classes c ON s.class_id = c.id
            LEFT JOIN assessment_records a ON s.id = a.student_id
            WHERE s.student_id = ?;
        """, (student_id,))
        row = cur.fetchone()
        if not row:
            return None
        res = dict(row)
        totals = compute_totals(
            res["midterm_marks"],
            res["assignment_marks"],
            res["presentation_marks"],
            res["attendance_marks"],
        )
        res.update(totals)
        return res
