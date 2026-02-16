from datetime import date, datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, ForeignKey, Table, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)

# Association table for many-to-many relationship between tasks and tags
task_tags = Table(
    "task_tags",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)

    tasks = relationship("Task", secondary=task_tags, back_populates="tags")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, nullable=False, default=3)
    due_date = Column(Date, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)  # Soft delete flag
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    tags = relationship("Tag", secondary=task_tags, back_populates="tasks", lazy="joined")

    __table_args__ = (
        Index("ix_tasks_priority", "priority"),
        Index("ix_tasks_completed", "completed"),
        Index("ix_tasks_is_deleted", "is_deleted"),
        Index("ix_tasks_due_date", "due_date"),
        # Composite index for common query patterns (list tasks filters is_deleted first)
        Index("ix_tasks_deleted_completed", "is_deleted", "completed"),
        Index("ix_tasks_deleted_priority", "is_deleted", "priority"),
    )
