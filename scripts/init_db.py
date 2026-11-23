"""
init_db.py — Database initialization script
Creates the SQLite relational schema and seeds default administrative & teacher accounts.
"""

import sys
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.database import init_db
from backend.config import DB_PATH

def main():
    print(f"[Init DB] Initializing database at: {DB_PATH}")
    init_db(DB_PATH)
    print("[Init DB] Database schema successfully created and default users seeded.")

if __name__ == "__main__":
    main()
