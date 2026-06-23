from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import schemas, crud, auth, models

router = APIRouter(tags=["tasks"])

@router.post("/api/projects/{project_id}/tasks", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
def create_project_task(
    project_id: int,
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_project = crud.get_project(db, project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if current_user.role not in ["admin", "manager"] and db_project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add tasks to this project"
        )
        
    return crud.create_task(db=db, task=task, project_id=project_id, creator_id=current_user.id)

@router.get("/api/projects/{project_id}/tasks", response_model=List[schemas.TaskResponse])
def read_project_tasks(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_project = crud.get_project(db, project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return crud.get_tasks(db=db, project_id=project_id, skip=skip, limit=limit)

@router.get("/api/tasks/{task_id}", response_model=schemas.TaskResponse)
def read_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_task = crud.get_task(db=db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@router.put("/api/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    task_id: int,
    task: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_task = crud.get_task(db=db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
        
    db_project = crud.get_project(db, db_task.project_id)
    is_authorized = (
        current_user.role in ["admin", "manager"] or
        db_task.creator_id == current_user.id or
        db_task.assignee_id == current_user.id or
        (db_project and db_project.owner_id == current_user.id)
    )
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this task"
        )
        
    return crud.update_task(db=db, task_id=task_id, task=task, user_id=current_user.id)

@router.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_task = crud.get_task(db=db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
        
    db_project = crud.get_project(db, db_task.project_id)
    is_authorized = (
        current_user.role in ["admin", "manager"] or
        db_task.creator_id == current_user.id or
        (db_project and db_project.owner_id == current_user.id)
    )
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this task"
        )
        
    crud.delete_task(db=db, task_id=task_id, user_id=current_user.id)
    return None
