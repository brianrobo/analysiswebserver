"""
File download API endpoints for analysis results
Supports JSON, CSV, and ZIP formats
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from typing import Literal
from io import BytesIO
import logging

from api.core.dependencies import get_current_user, get_db
from api.core.cache import cache
from api.db.models import User, AnalysisJob, AnalysisResult
from api.services.export_service import export_service
from api.services.sharing_service import sharing_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analysis", tags=["download"])


@router.get("/{job_id}/download")
async def download_analysis_result(
    job_id: int,
    format: Literal["json", "csv", "zip"] = Query("json", description="Export format"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Download analysis result in various formats

    **Formats**:
    - `json`: Complete analysis result (pretty-printed)
    - `csv`: Summary table (File Path, LOC, UI %, Pure Functions, etc.)
    - `zip`: Extracted pure functions with README

    **Authentication**: Required (JWT token)
    **Authorization**: Owner only (or shared with can_download permission in Phase 3.5)

    **Examples**:
    ```
    GET /api/v1/analysis/123/download?format=json
    GET /api/v1/analysis/123/download?format=csv
    GET /api/v1/analysis/123/download?format=zip
    ```
    """
    # Verify job ownership or shared access
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")

    # Check access: owner or shared with can_download permission
    has_access = sharing_service.check_access(
        db=db,
        job_id=job_id,
        user=current_user,
        require_download=True
    )

    if not has_access:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to download this analysis"
        )

    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not completed yet (status: {job.status})"
        )

    # Get result from cache or database
    result_dict = await cache.get_analysis_result(job_id)

    if not result_dict:
        # Cache miss - query database
        result = db.query(AnalysisResult).filter(
            AnalysisResult.job_id == job_id
        ).first()

        if not result:
            raise HTTPException(status_code=404, detail="Analysis result not found")

        result_dict = {
            "job_id": job.id,
            "job_name": job.job_name,
            "result_data": result.result_data,
            "summary": result.summary,
            "processing_time": result.processing_time,
            "created_at": result.created_at.isoformat() if result.created_at else None,
        }

        # Cache for next time
        await cache.set_analysis_result(job_id, result_dict)

    # Export in requested format
    try:
        if format == "json":
            return _export_json(result_dict, job.job_name, job_id)

        elif format == "csv":
            return _export_csv(result_dict, job.job_name, job_id)

        elif format == "zip":
            return _export_zip(result_dict, job.job_name, job_id)

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    except Exception as e:
        logger.error(f"Failed to export analysis result: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Export failed: {str(e)}"
        )


def _export_json(result_dict: dict, job_name: str, job_id: int) -> Response:
    """Export as JSON response"""
    json_content = export_service.export_json(result_dict)

    return Response(
        content=json_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="analysis_{job_id}_{_sanitize_filename(job_name)}.json"',
            "Content-Type": "application/json; charset=utf-8"
        }
    )


def _export_csv(result_dict: dict, job_name: str, job_id: int) -> Response:
    """Export as CSV response"""
    csv_content = export_service.export_csv(result_dict)

    return Response(
        content=csv_content.encode('utf-8'),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="analysis_{job_id}_{_sanitize_filename(job_name)}.csv"',
            "Content-Type": "text/csv; charset=utf-8"
        }
    )


def _export_zip(result_dict: dict, job_name: str, job_id: int) -> StreamingResponse:
    """Export as ZIP response"""
    project_name = _sanitize_filename(job_name) or f"analysis_{job_id}"
    zip_bytes = export_service.export_pure_functions_zip(result_dict, project_name)

    return StreamingResponse(
        BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{project_name}_pure_functions.zip"',
        }
    )


def _sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe download

    Removes special characters and limits length
    """
    # Remove special characters
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    sanitized = "".join(c if c in safe_chars else "_" for c in filename)

    # Limit length
    if len(sanitized) > 50:
        sanitized = sanitized[:50]

    return sanitized or "analysis"
