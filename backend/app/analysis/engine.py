from __future__ import annotations

from sqlalchemy.orm import Session

from app.analysis.checks import run_builtin_checks, run_custom_checks
from app.models.db_models import CustomRule, Finding
from app.models.network import NetworkModel

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def analyze(model: NetworkModel, db: Session, job_id: str) -> list[Finding]:
    custom_rules = db.query(CustomRule).all()

    results = run_builtin_checks(model)
    results.extend(run_custom_checks(model, custom_rules))
    results.sort(key=lambda f: SEVERITY_ORDER.get(f.severity, 99))

    findings = [
        Finding(
            job_id=job_id,
            severity=r.severity,
            category=r.category,
            rule_ref=r.rule_ref,
            device_name=r.device_name,
            description=r.description,
            remediation=r.remediation,
        )
        for r in results
    ]
    db.add_all(findings)
    db.commit()
    return findings
