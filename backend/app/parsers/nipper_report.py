from __future__ import annotations

import re
from html.parser import HTMLParser

from app.models.network import Device, ImportedFinding, NetworkModel
from app.parsers.base import BaseParser

_RISK_MAP = {
    "crit": "critical",
    "critical": "critical",
    "high": "high",
    "med": "medium",
    "medium": "medium",
    "low": "low",
    "info": "info",
    "informational": "info",
}


class _NipperHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.findings: list[dict[str, str]] = []
        self.sections: dict[str, dict[str, str]] = {}
        self._in_summary_table = False
        self._table_depth = 0
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._row_metadata: list[dict[str, str]] | None = None
        self._cell_class = ""
        self._cell_href = ""
        self._report_depth = 0
        self._capture_section: str | None = None
        self._section_blocks: dict[str, list[str]] = {}
        self._block_name: str | None = None
        self._heading_parts: list[str] | None = None
        self._script_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag in {"script", "style"}:
            self._script_depth += 1
        if tag == "table" and "findings summary table" in attributes.get("summary", "").lower():
            self._in_summary_table = True
            self._table_depth = 1
        elif self._in_summary_table and tag == "table":
            self._table_depth += 1
        if self._in_summary_table and tag == "tr":
            self._row = []
            self._row_metadata = []
        elif self._in_summary_table and tag in {"td", "th"} and self._row is not None:
            self._cell = []
            self._cell_class = ""
            self._cell_href = ""
        elif self._cell is not None:
            if tag == "font":
                self._cell_class = attributes.get("class", "")
            elif tag == "a":
                self._cell_href = attributes.get("href", "")

        if tag == "div" and "reportsection" in attributes.get("class", "").split():
            self._report_depth = 1
        elif tag == "div" and self._report_depth:
            self._report_depth += 1
        if tag == "a" and self._report_depth and self._capture_section is None:
            anchor = attributes.get("id", "")
            if any(finding.get("anchor") == anchor for finding in self.findings):
                self._capture_section = anchor
                self._section_blocks = {}
                self._block_name = None
        if tag == "h3" and self._capture_section:
            self._heading_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._script_depth:
            self._script_depth -= 1
        if self._in_summary_table and tag == "table":
            self._table_depth -= 1
            if self._table_depth == 0:
                self._in_summary_table = False
        if tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._row.append(" ".join(self._cell).strip())
            if self._row_metadata is not None:
                self._row_metadata.append({"class": self._cell_class, "href": self._cell_href})
            self._cell = None
        if tag == "tr" and self._row is not None:
            if len(self._row) >= 4 and self._row[0].strip().lower() != "finding id":
                risk_class = self._row_metadata[2]["class"] if self._row_metadata and len(self._row_metadata) > 2 else ""
                section_href = self._row_metadata[3]["href"] if self._row_metadata and len(self._row_metadata) > 3 else ""
                risk_match = re.search(r"rate-(crit|high|med|medium|low|info|informational)", risk_class, re.IGNORECASE)
                anchor_match = re.search(r"#(T\d+)", section_href)
                section_match = re.search(r"\d+(?:\.\d+)+", self._row[3])
                if risk_match and anchor_match:
                    self.findings.append({
                        "id": self._row[0],
                        "title": self._row[1],
                        "severity": _RISK_MAP[risk_match.group(1).lower()],
                        "anchor": anchor_match.group(1),
                        "section": section_match.group(0) if section_match else "",
                    })
            self._row = None
            self._row_metadata = None
        if tag == "h3" and self._heading_parts is not None:
            heading = " ".join(self._heading_parts).strip()
            match = re.search(r"\d+(?:\.\d+)+\s+(.+)$", heading)
            self._block_name = match.group(1).strip().lower() if match else heading.lower()
            self._section_blocks.setdefault(self._block_name, [])
            self._heading_parts = None
        if tag == "div" and self._report_depth:
            self._report_depth -= 1
            if self._report_depth == 0:
                if self._capture_section:
                    self.sections[self._capture_section] = {
                        name: " ".join(parts).strip()
                        for name, parts in self._section_blocks.items()
                    }
                self._capture_section = None
                self._block_name = None

    def handle_data(self, data: str) -> None:
        if self._script_depth or not data.strip():
            return
        text = re.sub(r"\s+", " ", data).strip()
        if self._cell is not None:
            self._cell.append(text)
        if self._heading_parts is not None:
            self._heading_parts.append(text)
        elif self._capture_section and self._block_name:
            self._section_blocks[self._block_name].append(text)


class NipperReportParser(BaseParser):
    vendor = "nipper_report"

    @classmethod
    def detect(cls, raw_text: str, filename: str) -> bool:
        head = raw_text[:100_000].lower()
        return "<html" in head and ("nipper from titania" in head or "created by nipper" in head)

    def parse(self, raw_text: str, filename: str) -> NetworkModel:
        html_parser = _NipperHTMLParser()
        html_parser.feed(raw_text)
        if not html_parser.findings:
            raise ValueError("Nipper report found, but no security findings summary table was detected.")

        device_name = _device_name(raw_text, filename)
        imported_findings = []
        for item in html_parser.findings:
            section = html_parser.sections.get(item["anchor"], {})
            title = item["title"]
            details = [section[key] for key in ("finding", "impact", "ease") if section.get(key)]
            imported_findings.append(
                ImportedFinding(
                    severity=item["severity"],
                    category="Nipper Audit",
                    rule_ref=f"{item['id']} ({item['section']})".strip(),
                    device_name=device_name,
                    description=f"{title}. " + " ".join(details),
                    remediation=section.get("recommendation") or f"Review Nipper report section {item['section']} for its recommendation.",
                )
            )

        device_type = "firewall" if re.search(r"\bASA\s*\d*\b", raw_text, re.IGNORECASE) else "router"
        device = Device(name=device_name, vendor=self.vendor, device_type=device_type)
        return NetworkModel(devices=[device], imported_findings=imported_findings)


def _device_name(raw_text: str, filename: str) -> str:
    match = re.search(r"Nipper identified\s+\d+\s+filter rules on\s+([\w.-]+)", raw_text, re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(r"^hostname\s+(\S+)", raw_text, re.IGNORECASE | re.MULTILINE)
    return match.group(1) if match else filename.rsplit(".", 1)[0]