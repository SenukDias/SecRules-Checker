import unittest

from app.analysis.checks.builtin import run_builtin_checks
from app.models.network import Device, NetworkModel, Rule, RuleAction


class RuleFindingIdentityTests(unittest.TestCase):
    def test_acl_findings_identify_each_entry_and_ignore_cross_acl_redundancy(self):
        first = Rule(
            id="inside-1",
            position=1,
            name="inside",
            action=RuleAction.ALLOW,
            source=["10.0.0.1"],
            destination=["10.0.0.2"],
            services=["tcp/443"],
        )
        duplicate_in_same_acl = Rule(
            id="inside-2",
            position=2,
            name="inside",
            action=RuleAction.ALLOW,
            source=["10.0.0.1"],
            destination=["10.0.0.2"],
            services=["tcp/443"],
        )
        equivalent_other_acl = Rule(
            id="outside-3",
            position=3,
            name="outside",
            action=RuleAction.ALLOW,
            source=["10.0.0.1"],
            destination=["10.0.0.2"],
            services=["tcp/443"],
        )
        model = NetworkModel(devices=[Device(
            name="ASA",
            vendor="cisco_asa",
            device_type="firewall",
            rules=[first, duplicate_in_same_acl, equivalent_other_acl],
        )])

        findings = run_builtin_checks(model)
        missing_logging = [finding for finding in findings if finding.category == "Missing Logging"]
        redundant = [finding for finding in findings if finding.category == "Redundant Rule"]

        self.assertEqual([finding.rule_ref for finding in missing_logging], ["inside-1", "inside-2", "outside-3"])
        self.assertEqual(len({finding.description for finding in missing_logging}), 3)
        self.assertEqual([finding.rule_ref for finding in redundant], ["inside-2"])
        self.assertIn("position 1", redundant[0].description)
        self.assertIn("position 2", redundant[0].description)


if __name__ == "__main__":
    unittest.main()
