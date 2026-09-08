from dataclasses import dataclass


@dataclass
class FindingResult:
    severity: str  # critical|high|medium|low|info
    category: str
    rule_ref: str
    device_name: str
    description: str
    remediation: str
