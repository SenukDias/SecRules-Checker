from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import ROLE_ADMIN, CurrentUser, get_current_user
from app.db import get_db
from app.models.db_models import Job

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _visible_jobs(db: Session, user: CurrentUser):
    query = db.query(Job)
    if not user.has_role(ROLE_ADMIN):
        query = query.filter(Job.owner_sub == user.sub)
    return query.order_by(Job.created_at.desc())


@router.get("")
def list_jobs(db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    jobs = _visible_jobs(db, user).all()
    return [
        {
            "id": j.id,
            "filename": j.filename,
            "vendor": j.vendor,
            "status": j.status,
            "error": j.error,
            "created_at": j.created_at,
        }
        for j in jobs
    ]


def _get_job_or_404(db: Session, user: CurrentUser, job_id: str) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    if not user.has_role(ROLE_ADMIN) and job.owner_sub != user.sub:
        raise HTTPException(403, "Not your job")
    return job


@router.get("/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    job = _get_job_or_404(db, user, job_id)
    return {
        "id": job.id,
        "filename": job.filename,
        "vendor": job.vendor,
        "status": job.status,
        "error": job.error,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }
