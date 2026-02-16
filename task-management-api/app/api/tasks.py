from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.task import Task, Tag
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    PaginatedTaskResponse,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_or_create_tags(db: Session, tag_names: list[str]) -> list[Tag]:
    """Get existing tags or create new ones."""
    tags = []
    for name in tag_names:
        name = name.strip().lower()
        if not name:
            continue
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()
        tags.append(tag)
    return tags


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task_data: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    task = Task(
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        due_date=task_data.due_date,
    )

    if task_data.tags:
        task.tags = get_or_create_tags(db, task_data.tags)

    db.add(task)
    db.commit()
    db.refresh(task)

    return TaskResponse.from_orm_with_tags(task)


@router.get("", response_model=PaginatedTaskResponse)
def list_tasks(
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    priority: Optional[int] = Query(None, ge=1, le=5, description="Filter by priority level"),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags"),
    limit: int = Query(10, ge=1, le=100, description="Number of tasks to return"),
    offset: int = Query(0, ge=0, description="Number of tasks to skip"),
    db: Session = Depends(get_db),
):
    """Retrieve tasks with filtering and pagination."""
    query = db.query(Task).filter(Task.is_deleted == False)

    # Apply filters
    if completed is not None:
        query = query.filter(Task.completed == completed)

    if priority is not None:
        query = query.filter(Task.priority == priority)

    if tags:
        tag_names = [t.strip().lower() for t in tags.split(",") if t.strip()]
        if tag_names:
            # Filter tasks that have ANY of the specified tags
            # Using JOIN for better performance on large datasets
            query = query.join(Task.tags).filter(Tag.name.in_(tag_names)).distinct()

    # Get total count before pagination
    total = query.count()

    # Apply pagination
    tasks = query.order_by(Task.created_at.desc()).offset(offset).limit(limit).all()

    return PaginatedTaskResponse(
        total=total,
        limit=limit,
        offset=offset,
        tasks=[TaskResponse.from_orm_with_tags(task) for task in tasks],
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific task by ID."""
    task = db.query(Task).filter(Task.id == task_id, Task.is_deleted == False).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Not Found", "details": {"task_id": f"Task with id {task_id} not found"}},
        )
    return TaskResponse.from_orm_with_tags(task)


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_data: TaskUpdate, db: Session = Depends(get_db)):
    """Partially update a task."""
    task = db.query(Task).filter(Task.id == task_id, Task.is_deleted == False).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Not Found", "details": {"task_id": f"Task with id {task_id} not found"}},
        )

    # Only update fields that are provided
    update_data = task_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "tags":
            if value is not None:
                task.tags = get_or_create_tags(db, value)
        else:
            setattr(task, field, value)

    db.commit()
    db.refresh(task)

    return TaskResponse.from_orm_with_tags(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Soft delete a task."""
    task = db.query(Task).filter(Task.id == task_id, Task.is_deleted == False).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Not Found", "details": {"task_id": f"Task with id {task_id} not found"}},
        )

    # Soft delete - just flag as deleted
    task.is_deleted = True
    db.commit()

    return None
