from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth import ROLE_ADMIN, ROLE_ANALYST, CurrentUser, require_roles
from app.config import get_settings
from app.db import get_db
from app.models.db_models import Job

router = APIRouter(prefix="/jobs", tags=["upload"])
settings = get_settings()


@router.post("", status_code=201)
async def upload_config(
    file: UploadFile,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_ANALYST)),
):
    contents = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(413, f"File exceeds {settings.max_upload_size_mb}MB limit")
    if not contents.strip():
        raise HTTPException(400, "Uploaded file is empty")

    job_id = str(uuid.uuid4())
    os.makedirs(settings.upload_dir, exist_ok=True)
    upload_path = os.path.join(settings.upload_dir, f"{job_id}_{file.filename}")
    with open(upload_path, "wb") as fh:
        fh.write(contents)

    job = Job(id=job_id, filename=file.filename or "upload.txt", owner_sub=user.sub, status="pending")
    db.add(job)
    db.commit()

    from worker import process_job

    process_job.delay(job_id, upload_path)

    return {"job_id": job_id, "status": job.status}
