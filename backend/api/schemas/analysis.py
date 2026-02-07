"""
Analysis job schemas
"""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, ConfigDict

from api.db.models import JobStatus


class AnalysisJobBase(BaseModel):
    """Base analysis job schema"""
    tool_name: str = Field(..., max_length=50)
    job_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class AnalysisJobCreate(BaseModel):
    """Schema for creating an analysis job from local path"""
    path: str = Field(..., description="Local file system path to analyze")
    job_name: Optional[str] = Field(None, max_length=200)


class AnalysisJobResponse(BaseModel):
    """Schema for analysis job response"""
    id: int
    job_name: str
    status: str
    progress: int = Field(ge=0, le=100)
    created_at: datetime
    error_message: Optional[str] = None
    message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AnalysisJobList(BaseModel):
    """Schema for paginated analysis job list"""
    total: int
    items: list[AnalysisJobResponse]
    page: int
    page_size: int


class AnalysisJobStatusUpdate(BaseModel):
    """Schema for updating job status (internal use)"""
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    error_message: Optional[str] = None
    output_file_path: Optional[str] = None


class AnalysisResultResponse(BaseModel):
    """Schema for analysis result response"""
    job_id: int
    job_name: str
    result_data: dict[str, Any]
    summary: Optional[dict[str, Any]] = None
    processing_time: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalysisHistoryResponse(BaseModel):
    """Schema for analysis history item"""
    id: int
    job_name: str
    status: str
    input_file: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
