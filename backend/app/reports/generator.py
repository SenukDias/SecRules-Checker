from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from weasyprint import HTML

from app.models.db_models import Finding, Job

TEMPLATE_DIR = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

SEVERITY_FILL = {
    "critical": "D32F2F",
    "high": "E8620C",
    "medium": "B8960C",
    "low": "1F9D55",
    "info": "607D8B",
}


def _severity_counts(findings: list[Finding]) -> dict[str, int]:
    counts = Counter(f.severity for f in findings)
    for sev in ("critical", "high", "medium", "low", "info"):
        counts.setdefault(sev, 0)
    ordered = {sev: counts[sev] for sev in ("critical", "high", "medium", "low", "info")}
    return ordered


def render_html(job: Job, findings: list[Finding], topology_image_b64: str | None = None) -> str:
    template = _env.get_template("report.html")
    return template.render(
        job=job,
        findings=findings,
        severity_counts=_severity_counts(findings),
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        topology_image=topology_image_b64,
    )


def render_pdf(job: Job, findings: list[Finding], topology_image_b64: str | None = None) -> bytes:
    html_content = render_html(job, findings, topology_image_b64)
    return HTML(string=html_content, base_url=str(TEMPLATE_DIR)).write_pdf()


def render_excel(job: Job, findings: list[Finding]) -> bytes:
    from io import BytesIO

    wb = Workbook()
    ws = wb.active
    ws.title = "Findings"
    headers = ["Severity", "Category", "Device", "Rule", "Description", "Remediation"]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="1F2430", end_color="1F2430", fill_type="solid")

    for f in findings:
        ws.append([f.severity.upper(), f.category, f.device_name, f.rule_ref, f.description, f.remediation])
        row = ws[ws.max_row]
        fill_color = SEVERITY_FILL.get(f.severity, "607D8B")
        row[0].fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
        row[0].font = Font(color="FFFFFF", bold=True)

    for col, width in zip("ABCDEF", (12, 22, 20, 20, 60, 60)):
        ws.column_dimensions[col].width = width

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
