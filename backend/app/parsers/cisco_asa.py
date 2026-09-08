from __future__ import annotations

import re

from app.models.network import Device, Interface, NetworkModel, Rule, RuleAction
from app.parsers._cisco_common import parse_acl_tokens
from app.parsers.base import BaseParser

_ACL_RE = re.compile(
    r"^access-list\s+(?P<acl>\S+)\s+extended\s+(?P<action>permit|deny)\s+(?P<rest>.+)$",
    re.IGNORECASE,
)
_IFACE_RE = re.compile(r"^interface\s+(?P<name>\S+)", re.IGNORECASE)
_NAMEIF_RE = re.compile(r"^\s*nameif\s+(?P<zone>\S+)", re.IGNORECASE)
_IPADDR_RE = re.compile(r"^\s*ip address\s+(?P<ip>\d+\.\d+\.\d+\.\d+)\s+(?P<mask>\d+\.\d+\.\d+\.\d+)", re.IGNORECASE)
_HOSTNAME_RE = re.compile(r"^hostname\s+(?P<name>\S+)", re.IGNORECASE)


class CiscoASAParser(BaseParser):
    vendor = "cisco_asa"

    @classmethod
    def detect(cls, raw_text: str, filename: str) -> bool:
        return bool(re.search(r"access-list .+ extended (permit|deny)", raw_text, re.IGNORECASE)) or \
            bool(re.search(r"^ASA Version", raw_text, re.MULTILINE))

    def parse(self, raw_text: str, filename: str) -> NetworkModel:
        lines = raw_text.splitlines()
        hostname = filename
        interfaces: list[Interface] = []
        rules: list[Rule] = []

        current_iface: dict | None = None
        for line in lines:
            if m := _HOSTNAME_RE.match(line):
                hostname = m.group("name")
                continue
            if m := _IFACE_RE.match(line):
                if current_iface:
                    interfaces.append(_flush_iface(current_iface))
                current_iface = {"name": m.group("name")}
                continue
            if current_iface is not None:
                if m := _NAMEIF_RE.match(line):
                    current_iface["zone"] = m.group("zone")
                    continue
                if m := _IPADDR_RE.match(line):
                    current_iface["ip"] = m.group("ip")
                    current_iface["mask"] = m.group("mask")
                    continue
                if line.strip() == "!" or line.strip() == "":
                    interfaces.append(_flush_iface(current_iface))
                    current_iface = None
                    continue

            if m := _ACL_RE.match(line.strip()):
                position = len(rules) + 1
                parsed = parse_acl_tokens(m.group("rest").split())
                rules.append(
                    Rule(
                        id=f"{m.group('acl')}-{position}",
                        position=position,
                        name=m.group("acl"),
                        action=RuleAction.ALLOW if m.group("action").lower() == "permit" else RuleAction.DENY,
                        source=[parsed["source"]],
                        destination=[parsed["destination"]],
                        services=[parsed["service"]],
                        logging_enabled=parsed["log"],
                        raw=line.strip(),
                    )
                )

        if current_iface:
            interfaces.append(_flush_iface(current_iface))

        device = Device(
            name=hostname,
            vendor=self.vendor,
            device_type="firewall",
            interfaces=interfaces,
            rules=rules,
            raw_source=raw_text,
        )
        return NetworkModel(devices=[device])


def _flush_iface(data: dict) -> Interface:
    return Interface(
        name=data.get("name", "unknown"),
        zone=data.get("zone"),
        ip_address=data.get("ip"),
        subnet_mask=data.get("mask"),
        is_wan=(data.get("zone") == "outside"),
    )
