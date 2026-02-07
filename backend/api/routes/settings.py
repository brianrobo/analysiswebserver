"""
User settings API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.core.dependencies import get_current_user
from api.db.session import get_db
from api.db.models import User, UserSettings as UserSettingsModel
from api.schemas.settings import UserSettings, UserSettingsUpdate


router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=UserSettings)
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's settings

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        User settings object

    Raises:
        HTTPException: If settings not found
    """
    settings = db.query(UserSettingsModel).filter(
        UserSettingsModel.user_id == current_user.id
    ).first()

    if not settings:
        # Create default settings if not exists
        settings = UserSettingsModel(
            user_id=current_user.id,
            theme="light",
            sidebar_collapsed=False,
            open_tabs=[],
            active_tab=None,
            tool_preferences={},
            recent_tools=[]
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings


@router.patch("", response_model=UserSettings)
async def update_user_settings(
    settings_update: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user settings (partial update)

    Args:
        settings_update: Settings update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user settings

    Raises:
        HTTPException: If settings not found
    """
    settings = db.query(UserSettingsModel).filter(
        UserSettingsModel.user_id == current_user.id
    ).first()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User settings not found"
        )

    # Update only provided fields
    update_data = settings_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    db.commit()
    db.refresh(settings)

    return settings


@router.patch("/theme", response_model=UserSettings)
async def update_theme(
    theme: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user theme preference

    Args:
        theme: Theme name ("light" or "dark")
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user settings

    Raises:
        HTTPException: If theme is invalid
    """
    if theme not in ["light", "dark"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid theme. Must be 'light' or 'dark'"
        )

    settings = db.query(UserSettingsModel).filter(
        UserSettingsModel.user_id == current_user.id
    ).first()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User settings not found"
        )

    settings.theme = theme
    db.commit()
    db.refresh(settings)

    return settings


@router.patch("/workspace", response_model=UserSettings)
async def update_workspace(
    open_tabs: list[str],
    active_tab: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update workspace state (open tabs and active tab)

    Args:
        open_tabs: List of open tab IDs
        active_tab: Currently active tab ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user settings
    """
    settings = db.query(UserSettingsModel).filter(
        UserSettingsModel.user_id == current_user.id
    ).first()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User settings not found"
        )

    settings.open_tabs = open_tabs
    if active_tab is not None:
        settings.active_tab = active_tab

    db.commit()
    db.refresh(settings)

    return settings


@router.patch("/tool-preferences", response_model=UserSettings)
async def update_tool_preferences(
    tool_id: str,
    preferences: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update preferences for a specific tool

    Args:
        tool_id: Tool identifier
        preferences: Tool-specific preferences
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user settings
    """
    settings = db.query(UserSettingsModel).filter(
        UserSettingsModel.user_id == current_user.id
    ).first()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User settings not found"
        )

    # Update tool preferences
    if settings.tool_preferences is None:
        settings.tool_preferences = {}

    settings.tool_preferences[tool_id] = preferences
    db.commit()
    db.refresh(settings)

    return settings


@router.post("/recent-tool/{tool_id}", response_model=UserSettings)
async def add_recent_tool(
    tool_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a tool to recent tools list (max 10)

    Args:
        tool_id: Tool identifier
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user settings
    """
    settings = db.query(UserSettingsModel).filter(
        UserSettingsModel.user_id == current_user.id
    ).first()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User settings not found"
        )

    # Remove tool if already in list
    if tool_id in settings.recent_tools:
        settings.recent_tools.remove(tool_id)

    # Add to beginning of list
    settings.recent_tools.insert(0, tool_id)

    # Keep only last 10
    settings.recent_tools = settings.recent_tools[:10]

    db.commit()
    db.refresh(settings)

    return settings
