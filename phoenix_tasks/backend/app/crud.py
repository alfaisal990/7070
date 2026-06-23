from sqlalchemy.orm import Session
from . import models, schemas
from .auth import get_password_hash

# Activity Logger
def log_activity(db: Session, user_id: int, action: str, details: str = None):
    db_activity = models.Activity(user_id=user_id, action=action, details=details)
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity

# User operations
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    log_activity(db, db_user.id, "register", f"User registered with role {user.role}")
    return db_user

# Project operations
def get_project(db: Session, project_id: int):
    return db.query(models.Project).filter(models.Project.id == project_id).first()

def get_projects(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Project).offset(skip).limit(limit).all()

def create_project(db: Session, project: schemas.ProjectCreate, owner_id: int):
    db_project = models.Project(**project.model_dump(), owner_id=owner_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    log_activity(db, owner_id, "create_project", f"Created project '{db_project.name}'")
    return db_project

def update_project(db: Session, project_id: int, project: schemas.ProjectUpdate, user_id: int):
    db_project = get_project(db, project_id)
    if not db_project:
        return None
    for key, val in project.model_dump(exclude_unset=True).items():
        setattr(db_project, key, val)
    db.commit()
    db.refresh(db_project)
    log_activity(db, user_id, "update_project", f"Updated project '{db_project.name}'")
    return db_project

def delete_project(db: Session, project_id: int, user_id: int):
    db_project = get_project(db, project_id)
    if not db_project:
        return False
    name = db_project.name
    db.delete(db_project)
    db.commit()
    log_activity(db, user_id, "delete_project", f"Deleted project '{name}'")
    return True

# Task operations
def get_task(db: Session, task_id: int):
    return db.query(models.Task).filter(models.Task.id == task_id).first()

def get_tasks(db: Session, project_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Task).filter(models.Task.project_id == project_id).offset(skip).limit(limit).all()

def create_task(db: Session, task: schemas.TaskCreate, project_id: int, creator_id: int):
    db_task = models.Task(**task.model_dump(), project_id=project_id, creator_id=creator_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    log_activity(db, creator_id, "create_task", f"Created task '{db_task.title}' under project ID {project_id}")
    return db_task

def update_task(db: Session, task_id: int, task: schemas.TaskUpdate, user_id: int):
    db_task = get_task(db, task_id)
    if not db_task:
        return None
    for key, val in task.model_dump(exclude_unset=True).items():
        setattr(db_task, key, val)
    db.commit()
    db.refresh(db_task)
    log_activity(db, user_id, "update_task", f"Updated task '{db_task.title}' (Status: {db_task.status})")
    return db_task

def delete_task(db: Session, task_id: int, user_id: int):
    db_task = get_task(db, task_id)
    if not db_task:
        return False
    title = db_task.title
    db.delete(db_task)
    db.commit()
    log_activity(db, user_id, "delete_task", f"Deleted task '{title}'")
    return True

# Comment operations
def create_comment(db: Session, comment: schemas.CommentCreate, task_id: int, author_id: int):
    db_comment = models.Comment(**comment.model_dump(), task_id=task_id, author_id=author_id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    log_activity(db, author_id, "add_comment", f"Added comment to task ID {task_id}")
    return db_comment

def get_comments(db: Session, task_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Comment).filter(models.Comment.task_id == task_id).offset(skip).limit(limit).all()

# Activity log operations
def get_activities(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Activity).order_by(models.Activity.created_at.desc()).offset(skip).limit(limit).all()
