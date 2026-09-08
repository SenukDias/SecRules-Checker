from __future__ import annotations

import re

from app.models.network import Device, Interface, NetworkModel, Rule, RuleAction
from app.parsers.base import BaseParser

_RULE_RE = re.compile(
    r"^set\s+rulebase\s+security\s+rules\s+(?P<name>\"[^\"]+\"|\S+)\s+(?P<rest>.+)$",
    re.IGNORECASE,
)
_KV_RE = re.compile(
    r"\b(from|to|source|destination|application|service|action|log-end|disabled)\s+(.+?)(?=\s+(?:from|to|source|destination|application|service|action|log-end|disabled)\s|$)",
    re.IGNORECASE,
)
_IFACE_RE = re.compile(
    r"^set\s+network\s+interface\s+\S+\s+(?P<name>\S+)\s+layer3\s+ip\s+(?P<ip>[\d.]+)/(?P<mask>\d+)",
    re.IGNORECASE,
)
_HOSTNAME_RE = re.compile(r"^set\s+deviceconfig\s+system\s+hostname\s+(?P<name>\S+)", re.IGNORECASE)


class PaloAltoParser(BaseParser):
    vendor = "palo_alto"

    @classmethod
    def detect(cls, raw_text: str, filename: str) -> bool:
        return "set rulebase security rules" in raw_text.lower()

    def parse(self, raw_text: str, filename: str) -> NetworkModel:
        hostname = filename
        interfaces: list[Interface] = []
        rules: list[Rule] = []

        for line in raw_text.splitlines():
            stripped = line.strip()
            if m := _HOSTNAME_RE.match(stripped):
                hostname = m.group("name")
                continue
            if m := _IFACE_RE.match(stripped):
                interfaces.append(Interface(name=m.group("name"), zone=None, ip_address=m.group("ip"), subnet_mask=m.group("mask")))
                continue
            if m := _RULE_RE.match(stripped):
                name = m.group("name").strip('"')
                fields = {k.lower(): v.strip().strip('"') for k, v in _KV_RE.findall(m.group("rest"))}
                position = len(rules) + 1
                action = fields.get("action", "allow").lower()
                rules.append(
                    Rule(
                        id=f"{name}-{position}",
                        position=position,
                        name=name,
                        action=RuleAction.ALLOW if action == "allow" else RuleAction.DENY,
                        source=fields.get("source", "any").split(),
                        destination=fields.get("destination", "any").split(),
                        services=fields.get("service", "application-default").split(),
                        zones=(fields.get("from"), fields.get("to")),
                        logging_enabled=fields.get("log-end", "no").lower() == "yes",
                        disabled=fields.get("disabled", "no").lower() == "yes",
                        raw=stripped,
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
