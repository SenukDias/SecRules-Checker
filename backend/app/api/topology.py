from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.jobs import _get_job_or_404
from app.auth import CurrentUser, get_current_user
from app.db import get_db

router = APIRouter(prefix="/jobs", tags=["topology"])


@router.get("/{job_id}/topology")
def get_topology(job_id: str, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    job = _get_job_or_404(db, user, job_id)
    return job.topology or {"nodes": [], "edges": []}
