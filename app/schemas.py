"""Pydantic request / response schemas."""

import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TodoStatus(str, Enum):
    """Allowed values for Todo.status."""

    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class Priority(str, Enum):
    """Allowed values for Todo.priority."""

    low = "low"
    medium = "medium"
    high = "high"


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------


class UserCreate(BaseModel):
    """Request body for creating a user."""

    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    email: EmailStr = Field(..., description="Unique email address")


class UserResponse(BaseModel):
    """Response body for a user."""

    id: int = Field(..., description="User ID")
    name: str = Field(..., description="Display name")
    email: str = Field(..., description="Email address")
    created_at: datetime.datetime = Field(..., description="Creation timestamp (UTC)")

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Team
# ---------------------------------------------------------------------------


class TeamCreate(BaseModel):
    """Request body for creating a team."""

    name: str = Field(..., min_length=1, max_length=100, description="Team name")


class TeamResponse(BaseModel):
    """Response body for a team."""

    id: int = Field(..., description="Team ID")
    name: str = Field(..., description="Team name")
    created_at: datetime.datetime = Field(..., description="Creation timestamp (UTC)")

    model_config = {"from_attributes": True}


class MemberAdd(BaseModel):
    """Request body for adding a member to a team."""

    user_id: int = Field(..., description="ID of the user to add")


class MemberResponse(BaseModel):
    """Response body for a team member entry."""

    team_id: int = Field(..., description="Team ID")
    user_id: int = Field(..., description="User ID")
    joined_at: datetime.datetime = Field(..., description="When the user joined the team")

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Tag
# ---------------------------------------------------------------------------


class TagCreate(BaseModel):
    """Request body for creating a tag."""

    name: str = Field(..., min_length=1, max_length=50, description="Tag name (unique per team)")


class TagResponse(BaseModel):
    """Response body for a tag."""

    id: int = Field(..., description="Tag ID")
    name: str = Field(..., description="Tag name")
    team_id: int = Field(..., description="Owning team ID")

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Todo
# ---------------------------------------------------------------------------


class TodoCreate(BaseModel):
    """Request body for creating a todo."""

    title: str = Field(..., min_length=1, max_length=255, description="Todo title")
    description: str | None = Field(None, description="Optional detailed description")
    status: TodoStatus = Field(TodoStatus.todo, description="Current status")
    priority: Priority = Field(Priority.medium, description="Priority level")
    due_date: datetime.date | None = Field(None, description="Optional due date")
    assignee_id: int | None = Field(None, description="ID of the assigned team member")
    created_by: int = Field(..., description="ID of the user creating this todo")


class TodoUpdate(BaseModel):
    """Request body for partially updating a todo (all fields optional)."""

    title: str | None = Field(None, min_length=1, max_length=255, description="Todo title")
    description: str | None = Field(None, description="Detailed description")
    status: TodoStatus | None = Field(None, description="Current status")
    priority: Priority | None = Field(None, description="Priority level")
    due_date: datetime.date | None = Field(None, description="Due date")
    assignee_id: int | None = Field(None, description="ID of the assigned team member")


class TodoResponse(BaseModel):
    """Response body for a todo."""

    id: int = Field(..., description="Todo ID")
    title: str = Field(..., description="Todo title")
    description: str | None = Field(None, description="Detailed description")
    status: TodoStatus = Field(..., description="Current status")
    priority: Priority = Field(..., description="Priority level")
    due_date: datetime.date | None = Field(None, description="Due date")
    team_id: int = Field(..., description="Owning team ID")
    assignee_id: int | None = Field(None, description="Assigned user ID")
    created_by: int = Field(..., description="Creator user ID")
    created_at: datetime.datetime = Field(..., description="Creation timestamp (UTC)")
    updated_at: datetime.datetime = Field(..., description="Last update timestamp (UTC)")
    tags: list[TagResponse] = Field(default_factory=list, description="Attached tags")

    model_config = {"from_attributes": True}
