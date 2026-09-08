from __future__ import annotations

import re

from app.models.network import Device, Interface, NetworkModel, Rule, RuleAction
from app.parsers.base import BaseParser

_HOSTNAME_RE = re.compile(r'^configure\s+snmp\s+sysName\s+"(?P<name>[^"]+)"', re.IGNORECASE)
_VLAN_CREATE_RE = re.compile(r'^create\s+vlan\s+"(?P<name>[^"]+)"', re.IGNORECASE)
_VLAN_TAG_RE = re.compile(r'^configure\s+vlan\s+(?P<vlan>\S+)\s+tag\s+(?P<tag>\d+)', re.IGNORECASE)
_VLAN_DESC_RE = re.compile(r'^configure\s+vlan\s+(?P<vlan>\S+)\s+description\s+"(?P<desc>[^"]*)"', re.IGNORECASE)
_VLAN_IP_RE = re.compile(
    r'^configure\s+vlan\s+(?P<vlan>\S+)\s+ipaddress\s+(?P<ip>[\d.]+)\s+(?P<mask>[\d.]+)', re.IGNORECASE
)
_SNMP_V1V2C_RE = re.compile(r'^enable\s+snmp\s+access\s+snmp-v1v2c\s*$', re.IGNORECASE)
_HTTP_ENABLE_RE = re.compile(r'^enable\s+web\s+http\s*$', re.IGNORECASE)


class ExtremeXOSParser(BaseParser):
    """Extreme Networks switches (ExtremeXOS 'show configuration' export).

    Switches don't have traffic-filtering ACL rules the way firewalls/routers do, so
    this parser synthesizes lightweight "rules" from security-relevant management
    settings (SNMP community version, HTTP management) that the existing insecure-
    protocol checks already understand, plus interfaces/subnets per VLAN.
    """

    vendor = "extreme_exos"

    @classmethod
    def detect(cls, raw_text: str, filename: str) -> bool:
        return "ExtremeXOS" in raw_text or bool(
            re.search(r'^create\s+vlan\s+"', raw_text, re.IGNORECASE | re.MULTILINE)
        )

    def parse(self, raw_text: str, filename: str) -> NetworkModel:
        hostname = filename
        vlans: dict[str, dict] = {}
        vlan_order: list[str] = []
        snmp_v1v2c = False
        http_enabled = False

        for raw_line in raw_text.splitlines():
            line = raw_line.strip()
            if m := _HOSTNAME_RE.match(line):
                hostname = m.group("name")
                continue
            if m := _VLAN_CREATE_RE.match(line):
                name = m.group("name")
                if name not in vlans:
                    vlans[name] = {}
                    vlan_order.append(name)
                continue
            if m := _VLAN_TAG_RE.match(line):
                vlans.setdefault(m.group("vlan"), {})["tag"] = m.group("tag")
                continue
            if m := _VLAN_DESC_RE.match(line):
                vlans.setdefault(m.group("vlan"), {})["description"] = m.group("desc")
                continue
            if m := _VLAN_IP_RE.match(line):
                vlan = vlans.setdefault(m.group("vlan"), {})
                vlan["ip"] = m.group("ip")
                vlan["mask"] = m.group("mask")
                continue
            if _SNMP_V1V2C_RE.match(line):
                snmp_v1v2c = True
                continue
            if _HTTP_ENABLE_RE.match(line):
                http_enabled = True
                continue
            if re.match(r"^disable\s+web\s+http\s*$", line, re.IGNORECASE):
                http_enabled = False

        interfaces = [
            Interface(
                name=f"VLAN-{vlans[name].get('tag', '?')}" if vlans[name].get("tag") else name,
                zone=name,
                ip_address=vlans[name].get("ip"),
                subnet_mask=vlans[name].get("mask"),
            )
            for name in vlan_order
        ]

        rules: list[Rule] = []
        if snmp_v1v2c:
            rules.append(
                Rule(
                    id="mgmt-snmp-v1v2c",
                    position=len(rules) + 1,
                    name="SNMP-v1v2c-Access",
                    action=RuleAction.ALLOW,
                    source=["any"],
                    destination=["device"],
                    services=["snmp"],
                    logging_enabled=False,
                    description="SNMP access is enabled with v1/v2c (community-string) authentication.",
                )
            )
        if http_enabled:
            rules.append(
                Rule(
                    id="mgmt-http",
                    position=len(rules) + 1,
                    name="HTTP-Management-Access",
                    action=RuleAction.ALLOW,
                    source=["any"],
                    destination=["device"],
                    services=["http"],
                    logging_enabled=False,
                    description="Unencrypted HTTP web management is enabled.",
                )
            )

        device = Device(
            name=hostname,
            vendor=self.vendor,
            device_type="switch",
            interfaces=interfaces,
            rules=rules,
            raw_source=raw_text,
        )
        return NetworkModel(devices=[device])
