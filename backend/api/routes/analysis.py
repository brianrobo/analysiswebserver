"""
Analysis API endpoints for PyQt/PySide project analysis
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from api.core.dependencies import get_current_user, get_db
from api.db.models import User, AnalysisJob, AnalysisResult
from api.schemas.analysis import (
    AnalysisJobCreate,
    AnalysisJobResponse,
    AnalysisResultResponse,
    AnalysisHistoryResponse,
)
from analysis import AnalysisEngine
from analysis.processors.file_processor import FileProcessor
from analysis.processors.path_processor import PathProcessor
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
        job.status = "running"
        job.progress = 10
        db.commit()

        # Run analysis
        result = await analysis_engine.analyze_project(project_path, project_name)

        # Save result to database
        job.progress = 90
        db.commit()

        analysis_result = AnalysisResult(
            job_id=job_id,
            result_data=result.model_dump(),  # Pydantic v2
            summary=result.analysis_summary,
            processing_time=(datetime.utcnow() - job.created_at).total_seconds(),
            records_processed=result.total_files,
        )
        db.add(analysis_result)

        # Update job
        job.status = "completed"
        job.progress = 100
        db.commit()

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        db.commit()


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
    Get analysis result

    Returns complete analysis report with suggestions
    """
    job = db.query(AnalysisJob).filter(
        AnalysisJob.id == job_id,
        AnalysisJob.user_id == current_user.id,
    ).first()

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

    return AnalysisResultResponse(
        job_id=job.id,
        job_name=job.job_name,
        result_data=result.result_data,
        summary=result.summary,
        processing_time=result.processing_time,
        created_at=result.created_at,
    )


@router.get("/history", response_model=list[AnalysisHistoryResponse])
async def get_analysis_history(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get analysis history for current user

    - **limit**: Maximum number of results (default: 20)
    - **offset**: Offset for pagination (default: 0)
    """
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

    return history


@router.delete("/{job_id}")
async def delete_analysis(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete an analysis job and its results

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

    # Cleanup uploaded files if exists
    if job.parameters and "upload_id" in job.parameters:
        upload_id = job.parameters["upload_id"]
        file_processor.cleanup_upload(current_user.id, upload_id)

    return {"message": "Analysis deleted successfully"}
