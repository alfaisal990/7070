from typing import List
import time
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from ..database import get_db
from .. import schemas, crud, models, auth

class RateLimiter:
    def __init__(self, limit: int, window: float):
        self.limit = limit
        self.window = window
        self.requests = {}

    def __call__(self, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        user_reqs = self.requests.setdefault(client_ip, [])
        user_reqs = [t for t in user_reqs if now - t < self.window]
        self.requests[client_ip] = user_reqs
        if len(user_reqs) >= self.limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
        self.requests[client_ip].append(now)

task_limiter = RateLimiter(limit=30, window=60.0)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.post("", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task: schemas.TaskCreate, request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user), rate_limit = Depends(task_limiter)):
    return crud.create_user_task(db=db, task=task, owner_id=current_user.id)

@router.get("", response_model=List[schemas.TaskResponse])
def read_tasks(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user), rate_limit = Depends(task_limiter)):
    return crud.get_tasks(db=db, owner_id=current_user.id, skip=skip, limit=limit)

@router.get("/{task_id}", response_model=schemas.TaskResponse)
def read_task(task_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_task = crud.get_task(db=db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if db_task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this task")
    return db_task

@router.put("/{task_id}", response_model=schemas.TaskResponse)
def update_task(task_id: int, task: schemas.TaskUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_task = crud.get_task(db=db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if db_task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this task")
    return crud.update_task(db=db, task_id=task_id, task=task)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_task = crud.get_task(db=db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if db_task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this task")
    crud.delete_task(db=db, task_id=task_id)
    return None
