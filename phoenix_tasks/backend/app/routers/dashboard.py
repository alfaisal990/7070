from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .. import schemas, auth, models

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/stats", response_model=schemas.DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    total_projects = db.query(models.Project).count()
    total_tasks = db.query(models.Task).count()
    todo_tasks = db.query(models.Task).filter(models.Task.status == "todo").count()
    in_progress_tasks = db.query(models.Task).filter(models.Task.status == "in_progress").count()
    done_tasks = db.query(models.Task).filter(models.Task.status == "done").count()
    high_priority_tasks = db.query(models.Task).filter(models.Task.priority == "high").count()

    return {
        "total_projects": total_projects,
        "total_tasks": total_tasks,
        "todo_tasks": todo_tasks,
        "in_progress_tasks": in_progress_tasks,
        "done_tasks": done_tasks,
        "high_priority_tasks": high_priority_tasks
    }
