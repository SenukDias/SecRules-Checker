"""Admin-defined custom checks, evaluated with a small declarative condition DSL.

Condition schema (JSON): {"field": "services"|"source"|"destination"|"action",
                           "op": "contains_any"|"contains_all"|"equals",
                           "value": <str or list[str]>}
"""
from __future__ import annotations

from app.analysis.models import FindingResult
from app.models.db_models import CustomRule
from app.models.network import Device, NetworkModel, Rule


def _rule_field(rule: Rule, field: str) -> list[str]:
    if field == "services":
        return [s.lower() for s in rule.services]
    if field == "source":
        return [s.lower() for s in rule.source]
    if field == "destination":
        return [s.lower() for s in rule.destination]
    if field == "action":
        return [rule.action.value]
    return []


def _matches(rule: Rule, condition: dict) -> bool:
    field = condition.get("field")
    op = condition.get("op", "contains_any")
    value = condition.get("value", [])
    values = [v.lower() for v in (value if isinstance(value, list) else [value])]
    actual = _rule_field(rule, field)

    if op == "contains_any":
        return any(v in actual for v in values)
    if op == "contains_all":
        return all(v in actual for v in values)
    if op == "equals":
        return actual == values
    return False


def run_custom_checks(model: NetworkModel, custom_rules: list[CustomRule]) -> list[FindingResult]:
    findings: list[FindingResult] = []
    active_rules = [cr for cr in custom_rules if cr.enabled]
    if not active_rules:
        return findings

    for device in model.devices:
        for rule in device.rules:
            if rule.disabled:
                continue
            for custom in active_rules:
                if _matches(rule, custom.condition):
                    findings.append(
                        FindingResult(
                            severity=custom.severity,
                            category=custom.category,
                            rule_ref=rule.name or rule.id,
                            device_name=device.name,
                            description=custom.description_template.format(rule_name=rule.name, device=device.name),
                            remediation=custom.remediation,
                        )
                    )
    return findings
