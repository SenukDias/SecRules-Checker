from __future__ import annotations

import re

from app.models.network import Device, Interface, NetworkModel, Rule, RuleAction
from app.parsers.base import BaseParser

_SET_RE = re.compile(r'^set\s+(?P<key>\S+)\s+(?P<value>.+)$', re.IGNORECASE)
_HOSTNAME_RE = re.compile(r'^set\s+hostname\s+"?(?P<name>[^"\s]+)"?', re.IGNORECASE)


def _split_quoted(value: str) -> list[str]:
    return re.findall(r'"([^"]+)"|(\S+)', value)


def _flatten(matches: list[tuple[str, str]]) -> list[str]:
    return [a or b for a, b in matches]


class FortiGateParser(BaseParser):
    vendor = "fortigate"

    @classmethod
    def detect(cls, raw_text: str, filename: str) -> bool:
        return "config firewall policy" in raw_text.lower()

    def parse(self, raw_text: str, filename: str) -> NetworkModel:
        hostname = filename
        interfaces: list[Interface] = []
        rules: list[Rule] = []

        section = None
        current: dict | None = None
        current_id: str | None = None

        for raw_line in raw_text.splitlines():
            line = raw_line.strip()
            if m := _HOSTNAME_RE.match(line):
                hostname = m.group("name")
                continue
            if line.startswith("config system interface"):
                section = "interface"
                continue
            if line.startswith("config firewall policy"):
                section = "policy"
                continue
            if line == "end":
                section = None
                continue
            if section is None:
                continue

            if m := re.match(r'^edit\s+"?(?P<id>[^"]+)"?$', line, re.IGNORECASE):
                current = {}
                current_id = m.group("id")
                continue
            if line == "next":
                if current is not None and current_id is not None:
                    if section == "interface":
                        interfaces.append(
                            Interface(
                                name=current_id,
                                zone=current.get("zone"),
                                ip_address=(current.get("ip") or "").split()[0] if current.get("ip") else None,
                                subnet_mask=(current.get("ip") or "").split()[1] if current.get("ip") and len(current.get("ip", "").split()) > 1 else None,
                            )
                        )
                    elif section == "policy":
                        position = len(rules) + 1
                        action = (current.get("action") or "deny").lower()
                        services = _flatten(_split_quoted(current.get("service", "ALL")))
                        src = _flatten(_split_quoted(current.get("srcaddr", "all")))
                        dst = _flatten(_split_quoted(current.get("dstaddr", "all")))
                        rules.append(
                            Rule(
                                id=f"policy-{current_id}",
                                position=position,
                                name=current.get("name", f"policy-{current_id}").strip('"'),
                                action=RuleAction.ALLOW if action == "accept" else RuleAction.DENY,
                                source=src,
                                destination=dst,
                                services=services,
                                zones=(current.get("srcintf", "").strip('"'), current.get("dstintf", "").strip('"')),
                                logging_enabled=current.get("logtraffic", "disable") not in ("disable", ""),
                                disabled=current.get("status", "enable") == "disable",
                                raw=str(current),
                            )
                        )
                current = None
                current_id = None
                continue
            if current is not None and (m := _SET_RE.match(line)):
                current[m.group("key").lower()] = m.group("value").strip()

        device = Device(
            name=hostname,
            vendor=self.vendor,
            device_type="firewall",
            interfaces=interfaces,
            rules=rules,
            raw_source=raw_text,
        )
        return NetworkModel(devices=[device])
