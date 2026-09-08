from __future__ import annotations

import asyncio
import dataclasses
from concurrent.futures import ThreadPoolExecutor

from celery_app import celery_app
from app.analysis import analyze
from app.db import SessionLocal
from app.enrichment import enrich_ips
from app.models.db_models import Finding, Job
from app.parsers import UnsupportedFormatError, parse_export
from app.topology import build_topology

SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


def _max_severity_by_device(findings: list[Finding]) -> dict[str, str]:
    result: dict[str, str] = {}
    for f in findings:
        current = result.get(f.device_name, "info")
        if SEVERITY_RANK.get(f.severity, 0) > SEVERITY_RANK.get(current, 0):
            result[f.device_name] = f.severity
    return result


def _run_async(coro):
    """Run a coroutine to completion, whether or not an event loop is already running
    (Celery eager mode can execute in-process inside FastAPI's running loop)."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with ThreadPoolExecutor(1) as pool:
        return pool.submit(asyncio.run, coro).result()


def _read_upload(path: str) -> str:
    with open(path, encoding="utf-8", errors="ignore") as fh:
        return fh.read()


@celery_app.task(name="worker.process_job")
def process_job(job_id: str, upload_path: str) -> None:
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is None:
            return

        job.status = "parsing"
        db.commit()

        raw_text = _read_upload(upload_path)
        try:
            vendor, model = parse_export(raw_text, job.filename)
        except UnsupportedFormatError as exc:
            job.status = "failed"
            job.error = str(exc)
            db.commit()
            return

        job.vendor = vendor
        job.parsed_model = dataclasses.asdict(model)
        job.status = "analyzing"
        db.commit()

        findings = analyze(model, db, job_id)
        severity_by_device = _max_severity_by_device(findings)

        public_ips = model.all_public_ips()
        enrichment = _run_async(enrich_ips(public_ips)) if public_ips else {}
        job.topology = build_topology(model, enrichment, severity_by_device)

        job.status = "done"
        db.commit()
    except Exception as exc:  # noqa: BLE001 - surface any failure to the user
        job = db.get(Job, job_id)
        if job:
            job.status = "failed"
            job.error = str(exc)
            db.commit()
        raise
    finally:
        db.close()
