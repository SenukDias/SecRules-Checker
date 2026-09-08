"""Built-in best-practice checks - always evaluated regardless of documented business justification."""
from __future__ import annotations

from app.analysis.models import FindingResult
from app.models.network import Device, NetworkModel, Rule, RuleAction

INSECURE_SERVICES = {
    "telnet": "Telnet (unencrypted management/remote access)",
    "tcp/23": "Telnet (unencrypted management/remote access)",
    "ftp": "FTP (unencrypted file transfer)",
    "tcp/21": "FTP (unencrypted file transfer)",
    "tcp/20": "FTP data (unencrypted file transfer)",
    "tftp": "TFTP (unauthenticated file transfer)",
    "udp/69": "TFTP (unauthenticated file transfer)",
    "http": "HTTP (unencrypted web management/traffic)",
    "tcp/80": "HTTP (unencrypted web management/traffic)",
    "snmp": "SNMP (check for v1/v2c community strings)",
    "udp/161": "SNMP (check for v1/v2c community strings)",
    "rsh": "RSH (unauthenticated remote shell)",
}

SENSITIVE_MGMT_PORTS = {
    "tcp/3389": "RDP",
    "tcp/22": "SSH",
    "tcp/23": "Telnet",
    "tcp/443": "HTTPS mgmt",
    "tcp/8443": "HTTPS mgmt",
}

ANY_TOKENS = {"any", "any4", "any6", "0.0.0.0/0", "all"}
# "ip" (bare protocol, no port) is how Cisco ACLs express "all protocols/ports".
ANY_SERVICE_TOKENS = ANY_TOKENS | {"ip"}


def _is_any(tokens: list[str]) -> bool:
    return any(t.lower() in ANY_TOKENS for t in tokens)


def _is_any_service(tokens: list[str]) -> bool:
    return any(t.lower() in ANY_SERVICE_TOKENS for t in tokens)


def check_any_any_allow(device: Device, rule: Rule) -> FindingResult | None:
    if rule.action != RuleAction.ALLOW or rule.disabled:
        return None
    if _is_any(rule.source) and _is_any(rule.destination) and _is_any_service(rule.services):
        return FindingResult(
            severity="critical",
            category="Overly Permissive Rule",
            rule_ref=rule.name or rule.id,
            device_name=device.name,
            description=f"Rule '{rule.name}' allows ANY source to ANY destination on ANY service.",
            remediation="Restrict source, destination, and service to the minimum required scope.",
        )
    return None


def check_insecure_protocol(device: Device, rule: Rule) -> list[FindingResult]:
    if rule.action != RuleAction.ALLOW or rule.disabled:
        return []
    findings = []
    for svc in rule.services:
        key = svc.lower()
        if key in INSECURE_SERVICES:
            findings.append(
                FindingResult(
                    severity="high",
                    category="Insecure Protocol",
                    rule_ref=rule.name or rule.id,
                    device_name=device.name,
                    description=f"Rule '{rule.name}' permits {INSECURE_SERVICES[key]} ({svc}).",
                    remediation="Replace with an encrypted/authenticated alternative (e.g. SSH, SFTP, HTTPS, SNMPv3) or remove the rule.",
                )
            )
    return findings


def check_no_logging(device: Device, rule: Rule) -> FindingResult | None:
    if rule.action != RuleAction.ALLOW or rule.disabled or rule.logging_enabled:
        return None
    return FindingResult(
        severity="low",
        category="Missing Logging",
        rule_ref=rule.name or rule.id,
        device_name=device.name,
        description=f"Allow rule '{rule.name}' does not have logging enabled.",
        remediation="Enable logging on allow rules to support audit trails and incident investigation.",
    )


def check_unused_rule(device: Device, rule: Rule) -> FindingResult | None:
    if rule.disabled or rule.hitcount is None or rule.hitcount > 0:
        return None
    return FindingResult(
        severity="info",
        category="Unused Rule",
        rule_ref=rule.name or rule.id,
        device_name=device.name,
        description=f"Rule '{rule.name}' has a zero hit count and appears unused.",
        remediation="Review and remove unused rules to reduce attack surface and simplify auditing.",
    )


def check_internet_exposed_mgmt(device: Device, rule: Rule) -> list[FindingResult]:
    if rule.action != RuleAction.ALLOW or rule.disabled:
        return []
    if not _is_any(rule.source):
        return []
    findings = []
    for svc in rule.services:
        if svc.lower() in SENSITIVE_MGMT_PORTS:
            findings.append(
                FindingResult(
                    severity="critical",
                    category="Internet-Exposed Management",
                    rule_ref=rule.name or rule.id,
                    device_name=device.name,
                    description=(
                        f"Rule '{rule.name}' exposes {SENSITIVE_MGMT_PORTS[svc.lower()]} "
                        "management/remote-access service to ANY source (internet-facing)."
                    ),
                    remediation="Restrict management access to specific trusted source IPs/VPN, never ANY.",
                )
            )
    return findings


def check_shadowed_rule(device: Device, rules_seen: list[Rule], rule: Rule) -> FindingResult | None:
    """Simplified shadowing check: an earlier broader ALLOW/DENY rule fully covers this later rule."""
    for earlier in rules_seen:
        if earlier.disabled or earlier.action != rule.action:
            continue
        broader_src = _is_any(earlier.source) or set(rule.source).issubset(set(earlier.source))
        broader_dst = _is_any(earlier.destination) or set(rule.destination).issubset(set(earlier.destination))
        broader_svc = _is_any_service(earlier.services) or set(rule.services).issubset(set(earlier.services))
        if broader_src and broader_dst and broader_svc:
            return FindingResult(
                severity="medium",
                category="Shadowed Rule",
                rule_ref=rule.name or rule.id,
                device_name=device.name,
                description=(
                    f"Rule '{rule.name}' (position {rule.position}) is shadowed by earlier rule "
                    f"'{earlier.name}' (position {earlier.position}) and will never be evaluated."
                ),
                remediation="Remove or reorder the shadowed rule so its intended traffic is actually matched.",
            )
    return None


def check_redundant_rules(device: Device, rules: list[Rule]) -> list[FindingResult]:
    seen: dict[tuple, Rule] = {}
    findings = []
    for rule in rules:
        if rule.disabled:
            continue
        sig = (rule.action, tuple(sorted(rule.source)), tuple(sorted(rule.destination)), tuple(sorted(rule.services)))
        if sig in seen:
            findings.append(
                FindingResult(
                    severity="low",
                    category="Redundant Rule",
                    rule_ref=rule.name or rule.id,
                    device_name=device.name,
                    description=f"Rule '{rule.name}' duplicates rule '{seen[sig].name}' (identical source/destination/service/action).",
                    remediation="Remove duplicate rules to simplify the rule base and reduce audit overhead.",
                )
            )
        else:
            seen[sig] = rule
    return findings


def run_builtin_checks(model: NetworkModel) -> list[FindingResult]:
    findings: list[FindingResult] = []
    for device in model.devices:
        ordered_rules = sorted(device.rules, key=lambda r: r.position)
        seen_rules: list[Rule] = []
        for rule in ordered_rules:
            if f := check_any_any_allow(device, rule):
                findings.append(f)
            findings.extend(check_insecure_protocol(device, rule))
            if f := check_no_logging(device, rule):
                findings.append(f)
            if f := check_unused_rule(device, rule):
                findings.append(f)
            findings.extend(check_internet_exposed_mgmt(device, rule))
            # Only compare against earlier rules in the same ACL/policy - different
            # ACLs are typically bound to different interfaces/directions.
            same_acl_seen = [r for r in seen_rules if r.name == rule.name]
            if f := check_shadowed_rule(device, same_acl_seen, rule):
                findings.append(f)
            seen_rules.append(rule)
        findings.extend(check_redundant_rules(device, ordered_rules))
    return findings
