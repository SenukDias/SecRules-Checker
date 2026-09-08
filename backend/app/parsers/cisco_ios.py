from __future__ import annotations

import re

from app.models.network import Device, Interface, NetworkModel, Rule, RuleAction
from app.parsers._cisco_common import parse_acl_tokens
from app.parsers.base import BaseParser

_ACL_RE = re.compile(
    r"^access-list\s+(?P<num>\d+)\s+(?P<action>permit|deny)\s+(?P<rest>.+)$",
    re.IGNORECASE,
)
_IFACE_RE = re.compile(r"^interface\s+(?P<name>\S+)", re.IGNORECASE)
_IPADDR_RE = re.compile(r"^\s*ip address\s+(?P<ip>\d+\.\d+\.\d+\.\d+)\s+(?P<mask>\d+\.\d+\.\d+\.\d+)", re.IGNORECASE)
_HOSTNAME_RE = re.compile(r"^hostname\s+(?P<name>\S+)", re.IGNORECASE)
_IP_HTTP_SERVER_RE = re.compile(r"^ip\s+http\s+server\s*$", re.IGNORECASE | re.MULTILINE)
_TYPE7_PASSWORD_RE = re.compile(r"^\s*password\s+7\s+\S+", re.IGNORECASE | re.MULTILINE)


class CiscoIOSParser(BaseParser):
    vendor = "cisco_ios"

    @classmethod
    def detect(cls, raw_text: str, filename: str) -> bool:
        if re.search(r"^access-list\s+\d+\s+(permit|deny)", raw_text, re.IGNORECASE | re.MULTILINE):
            return True
        # Router/switch configs with no ACLs at all still need parsing (interfaces, routes,
        # weak mgmt settings) - detect via classic IOS-only markers instead.
        has_iface = re.search(r"^interface\s+\S+", raw_text, re.IGNORECASE | re.MULTILINE)
        has_ios_marker = re.search(r"^(boot-start-marker|service password-encryption|line vty)", raw_text, re.IGNORECASE | re.MULTILINE)
        return bool(has_iface and has_ios_marker)

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
                        id=f"acl{m.group('num')}-{position}",
                        position=position,
                        name=f"ACL-{m.group('num')}",
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

        if _IP_HTTP_SERVER_RE.search(raw_text):
            position = len(rules) + 1
            rules.append(
                Rule(
                    id="mgmt-http",
                    position=position,
                    name="HTTP-Management-Access",
                    action=RuleAction.ALLOW,
                    source=["any"],
                    destination=["device"],
                    services=["http"],
                    logging_enabled=False,
                    description="Unencrypted HTTP web management (ip http server) is enabled.",
                )
            )
        if _TYPE7_PASSWORD_RE.search(raw_text):
            position = len(rules) + 1
            rules.append(
                Rule(
                    id="weak-type7-password",
                    position=position,
                    name="Type-7-Password",
                    action=RuleAction.ALLOW,
                    source=["any"],
                    destination=["device"],
                    services=["type7-password"],
                    logging_enabled=False,
                    description="A line/enable password uses reversible Cisco Type 7 encryption.",
                )
            )

        device = Device(
            name=hostname,
            vendor=self.vendor,
            device_type="router",
            interfaces=interfaces,
            rules=rules,
            raw_source=raw_text,
        )
        return NetworkModel(devices=[device])


def _flush_iface(data: dict) -> Interface:
    return Interface(name=data.get("name", "unknown"), zone=None, ip_address=data.get("ip"), subnet_mask=data.get("mask"))
