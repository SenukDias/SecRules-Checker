from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.jobs import _get_job_or_404
from app.auth import CurrentUser, get_current_user
from app.db import get_db
from app.models.db_models import Finding

router = APIRouter(prefix="/jobs", tags=["findings"])


@router.get("/{job_id}/findings")
def list_findings(
    job_id: str,
    severity: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    _get_job_or_404(db, user, job_id)
    query = db.query(Finding).filter(Finding.job_id == job_id)
    if severity:
        query = query.filter(Finding.severity == severity)
    findings = query.all()
    return [
        {
            "id": f.id,
            "severity": f.severity,
            "category": f.category,
            "rule_ref": f.rule_ref,
            "device_name": f.device_name,
            "description": f.description,
            "remediation": f.remediation,
        }
        for f in findings
    ]
