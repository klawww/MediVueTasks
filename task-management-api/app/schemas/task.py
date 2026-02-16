from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TagBase(BaseModel):
    name: str


class TagResponse(TagBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    priority: int = Field(..., ge=1, le=5, description="Priority level (1-5, where 5 is highest)")
    due_date: date = Field(..., description="Due date in ISO format (YYYY-MM-DD)")
    tags: Optional[list[str]] = Field(default=None, description="List of tag names")

    @field_validator("due_date")
    @classmethod
    def due_date_not_in_past(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("due_date cannot be in the past")
        return v


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    priority: Optional[int] = Field(None, ge=1, le=5, description="Priority level (1-5)")
    due_date: Optional[date] = Field(None, description="Due date in ISO format (YYYY-MM-DD)")
    completed: Optional[bool] = Field(None, description="Task completion status")
    tags: Optional[list[str]] = Field(None, description="List of tag names")

    @field_validator("due_date")
    @classmethod
    def due_date_not_in_past(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v < date.today():
            raise ValueError("due_date cannot be in the past")
        return v


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    priority: int
    due_date: date
    completed: bool
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_tags(cls, task) -> "TaskResponse":
        return cls(
            id=task.id,
            title=task.title,
            description=task.description,
            priority=task.priority,
            due_date=task.due_date,
            completed=task.completed,
            tags=[tag.name for tag in task.tags],
            created_at=task.created_at,
            updated_at=task.updated_at,
        )


class PaginatedTaskResponse(BaseModel):
    total: int
    limit: int
    offset: int
    tasks: list[TaskResponse]


class ErrorDetail(BaseModel):
    error: str
    details: Optional[dict] = None
