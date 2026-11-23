"""
main.py — Main FastAPI application entrypoint for Student Learning Pattern Analysis
Human-centred educational analytics system for mid-semester assessment.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.config import ALLOWED_ORIGINS, DB_PATH, PROJECT_NAME, VERSION
from backend.database import init_db
from backend.routers import (
    assessment_routes,
    auth_routes,
    class_routes,
    dashboard_routes,
    import_export_routes,
    student_routes,
    teacher_routes,
)

# ── FastAPI App Instance ───────────────────────────────────────────
app = FastAPI(
    title=PROJECT_NAME,
    description="Human-Centred Educational Analytics System for Mid-Semester Academic Performance",
    version=VERSION,
)

# ── CORS Middleware ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include API Routers ────────────────────────────────────────────
app.include_router(auth_routes.router)
app.include_router(class_routes.router)
app.include_router(teacher_routes.router)
app.include_router(student_routes.router)
app.include_router(assessment_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(import_export_routes.router)

# ── Static Files (Frontend) ────────────────────────────────────────
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.on_event("startup")
def startup_event():
    """Ensure database tables and default administrators exist on startup."""
    init_db(DB_PATH)
    print(f"[{PROJECT_NAME}] Application startup complete. Database ready.")


@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirect root URL to the login page."""
    return RedirectResponse(url="/static/login.html")


@app.get("/health", tags=["Health"])
def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "project": PROJECT_NAME,
        "version": VERSION,
        "assessment_model": "Mid-Semester (30 Midterm, 3 Assignment, 3 Presentation, 4 Attendance)",
    }
