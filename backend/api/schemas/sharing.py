"""
Pydantic schemas for team sharing
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ShareRequest(BaseModel):
    """Request to share analysis with a team"""
    team_id: int = Field(..., description="Team ID to share with")
    can_view: bool = Field(True, description="Permission to view analysis")
    can_download: bool = Field(True, description="Permission to download results")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration timestamp (ISO format)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "team_id": 2,
                "can_view": True,
                "can_download": True,
                "expires_at": "2026-03-01T00:00:00Z"
            }
        }
    }


class ShareResponse(BaseModel):
    """Response after sharing analysis"""
    job_id: int
    team_id: int
    shared_by_user_id: int
    can_view: bool
    can_download: bool
    created_at: datetime
    expires_at: Optional[datetime]
    message: str = "Analysis shared successfully"

    model_config = {
        "from_attributes": True
    }


class SharedAnalysisResponse(BaseModel):
    """Shared analysis item in list"""
    job_id: int
    job_name: Optional[str]
    status: str
    owner_id: int
    owner_name: str
    share: dict  # Share details (can_view, can_download, shared_by_id, etc.)
    created_at: str  # ISO format

    model_config = {
        "json_schema_extra": {
            "example": {
                "job_id": 10,
                "job_name": "MyProject Analysis",
                "status": "completed",
                "owner_id": 1,
                "owner_name": "John Doe",
                "share": {
                    "can_view": True,
                    "can_download": True,
                    "shared_by_id": 1,
                    "shared_at": "2026-02-08T10:00:00Z",
                    "expires_at": None
                },
                "created_at": "2026-02-08T09:00:00Z"
            }
        }
    }
