"""
Database models for the Analysis Tool application
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .session import Base


class UserRole(str, PyEnum):
    """User role enumeration"""
    ADMIN = "admin"
    TEAM_LEAD = "team_lead"
    MEMBER = "member"
    VIEWER = "viewer"


class JobStatus(str, PyEnum):
    """Analysis job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Team(Base):
    """Team model for organizing users"""
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="team")


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.MEMBER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Team membership
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    team = relationship("Team", back_populates="users")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    analysis_jobs = relationship("AnalysisJob", back_populates="user", cascade="all, delete-orphan")


class UserSettings(Base):
    """User-specific application settings"""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # UI Settings
    theme = Column(String(10), default="light", nullable=False)  # "light" | "dark"
    sidebar_collapsed = Column(Boolean, default=False, nullable=False)

    # Workspace Settings
    open_tabs = Column(JSON, default=list, nullable=False)  # List of open tab IDs
    active_tab = Column(String(50), nullable=True)  # Currently active tab ID

    # Tool Preferences
    tool_preferences = Column(JSON, default=dict, nullable=False)  # Tool-specific settings
    recent_tools = Column(JSON, default=list, nullable=False)  # Recently used tools (max 10)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="settings")


class AnalysisJob(Base):
    """Analysis job tracking"""
    __tablename__ = "analysis_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Job Information
    tool_name = Column(String(50), nullable=False, index=True)  # Which analysis tool was used
    job_name = Column(String(200), nullable=True)  # User-provided job name
    description = Column(Text, nullable=True)

    # Job Status
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    progress = Column(Integer, default=0, nullable=False)  # 0-100
    error_message = Column(Text, nullable=True)

    # File Information
    input_file_path = Column(String(500), nullable=False)  # Path to uploaded file
    input_file_name = Column(String(255), nullable=False)  # Original filename
    output_file_path = Column(String(500), nullable=True)  # Path to result file

    # Job Parameters
    parameters = Column(JSON, default=dict, nullable=False)  # Analysis parameters/options

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="analysis_jobs")
    result = relationship("AnalysisResult", back_populates="job", uselist=False, cascade="all, delete-orphan")


class AnalysisResult(Base):
    """Analysis job results"""
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("analysis_jobs.id"), unique=True, nullable=False)

    # Result Data
    result_data = Column(JSON, nullable=False)  # Structured result data
    summary = Column(Text, nullable=True)  # Human-readable summary

    # Statistics
    processing_time_seconds = Column(Integer, nullable=True)  # Time taken to process
    records_processed = Column(Integer, nullable=True)  # Number of records processed

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    job = relationship("AnalysisJob", back_populates="result")
