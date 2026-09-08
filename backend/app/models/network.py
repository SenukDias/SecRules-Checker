"""Vendor-agnostic normalized network model produced by every parser."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RuleAction(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass
class Rule:
    id: str
    position: int
    name: str | None
    action: RuleAction
    source: list[str]
    destination: list[str]
    services: list[str]  # e.g. "tcp/22", "any", "udp/53"
    zones: tuple[str | None, str | None] = (None, None)
    logging_enabled: bool = False
    disabled: bool = False
    hitcount: int | None = None
    description: str = ""
    raw: str = ""


@dataclass
class Interface:
    name: str
    zone: str | None
    ip_address: str | None
    subnet_mask: str | None
    is_wan: bool = False


@dataclass
class Subnet:
    cidr: str
    zone: str | None = None
    description: str = ""


@dataclass
class Device:
    name: str
    vendor: str
    device_type: str  # firewall | router | switch
    interfaces: list[Interface] = field(default_factory=list)
    subnets: list[Subnet] = field(default_factory=list)
    rules: list[Rule] = field(default_factory=list)
    raw_source: str = ""


@dataclass
class NetworkModel:
    """Result of parsing one uploaded export - typically a single device."""

    devices: list[Device] = field(default_factory=list)

    def all_rules(self) -> list[tuple[Device, Rule]]:
        return [(d, r) for d in self.devices for r in d.rules]

    def all_public_ips(self) -> set[str]:
        import ipaddress

        ips: set[str] = set()
        for device, rule in self.all_rules():
            for token in rule.source + rule.destination:
                ip = token.split("/")[0]
                try:
                    addr = ipaddress.ip_address(ip)
                except ValueError:
                    continue
                if not addr.is_private and not addr.is_loopback and not addr.is_link_local:
                    ips.add(ip)
        return ips
