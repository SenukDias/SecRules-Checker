from __future__ import annotations

import re

from app.models.network import Device, Interface, NetworkModel, Rule, RuleAction
from app.parsers._cisco_common import consume_address, parse_acl_tokens
from app.parsers.base import BaseParser

_ACL_RE = re.compile(
    r"^access-list\s+(?P<acl>\S+)\s+extended\s+(?P<action>permit|deny)\s+(?P<rest>.+)$",
    re.IGNORECASE,
)
_IFACE_RE = re.compile(r"^interface\s+(?P<name>\S+)", re.IGNORECASE)
_NAMEIF_RE = re.compile(r"^\s*nameif\s+(?P<zone>\S+)", re.IGNORECASE)
_IPADDR_RE = re.compile(r"^\s*ip address\s+(?P<ip>\d+\.\d+\.\d+\.\d+)\s+(?P<mask>\d+\.\d+\.\d+\.\d+)", re.IGNORECASE)
_HOSTNAME_RE = re.compile(r"^hostname\s+(?P<name>\S+)", re.IGNORECASE)
_ACL_REMARK_RE = re.compile(r"^access-list\s+(?P<acl>\S+)\s+remark(?:\s+(?P<text>.*))?$", re.IGNORECASE)
_OBJECT_RE = re.compile(r"^object\s+network\s+(?P<name>\S+)$", re.IGNORECASE)
_GROUP_RE = re.compile(r"^object-group\s+(?P<kind>network|service)\s+(?P<name>\S+)(?:\s+(?P<protocol>\S+))?$", re.IGNORECASE)


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
        network_objects, network_groups, service_groups = _parse_objects(lines)
        remarks: dict[str, str] = {}

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

            stripped = line.strip()
            if m := _ACL_REMARK_RE.match(stripped):
                remarks[m.group("acl")] = m.group("text") or ""
                continue
            if m := _ACL_RE.match(stripped):
                position = len(rules) + 1
                tokens = m.group("rest").split()
                parsed = parse_acl_tokens(tokens)
                parsed["source"] = _expand_network(parsed["source"], network_objects, network_groups)
                parsed["destination"] = _expand_network(parsed["destination"], network_objects, network_groups)
                parsed["services"] = _acl_services(tokens, service_groups, parsed["service"])
                parsed["services"] = [_normalize_service(service) for service in parsed["services"]]
                rule_name = m.group("acl")
                rules.append(
                    Rule(
                        id=f"{rule_name}-{position}",
                        position=position,
                        name=rule_name,
                        action=RuleAction.ALLOW if m.group("action").lower() == "permit" else RuleAction.DENY,
                        source=parsed["source"],
                        destination=parsed["destination"],
                        services=parsed["services"],
                        logging_enabled=parsed["log"],
                        disabled=bool(re.search(r"\binactive\s*$", stripped, re.IGNORECASE)),
                        description=remarks.pop(rule_name, ""),
                        raw=stripped,
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


def _parse_objects(lines: list[str]) -> tuple[dict[str, list[str]], dict[str, list[str]], dict[str, list[str]]]:
    network_objects: dict[str, list[str]] = {}
    network_groups: dict[str, list[str]] = {}
    service_groups: dict[str, list[str]] = {}
    current_object: str | None = None
    current_group: str | None = None
    current_group_kind: str | None = None
    group_protocol: str | None = None

    for line in lines:
        stripped = line.strip()
        if match := _OBJECT_RE.match(stripped):
            current_object = match.group("name")
            current_group = current_group_kind = None
            network_objects.setdefault(current_object, [])
            continue
        if match := _GROUP_RE.match(stripped):
            current_object = None
            current_group = match.group("name")
            current_group_kind = match.group("kind").lower()
            group_protocol = (match.group("protocol") or "ip").lower()
            target = network_groups if current_group_kind == "network" else service_groups
            target.setdefault(current_group, [])
            continue
        if stripped.startswith(("object ", "object-group ")) or stripped in {"!", ""}:
            current_object = current_group = current_group_kind = None
            continue

        if current_object:
            values = _network_object_values(stripped)
            network_objects[current_object].extend(values)
        elif current_group and current_group_kind == "network":
            if stripped.startswith("network-object "):
                network_groups[current_group].extend(_network_object_values(stripped[len("network-object "):]))
            elif stripped.startswith("group-object "):
                network_groups[current_group].append(f"group:{stripped.split()[-1]}")
        elif current_group and current_group_kind == "service":
            service = _service_group_line(stripped, group_protocol or "ip")
            if service:
                service_groups[current_group].extend(service)

    return network_objects, network_groups, service_groups


def _network_object_values(spec: str) -> list[str]:
    tokens = spec.split()
    if not tokens:
        return []
    kind = tokens[0].lower()
    if kind == "host" and len(tokens) > 1:
        return [tokens[1]]
    if kind == "subnet" and len(tokens) > 2:
        return [f"{tokens[1]}/{tokens[2]}"]
    if kind == "range" and len(tokens) > 2:
        return [f"{tokens[1]}-{tokens[2]}"]
    if kind == "fqdn" and len(tokens) > 1:
        return [tokens[-1]]
    if kind == "object" and len(tokens) > 1:
        return [f"object:{tokens[1]}"]
    if len(tokens) >= 2 and re.fullmatch(r"\d+(?:\.\d+){3}", tokens[0]):
        return [f"{tokens[0]}/{tokens[1]}"]
    return []


def _expand_network(
    value: str,
    network_objects: dict[str, list[str]],
    network_groups: dict[str, list[str]],
    seen: frozenset[str] = frozenset(),
) -> list[str]:
    key = value.split(":", 1)[1] if value.startswith(("object:", "group:")) else value
    if key in seen:
        return []
    if value.startswith("object:") or key in network_objects:
        values = network_objects.get(key, [value])
        return [item for entry in values for item in _expand_network(entry, network_objects, network_groups, seen | {key})]
    if value.startswith("group:") or key in network_groups:
        values = network_groups.get(key, [value])
        return [item for entry in values for item in _expand_network(entry, network_objects, network_groups, seen | {key})]
    return [value]


def _service_group_line(line: str, protocol: str) -> list[str]:
    tokens = line.split()
    if not tokens:
        return []
    if tokens[0].lower() == "port-object":
        parsed = parse_acl_tokens([protocol, "any", "any", *tokens[1:]])
        return [parsed["service"]] if parsed["service"] != protocol else []
    if tokens[0].lower() == "group-object" and len(tokens) > 1:
        return [f"group:{tokens[1]}"]
    if tokens[0].lower() == "service-object":
        service_protocol = tokens[1].lower() if len(tokens) > 1 and tokens[1].lower() in {"tcp", "udp", "icmp", "ip"} else protocol
        parsed = parse_acl_tokens([service_protocol, "any", "any", *tokens[2:]])
        return [parsed["service"]]
    return []


def _acl_services(tokens: list[str], service_groups: dict[str, list[str]], fallback: str) -> list[str]:
    _, index = consume_address(tokens, 1)
    _, index = consume_address(tokens, index)
    while index < len(tokens):
        if tokens[index].lower() == "object-group" and index + 1 < len(tokens):
            group_name = tokens[index + 1]
            if group_name in service_groups:
                return _expand_service_group(group_name, service_groups)
        index += 1
    return [fallback]


def _expand_service_group(name: str, groups: dict[str, list[str]], seen: frozenset[str] = frozenset()) -> list[str]:
    if name in seen:
        return []
    return [
        service
        for value in groups.get(name, [])
        for service in (_expand_service_group(value[6:], groups, seen | {name}) if value.startswith("group:") else [value])
    ]


def _normalize_service(service: str) -> str:
    protocol, separator, port = service.partition("/")
    aliases = {
        "domain": "53",
        "ftp": "21",
        "https": "443",
        "ntp": "123",
        "smtp": "25",
        "ssh": "22",
        "syslog": "514",
        "telnet": "23",
        "www": "80",
    }
    normalized_port = aliases.get(port.lower(), port) if separator else ""
    return f"{protocol}/{normalized_port}" if separator else service


def _flush_iface(data: dict) -> Interface:
    return Interface(
        name=data.get("name", "unknown"),
        zone=data.get("zone"),
        ip_address=data.get("ip"),
        subnet_mask=data.get("mask"),
        is_wan=(data.get("zone") == "outside"),
    )
