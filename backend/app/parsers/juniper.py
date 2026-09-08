from __future__ import annotations

import re

from app.models.network import Device, Interface, NetworkModel, Rule, RuleAction
from app.parsers.base import BaseParser

_HOSTNAME_RE = re.compile(r"^set\s+system\s+host-name\s+(?P<name>\S+)", re.IGNORECASE)
_IFACE_RE = re.compile(
    r"^set\s+interfaces\s+(?P<name>\S+)\s+unit\s+\d+\s+family\s+inet\s+address\s+(?P<ip>[\d.]+)/(?P<mask>\d+)",
    re.IGNORECASE,
)
_POLICY_RE = re.compile(
    r"^set\s+security\s+policies\s+from-zone\s+(?P<from>\S+)\s+to-zone\s+(?P<to>\S+)\s+policy\s+(?P<name>\S+)\s+(?P<rest>.+)$",
    re.IGNORECASE,
)


class JuniperParser(BaseParser):
    vendor = "juniper"

    @classmethod
    def detect(cls, raw_text: str, filename: str) -> bool:
        return bool(re.search(r"^set\s+security\s+policies\s+from-zone", raw_text, re.IGNORECASE | re.MULTILINE))

    def parse(self, raw_text: str, filename: str) -> NetworkModel:
        hostname = filename
        interfaces: list[Interface] = []
        # key = (from, to, name) -> accumulated rule fields
        policies: dict[tuple[str, str, str], dict] = {}
        order: list[tuple[str, str, str]] = []

        for raw_line in raw_text.splitlines():
            line = raw_line.strip()
            if m := _HOSTNAME_RE.match(line):
                hostname = m.group("name")
                continue
            if m := _IFACE_RE.match(line):
                interfaces.append(Interface(name=m.group("name"), zone=None, ip_address=m.group("ip"), subnet_mask=m.group("mask")))
                continue
            if m := _POLICY_RE.match(line):
                key = (m.group("from"), m.group("to"), m.group("name"))
                if key not in policies:
                    policies[key] = {"source": [], "destination": [], "application": [], "action": "deny", "log": False}
                    order.append(key)
                rest = m.group("rest")
                if sm := re.search(r"source-address\s+(\S+)", rest):
                    policies[key]["source"].append(sm.group(1))
                if dm := re.search(r"destination-address\s+(\S+)", rest):
                    policies[key]["destination"].append(dm.group(1))
                if am := re.search(r"application\s+(\S+)", rest):
                    policies[key]["application"].append(am.group(1))
                if "then permit" in rest.lower():
                    policies[key]["action"] = "permit"
                if "then deny" in rest.lower() or "then reject" in rest.lower():
                    policies[key]["action"] = "deny"
                if "log" in rest.lower():
                    policies[key]["log"] = True

        rules = []
        for position, key in enumerate(order, start=1):
            data = policies[key]
            from_zone, to_zone, name = key
            rules.append(
                Rule(
                    id=f"{name}-{position}",
                    position=position,
                    name=name,
                    action=RuleAction.ALLOW if data["action"] == "permit" else RuleAction.DENY,
                    source=data["source"] or ["any"],
                    destination=data["destination"] or ["any"],
                    services=data["application"] or ["any"],
                    zones=(from_zone, to_zone),
                    logging_enabled=data["log"],
                    raw=str(data),
                )
            )

        device = Device(
            name=hostname,
            vendor=self.vendor,
            device_type="firewall",
            interfaces=interfaces,
            rules=rules,
            raw_source=raw_text,
        )
        return NetworkModel(devices=[device])
