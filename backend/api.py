"""
api.py — Backwards-compatibility adapter pointing to backend.main
Ensures existing FYP deployment commands (e.g. uvicorn api:app or uvicorn backend.api:app) continue to work seamlessly.
"""

from backend.main import app

__all__ = ["app"]
