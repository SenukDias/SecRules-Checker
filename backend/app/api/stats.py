from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.jobs import _visible_jobs
from app.auth import CurrentUser, get_current_user
from app.db import get_db
from app.models.db_models import Finding

router = APIRouter(prefix="/stats", tags=["stats"])

SEVERITY_WEIGHT = {"critical": 10, "high": 6, "medium": 3, "low": 1, "info": 0}
TREND_DAYS = 14


@router.get("/summary")
def get_summary(db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    jobs = _visible_jobs(db, user).all()
    job_ids = [j.id for j in jobs]

    jobs_by_status = Counter(j.status for j in jobs)

    severity_counts = {sev: 0 for sev in ("critical", "high", "medium", "low", "info")}
    if job_ids:
        findings = db.query(Finding).filter(Finding.job_id.in_(job_ids)).all()
        for f in findings:
            severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1

    total_findings = sum(severity_counts.values())
    weighted = sum(SEVERITY_WEIGHT.get(sev, 0) * count for sev, count in severity_counts.items())
    max_possible = total_findings * SEVERITY_WEIGHT["critical"] or 1
    # Higher weighted-severity share -> lower risk score (100 = clean, 0 = critical-heavy).
    risk_score = round(max(0, 100 - (weighted / max_possible) * 100)) if total_findings else 100

    since = datetime.utcnow() - timedelta(days=TREND_DAYS)
    daily_counts: dict[str, int] = defaultdict(int)
    for j in jobs:
        if j.created_at >= since:
            daily_counts[j.created_at.strftime("%Y-%m-%d")] += 1
    trend = [
        {"date": (since + timedelta(days=i)).strftime("%Y-%m-%d"), "jobs": daily_counts.get((since + timedelta(days=i)).strftime("%Y-%m-%d"), 0)}
        for i in range(TREND_DAYS + 1)
    ]

    return {
        "total_jobs": len(jobs),
        "jobs_by_status": jobs_by_status,
        "severity_counts": severity_counts,
        "total_findings": total_findings,
        "risk_score": risk_score,
        "trend": trend,
    }
