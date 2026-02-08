"""
Analysis API endpoints for PyQt/PySide project analysis
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from api.core.dependencies import get_current_user, get_db
from api.core.cache import cache
from api.core.websocket_manager import manager as ws_manager
from api.db.models import User, AnalysisJob, AnalysisResult
from api.schemas.analysis import (
    AnalysisJobCreate,
    AnalysisJobResponse,
    AnalysisResultResponse,
    AnalysisHistoryResponse,
)
from api.schemas.sharing import (
    ShareRequest,
    ShareResponse,
    SharedAnalysisResponse,
)
from analysis import AnalysisEngine
from analysis.processors.file_processor import FileProcessor
from analysis.processors.path_processor import PathProcessor
from api.services.sharing_service import sharing_service
from datetime import datetime
import json
from pathlib import Path

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


# Initialize processors
file_processor = FileProcessor()
path_processor = PathProcessor()
analysis_engine = AnalysisEngine()


async def run_analysis_background(
    job_id: int,
    project_path: str,
    project_name: str,
    db: Session,
):
    """Background task to run analysis"""
    # Update job status
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        return

    try:
        # Update status: running (10%)
        job.status = "running"
        job.progress = 10
        db.commit()
        await cache.set_progress(job_id, 10, "running", "Starting analysis...")
        await ws_manager.send_progress_update(job_id, 10, "running", "Starting analysis...")

        # Run analysis
        result = await analysis_engine.analyze_project(project_path, project_name)

        # Save result to database (90%)
        job.progress = 90
        db.commit()
        await cache.set_progress(job_id, 90, "running", "Saving results...")
        await ws_manager.send_progress_update(job_id, 90, "running", "Saving results...")

        analysis_result = AnalysisResult(
            job_id=job_id,
            result_data=result.model_dump(),  # Pydantic v2
            summary=result.analysis_summary,
            processing_time=(datetime.utcnow() - job.created_at).total_seconds(),
            records_processed=result.total_files,
        )
        db.add(analysis_result)

        # Update job: completed (100%)
        job.status = "completed"
        job.progress = 100
        db.commit()
        await cache.set_progress(job_id, 100, "completed", "Analysis completed")
        await ws_manager.send_progress_update(job_id, 100, "completed", "Analysis completed")

        # Cache the result
        result_dict = {
            "job_id": job.id,
            "job_name": job.job_name,
            "result_data": result.model_dump(),
            "summary": result.analysis_summary,
            "processing_time": analysis_result.processing_time,
            "created_at": analysis_result.created_at.isoformat() if analysis_result.created_at else None,
        }
        await cache.set_analysis_result(job_id, result_dict)

        # Send completion notification via WebSocket
        await ws_manager.send_completion(job_id, result.analysis_summary)

        # Invalidate user history cache
        await cache.invalidate_user_history(job.user_id)

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
        await cache.set_progress(job_id, job.progress, "failed", f"Error: {str(e)}")
        await ws_manager.send_error(job_id, str(e))


@router.post("/upload", response_model=AnalysisJobResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    job_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a Python file or ZIP archive for analysis

    - **file**: Python file (.py) or ZIP archive (.zip)
    - **job_name**: Optional custom job name
    """
    # Read file content
    file_content = await file.read()

    try:
        # Process upload
        upload_info = await file_processor.process_upload(
            file_content, file.filename, current_user.id
        )

        # Create analysis job
        job = AnalysisJob(
            user_id=current_user.id,
            tool_name="pyqt_analyzer",
            job_name=job_name or f"Analysis of {file.filename}",
            status="pending",
            progress=0,
            input_file=file.filename,
            parameters={"upload_id": upload_info["upload_id"]},
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Start background analysis
        extracted_path = upload_info["extracted_path"]
        project_name = Path(file.filename).stem

        background_tasks.add_task(
            run_analysis_background,
            job.id,
            extracted_path,
            project_name,
            db,
        )

        return AnalysisJobResponse(
            id=job.id,
            job_name=job.job_name,
            status=job.status,
            progress=job.progress,
            created_at=job.created_at,
            message=f"Analysis started for {upload_info['file_count']} files",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/from-path", response_model=AnalysisJobResponse)
async def analyze_from_path(
    background_tasks: BackgroundTasks,
    request: AnalysisJobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyze a local directory or Python file

    - **path**: Local file system path
    - **job_name**: Optional custom job name
    """
    try:
        # Process local path
        path_info = path_processor.process_local_path(request.path)

        # Create analysis job
        job = AnalysisJob(
            user_id=current_user.id,
            tool_name="pyqt_analyzer",
            job_name=request.job_name or f"Analysis of {Path(request.path).name}",
            status="pending",
            progress=0,
            input_file=request.path,
            parameters={"local_path": True},
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Start background analysis
        project_name = Path(request.path).name

        background_tasks.add_task(
            run_analysis_background,
            job.id,
            path_info["path"],
            project_name,
            db,
        )

        return AnalysisJobResponse(
            id=job.id,
            job_name=job.job_name,
            status=job.status,
            progress=job.progress,
            created_at=job.created_at,
            message=f"Analysis started for {path_info['file_count']} files",
        )

    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/{job_id}/status", response_model=AnalysisJobResponse)
async def get_analysis_status(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get analysis job status

    Returns current status and progress percentage
    """
    job = db.query(AnalysisJob).filter(
        AnalysisJob.id == job_id,
        AnalysisJob.user_id == current_user.id,
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")

    return AnalysisJobResponse(
        id=job.id,
        job_name=job.job_name,
        status=job.status,
        progress=job.progress,
        created_at=job.created_at,
        error_message=job.error_message,
    )


@router.get("/{job_id}/result", response_model=AnalysisResultResponse)
async def get_analysis_result(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get analysis result (with Redis caching + team sharing support)

    Returns complete analysis report with suggestions

    **Authorization**: Owner or team member with can_view permission
    """
    # Check access (owner or shared)
    has_access = sharing_service.check_access(
        db=db,
        job_id=job_id,
        user=current_user,
        require_download=False  # Only need view permission
    )

    if not has_access:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to view this analysis"
        )

    # Check cache first
    cached_result = await cache.get_analysis_result(job_id)
    if cached_result:
        return AnalysisResultResponse(**cached_result)

    # Cache miss - query database
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")

    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not completed yet (status: {job.status})",
        )

    result = db.query(AnalysisResult).filter(
        AnalysisResult.job_id == job_id
    ).first()

    if not result:
        raise HTTPException(status_code=404, detail="Analysis result not found")

    # Build response
    result_dict = {
        "job_id": job.id,
        "job_name": job.job_name,
        "result_data": result.result_data,
        "summary": result.summary,
        "processing_time": result.processing_time,
        "created_at": result.created_at,
    }

    # Cache for next time
    await cache.set_analysis_result(job_id, result_dict)

    return AnalysisResultResponse(**result_dict)


@router.get("/history", response_model=list[AnalysisHistoryResponse])
async def get_analysis_history(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get analysis history for current user (with caching for first page)

    - **limit**: Maximum number of results (default: 20)
    - **offset**: Offset for pagination (default: 0)
    """
    # Cache only first page (offset=0)
    if offset == 0:
        cached_history = await cache.get_user_history(current_user.id)
        if cached_history:
            return [AnalysisHistoryResponse(**item) for item in cached_history[:limit]]

    # Query database
    jobs = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.user_id == current_user.id)
        .order_by(AnalysisJob.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    history = []
    for job in jobs:
        history.append(
            AnalysisHistoryResponse(
                id=job.id,
                job_name=job.job_name,
                status=job.status,
                input_file=job.input_file,
                created_at=job.created_at,
            )
        )

    # Cache first page
    if offset == 0 and history:
        history_dict = [item.model_dump() for item in history]
        await cache.set_user_history(current_user.id, history_dict)

    return history


@router.delete("/{job_id}")
async def delete_analysis(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete an analysis job and its results (invalidates cache)

    - **job_id**: Analysis job ID
    """
    job = db.query(AnalysisJob).filter(
        AnalysisJob.id == job_id,
        AnalysisJob.user_id == current_user.id,
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")

    # Delete result if exists
    db.query(AnalysisResult).filter(AnalysisResult.job_id == job_id).delete()

    # Delete job
    db.delete(job)
    db.commit()

    # Invalidate caches
    await cache.invalidate_analysis_result(job_id)
    await cache.invalidate_user_history(current_user.id)

    # Cleanup uploaded files if exists
    if job.parameters and "upload_id" in job.parameters:
        upload_id = job.parameters["upload_id"]
        file_processor.cleanup_upload(current_user.id, upload_id)

    return {"message": "Analysis deleted successfully"}


@router.get("/stats")
async def get_analysis_stats(
    current_user: User = Depends(get_current_user),
):
    """
    Get analysis statistics and cache performance

    Returns cache hit rate and other metrics
    """
    stats = await cache.get_cache_stats()

    return {
        "cache_stats": stats,
        "message": "Cache statistics retrieved successfully"
    }


# ==================== Team Sharing Endpoints ====================

@router.post("/{job_id}/share", response_model=ShareResponse)
async def share_analysis_with_team(
    job_id: int,
    request: ShareRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Share analysis with a team

    **Requirements**:
    - User must be TeamLead or Admin
    - User must own the analysis
    - Team must exist

    **Permissions**:
    - `can_view`: Allow team members to view analysis results
    - `can_download`: Allow team members to download results (JSON/CSV/ZIP)
    - `expires_at`: Optional expiration timestamp (NULL = no expiration)

    **Note**: If already shared, this will update the permissions
    """
    try:
        sharing = sharing_service.share_with_team(
            db=db,
            job_id=job_id,
            team_id=request.team_id,
            user=current_user,
            can_view=request.can_view,
            can_download=request.can_download,
            expires_at=request.expires_at
        )

        return ShareResponse(
            job_id=sharing.job_id,
            team_id=sharing.team_id,
            shared_by_user_id=sharing.shared_by_user_id,
            can_view=sharing.can_view,
            can_download=sharing.can_download,
            created_at=sharing.created_at,
            expires_at=sharing.expires_at
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sharing failed: {str(e)}")


@router.delete("/{job_id}/share/{team_id}")
async def unshare_analysis_with_team(
    job_id: int,
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Remove team sharing for an analysis

    **Authorization**:
    - Analysis owner
    - Admin
    - Team's Team Lead
    """
    try:
        success = sharing_service.unshare_with_team(
            db=db,
            job_id=job_id,
            team_id=team_id,
            user=current_user
        )

        if success:
            return {"message": "Analysis unshared successfully"}
        else:
            raise HTTPException(status_code=404, detail="Sharing not found")

    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unsharing failed: {str(e)}")


@router.get("/shared-with-me", response_model=list[SharedAnalysisResponse])
async def get_shared_analyses(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get analyses shared with user's team

    Returns analyses that:
    - Are shared with user's team
    - User doesn't own (no duplicates with /history)
    - Haven't expired yet

    **Pagination**: Use limit/offset for pagination
    """
    try:
        shared = sharing_service.get_shared_analyses(
            db=db,
            user=current_user,
            limit=limit,
            offset=offset
        )

        return [SharedAnalysisResponse(**item) for item in shared]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve shared analyses: {str(e)}"
        )
