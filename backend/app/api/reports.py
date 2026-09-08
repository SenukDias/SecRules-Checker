from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.jobs import _get_job_or_404
from app.auth import CurrentUser, get_current_user
from app.db import get_db
from app.models.db_models import Finding
from app.reports import render_excel, render_html, render_pdf

router = APIRouter(prefix="/jobs", tags=["reports"])

MEDIA_TYPES = {
    "pdf": "application/pdf",
    "html": "text/html",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


class ReportRequest(BaseModel):
    format: str = "pdf"
    topology_image_base64: str | None = None


@router.post("/{job_id}/report")
def export_report(
    job_id: str,
    body: ReportRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    job = _get_job_or_404(db, user, job_id)
    if job.status != "done":
        raise HTTPException(409, f"Job is not ready for report export (status={job.status})")

    fmt = body.format.lower()
    if fmt not in MEDIA_TYPES:
        raise HTTPException(400, f"Unsupported format '{fmt}'. Use pdf, html, or xlsx.")

    findings = db.query(Finding).filter(Finding.job_id == job_id).all()

    if fmt == "pdf":
        content = render_pdf(job, findings, body.topology_image_base64)
    elif fmt == "html":
        content = render_html(job, findings, body.topology_image_base64).encode("utf-8")
    else:
        content = render_excel(job, findings)

    filename = f"rulescope-report-{job.filename}.{fmt}"
    return Response(
        content=content,
        media_type=MEDIA_TYPES[fmt],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
