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


class AnalysisJobCreate(AnalysisJobBase):
    """Schema for creating an analysis job"""
    input_file_name: str


class AnalysisJobResponse(AnalysisJobBase):
    """Schema for analysis job response"""
    id: int
    user_id: int
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    error_message: Optional[str] = None
    input_file_name: str
    output_file_path: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

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
    id: int
    job_id: int
    result_data: dict[str, Any]
    summary: Optional[str] = None
    processing_time_seconds: Optional[int] = None
    records_processed: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
