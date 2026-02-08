"""
Team Sharing Service for Analysis Results
Manages permissions and access control for shared analyses
"""
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from api.db.models import (
    User,
    Team,
    AnalysisJob,
    AnalysisSharing,
    UserRole
)

logger = logging.getLogger(__name__)


class SharingService:
    """
    Service for managing analysis result sharing with teams

    Permissions:
    - Share: TeamLead+ only (for their own analyses)
    - Unshare: Owner, Admin, or Team's TeamLead
    - View Shared: All team members (if shared with their team)
    """

    def can_share(self, user: User) -> bool:
        """
        Check if user can share analyses

        Args:
            user: User object

        Returns:
            True if user is TeamLead or Admin
        """
        return user.role in [UserRole.TEAM_LEAD, UserRole.ADMIN]

    def share_with_team(
        self,
        db: Session,
        job_id: int,
        team_id: int,
        user: User,
        can_view: bool = True,
        can_download: bool = True,
        expires_at: Optional[datetime] = None
    ) -> AnalysisSharing:
        """
        Share analysis with a team

        Args:
            db: Database session
            job_id: Analysis job ID
            team_id: Team ID to share with
            user: User who is sharing (must be owner)
            can_view: Permission flag for viewing
            can_download: Permission flag for downloading
            expires_at: Optional expiration timestamp

        Returns:
            AnalysisSharing record

        Raises:
            ValueError: If user cannot share or doesn't own the analysis
            Exception: If team or job not found
        """
        # Check if user can share
        if not self.can_share(user):
            raise ValueError("Only Team Leads and Admins can share analyses")

        # Verify job ownership
        job = db.query(AnalysisJob).filter(
            AnalysisJob.id == job_id,
            AnalysisJob.user_id == user.id
        ).first()

        if not job:
            raise ValueError("Analysis job not found or you don't have permission to share it")

        # Verify team exists
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise ValueError(f"Team {team_id} not found")

        # Check if already shared (update permissions if so)
        existing = db.query(AnalysisSharing).filter(
            AnalysisSharing.job_id == job_id,
            AnalysisSharing.team_id == team_id
        ).first()

        if existing:
            # Update existing sharing
            existing.can_view = can_view
            existing.can_download = can_download
            existing.expires_at = expires_at
            existing.shared_by_user_id = user.id  # Update sharer
            db.commit()
            db.refresh(existing)

            logger.info(f"Updated sharing: job_id={job_id}, team_id={team_id}, user_id={user.id}")
            return existing

        # Create new sharing
        sharing = AnalysisSharing(
            job_id=job_id,
            team_id=team_id,
            shared_by_user_id=user.id,
            can_view=can_view,
            can_download=can_download,
            expires_at=expires_at
        )

        db.add(sharing)
        db.commit()
        db.refresh(sharing)

        logger.info(f"Created sharing: job_id={job_id}, team_id={team_id}, user_id={user.id}")
        return sharing

    def unshare_with_team(
        self,
        db: Session,
        job_id: int,
        team_id: int,
        user: User
    ) -> bool:
        """
        Remove team sharing for an analysis

        Args:
            db: Database session
            job_id: Analysis job ID
            team_id: Team ID
            user: User requesting unshare

        Returns:
            True if successfully unshared

        Raises:
            ValueError: If user doesn't have permission
        """
        # Get the job
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            raise ValueError("Analysis job not found")

        # Check permission: owner, admin, or team's team lead
        can_unshare = (
            job.user_id == user.id or  # Owner
            user.role == UserRole.ADMIN or  # Admin
            (user.role == UserRole.TEAM_LEAD and user.team_id == team_id)  # Team's leader
        )

        if not can_unshare:
            raise ValueError("You don't have permission to unshare this analysis")

        # Delete sharing record
        deleted = db.query(AnalysisSharing).filter(
            AnalysisSharing.job_id == job_id,
            AnalysisSharing.team_id == team_id
        ).delete()

        db.commit()

        if deleted > 0:
            logger.info(f"Removed sharing: job_id={job_id}, team_id={team_id}, user_id={user.id}")
            return True

        return False

    def get_shared_analyses(
        self,
        db: Session,
        user: User,
        limit: int = 20,
        offset: int = 0
    ) -> List[dict]:
        """
        Get analyses shared with user's team

        Args:
            db: Database session
            user: User object
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of shared analysis summaries
        """
        if not user.team_id:
            return []  # User not in a team

        # Query shared analyses
        now = datetime.utcnow()

        sharing_records = (
            db.query(AnalysisSharing, AnalysisJob, User)
            .join(AnalysisJob, AnalysisSharing.job_id == AnalysisJob.id)
            .join(User, AnalysisJob.user_id == User.id)
            .filter(
                AnalysisSharing.team_id == user.team_id,
                AnalysisJob.user_id != user.id,  # Exclude own analyses
                # Check expiration
                (AnalysisSharing.expires_at.is_(None)) | (AnalysisSharing.expires_at > now)
            )
            .order_by(AnalysisSharing.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        results = []
        for sharing, job, owner in sharing_records:
            results.append({
                "job_id": job.id,
                "job_name": job.job_name,
                "status": job.status.value,
                "owner_id": owner.id,
                "owner_name": owner.full_name or owner.email,
                "share": {
                    "can_view": sharing.can_view,
                    "can_download": sharing.can_download,
                    "shared_by_id": sharing.shared_by_user_id,
                    "shared_at": sharing.created_at.isoformat(),
                    "expires_at": sharing.expires_at.isoformat() if sharing.expires_at else None
                },
                "created_at": job.created_at.isoformat()
            })

        return results

    def check_access(
        self,
        db: Session,
        job_id: int,
        user: User,
        require_download: bool = False
    ) -> bool:
        """
        Check if user has access to an analysis (owner or shared)

        Args:
            db: Database session
            job_id: Analysis job ID
            user: User object
            require_download: If True, check for can_download permission

        Returns:
            True if user has access
        """
        # Check ownership
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            return False

        # Owner always has access
        if job.user_id == user.id:
            return True

        # Check team sharing
        if not user.team_id:
            return False

        now = datetime.utcnow()
        sharing = db.query(AnalysisSharing).filter(
            AnalysisSharing.job_id == job_id,
            AnalysisSharing.team_id == user.team_id,
            # Check expiration
            (AnalysisSharing.expires_at.is_(None)) | (AnalysisSharing.expires_at > now)
        ).first()

        if not sharing:
            return False

        # Check specific permission
        if require_download:
            return sharing.can_download

        return sharing.can_view


# Global sharing service instance
sharing_service = SharingService()
