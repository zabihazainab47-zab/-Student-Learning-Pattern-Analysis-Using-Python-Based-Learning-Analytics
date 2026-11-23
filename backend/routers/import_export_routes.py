"""
import_export_routes.py — CSV import and export endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response

from backend.auth import get_current_user
from backend.permissions import require_roles
from backend.services.csv_service import export_students_csv, import_students_csv

router = APIRouter(prefix="/api/data", tags=["Import / Export"])


@router.post("/import/csv", dependencies=[Depends(require_roles("administrator", "teacher"))])
async def upload_csv_data(
    file: UploadFile = File(...),
    overwrite: bool = Query(False, description="Whether to update existing student records"),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload and import student assessment records via CSV.
    Teachers can only import records for their assigned classes.
    Administrators can import across all classes.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Please upload a standard CSV (.csv) file.",
        )

    content_bytes = await file.read()
    try:
        csv_text = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        csv_text = content_bytes.decode("latin-1")

    result = import_students_csv(
        csv_content=csv_text,
        user=current_user,
        overwrite=overwrite,
    )
    return result


@router.get("/export/csv")
def export_csv_data(
    class_id: Optional[int] = Query(None, description="Optional class ID filter"),
    current_user: dict = Depends(get_current_user),
):
    """
    Export student assessment records to CSV.
    Exports only records permitted for the authenticated user's role and class assignments.
    Authentication secrets and sensitive tokens are strictly excluded.
    """
    csv_string = export_students_csv(current_user, class_id=class_id)
    filename = f"student_learning_assessments_{class_id or 'all'}.csv"

    return Response(
        content=csv_string,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )
