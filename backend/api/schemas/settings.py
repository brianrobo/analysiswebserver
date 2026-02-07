"""
User settings schemas
"""
from typing import Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class UserSettingsBase(BaseModel):
    """Base user settings schema"""
    theme: str = Field("light", pattern="^(light|dark)$")
    sidebar_collapsed: bool = False
    open_tabs: list[str] = Field(default_factory=list)
    active_tab: Optional[str] = None
    tool_preferences: dict[str, Any] = Field(default_factory=dict)
    recent_tools: list[str] = Field(default_factory=list, max_length=10)


class UserSettings(UserSettingsBase):
    """Schema for user settings response"""
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class UserSettingsUpdate(BaseModel):
    """Schema for updating user settings (partial update)"""
    theme: Optional[str] = Field(None, pattern="^(light|dark)$")
    sidebar_collapsed: Optional[bool] = None
    open_tabs: Optional[list[str]] = None
    active_tab: Optional[str] = None
    tool_preferences: Optional[dict[str, Any]] = None
    recent_tools: Optional[list[str]] = Field(None, max_length=10)
