from __future__ import annotations

import re

from app.models.network import Device, Interface, NetworkModel, Rule, RuleAction
from app.parsers.base import BaseParser

_HOSTNAME_RE = re.compile(r"^set\s+system\s+host-name\s+(?P<name>\S+)", re.IGNORECASE)
_VLAN_ID_RE = re.compile(r"^set\s+vlans\s+(?P<vlan>\S+)\s+vlan-id\s+(?P<id>\d+)", re.IGNORECASE)
_VLAN_L3_RE = re.compile(r"^set\s+vlans\s+(?P<vlan>\S+)\s+l3-interface\s+irb\.(?P<unit>\d+)", re.IGNORECASE)
_IRB_ADDR_RE = re.compile(
    r"^set\s+interfaces\s+irb\s+unit\s+(?P<unit>\d+)\s+family\s+inet\s+address\s+(?P<ip>[\d.]+)/(?P<mask>\d+)",
    re.IGNORECASE,
)
_SSH_ROOT_LOGIN_RE = re.compile(r"^set\s+system\s+services\s+ssh\s+root-login\s+allow\s*$", re.IGNORECASE)
_HTTP_MGMT_RE = re.compile(r"^set\s+system\s+services\s+web-management\s+http\s+", re.IGNORECASE)
_SNMP_COMMUNITY_RE = re.compile(r"^set\s+snmp\s+community\s+", re.IGNORECASE)


def _cidr_to_mask(prefix_len: str) -> str:
    bits = int(prefix_len)
    mask = (0xFFFFFFFF << (32 - bits)) & 0xFFFFFFFF if bits else 0
    return ".".join(str((mask >> shift) & 0xFF) for shift in (24, 16, 8, 0))


class JuniperSwitchParser(BaseParser):
    """Juniper EX-series switching config (VLANs/irb, no SRX 'security policies' block)."""

    vendor = "juniper_switch"

    @classmethod
    def detect(cls, raw_text: str, filename: str) -> bool:
        if re.search(r"^set\s+security\s+policies\s+from-zone", raw_text, re.IGNORECASE | re.MULTILINE):
            return False  # that's the SRX firewall parser's job
        return bool(re.search(r'^set\s+vlans\s+\S+\s+vlan-id\s+\d+', raw_text, re.IGNORECASE | re.MULTILINE)) and (
            "family ethernet-switching" in raw_text.lower() or "virtual-chassis" in raw_text.lower()
        )

    def parse(self, raw_text: str, filename: str) -> NetworkModel:
        hostname = filename
        vlan_tags: dict[str, str] = {}
        vlan_l3_unit: dict[str, str] = {}
        irb_addr: dict[str, tuple[str, str]] = {}
        ssh_root_login = False
        http_mgmt = False
        snmp_v1v2c = False

        for raw_line in raw_text.splitlines():
            line = raw_line.strip()
            if m := _HOSTNAME_RE.match(line):
                hostname = m.group("name")
                continue
            if m := _VLAN_ID_RE.match(line):
                vlan_tags[m.group("vlan")] = m.group("id")
                continue
            if m := _VLAN_L3_RE.match(line):
                vlan_l3_unit[m.group("vlan")] = m.group("unit")
                continue
            if m := _IRB_ADDR_RE.match(line):
                irb_addr[m.group("unit")] = (m.group("ip"), _cidr_to_mask(m.group("mask")))
                continue
            if _SSH_ROOT_LOGIN_RE.match(line):
                ssh_root_login = True
                continue
            if _HTTP_MGMT_RE.match(line):
                http_mgmt = True
                continue
            if _SNMP_COMMUNITY_RE.match(line):
                snmp_v1v2c = True
                continue

        interfaces: list[Interface] = []
        for vlan_name, tag in vlan_tags.items():
            unit = vlan_l3_unit.get(vlan_name)
            ip, mask = irb_addr.get(unit, (None, None)) if unit else (None, None)
            interfaces.append(Interface(name=f"vlan-{tag}", zone=vlan_name, ip_address=ip, subnet_mask=mask))

        rules: list[Rule] = []
        if ssh_root_login:
            rules.append(
                Rule(
                    id="mgmt-ssh-root-login",
                    position=len(rules) + 1,
                    name="SSH-Root-Login",
                    action=RuleAction.ALLOW,
                    source=["any"],
                    destination=["device"],
                    services=["ssh-root-login"],
                    logging_enabled=False,
                    description="SSH root login is explicitly allowed.",
                )
            )
        if http_mgmt:
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
        if snmp_v1v2c:
            rules.append(
                Rule(
                    id="mgmt-snmp-community",
                    position=len(rules) + 1,
                    name="SNMP-Community-Access",
                    action=RuleAction.ALLOW,
                    source=["any"],
                    destination=["device"],
                    services=["snmp"],
                    logging_enabled=False,
                    description="SNMP community-string (v1/v2c) access is configured.",
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
