from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import schemas, crud, auth, models

router = APIRouter(prefix="/api/activities", tags=["activities"])

@router.get("", response_model=List[schemas.ActivityResponse])
def read_activity_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.RoleChecker(["admin", "manager"]))
):
    return crud.get_activities(db=db, skip=skip, limit=limit)
