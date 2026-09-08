from __future__ import annotations

import csv
import io

from app.models.network import Device, Interface, NetworkModel, Rule, RuleAction
from app.parsers.base import BaseParser

EXPECTED_COLUMNS = {"name", "action", "source", "destination", "service"}


class GenericCsvParser(BaseParser):
    """Universal fallback: any vendor rule list exported/reformatted into this CSV template.

    Required columns: name, action, source, destination, service
    Optional columns: zone_from, zone_to, log, disabled, hitcount, description, device
    """

    vendor = "generic_csv"

    @classmethod
    def detect(cls, raw_text: str, filename: str) -> bool:
        if not filename.lower().endswith((".csv", ".txt")):
            return False
        first_line = raw_text.splitlines()[0] if raw_text.splitlines() else ""
        header = {h.strip().lower() for h in first_line.split(",")}
        return EXPECTED_COLUMNS.issubset(header)

    def parse(self, raw_text: str, filename: str) -> NetworkModel:
        reader = csv.DictReader(io.StringIO(raw_text))
        rules: list[Rule] = []
        device_name = filename

        for position, row in enumerate(reader, start=1):
            row = {k.strip().lower(): (v or "").strip() for k, v in row.items()}
            device_name = row.get("device") or device_name
            action = row.get("action", "deny").lower()
            rules.append(
                Rule(
                    id=f"row-{position}",
                    position=position,
                    name=row.get("name") or f"rule-{position}",
                    action=RuleAction.ALLOW if action in ("allow", "permit", "accept") else RuleAction.DENY,
                    source=[s.strip() for s in row.get("source", "any").split(";") if s.strip()] or ["any"],
                    destination=[s.strip() for s in row.get("destination", "any").split(";") if s.strip()] or ["any"],
                    services=[s.strip() for s in row.get("service", "any").split(";") if s.strip()] or ["any"],
                    zones=(row.get("zone_from") or None, row.get("zone_to") or None),
                    logging_enabled=row.get("log", "").lower() in ("yes", "true", "1", "enable"),
                    disabled=row.get("disabled", "").lower() in ("yes", "true", "1"),
                    hitcount=int(row["hitcount"]) if row.get("hitcount", "").isdigit() else None,
                    description=row.get("description", ""),
                    raw=str(row),
                )
            )

        device = Device(
            name=device_name,
            vendor="generic",
            device_type="firewall",
            interfaces=[],
            rules=rules,
            raw_source=raw_text,
        )
        return NetworkModel(devices=[device])
