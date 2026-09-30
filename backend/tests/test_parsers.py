import unittest

from app.parsers.cisco_asa import CiscoASAParser
from app.parsers.nipper_report import NipperReportParser


class CiscoASAParserTests(unittest.TestCase):
    def test_expands_objects_service_groups_and_inactive_acl(self):
        config = """hostname ASA-TEST
object network admin-host
 host 192.0.2.10
object-group network admins
 network-object object admin-host
 network-object 192.0.2.16 255.255.255.240
object-group service management tcp
 port-object eq ssh
 port-object eq https
access-list inside remark Admin access
access-list inside extended permit tcp object-group admins host 10.0.0.5 object-group management
access-list inside extended permit ip any any inactive
access-list Local_LAN_Access standard permit host 192.0.2.20
"""
        rules = CiscoASAParser().parse(config, "asa.txt").devices[0].rules

        self.assertEqual(rules[0].source, ["192.0.2.10", "192.0.2.16/255.255.255.240"])
        self.assertEqual(rules[0].destination, ["10.0.0.5"])
        self.assertEqual(rules[0].services, ["tcp/22", "tcp/443"])
        self.assertEqual(rules[0].description, "Admin access")
        self.assertTrue(rules[1].disabled)
        self.assertEqual(rules[2].source, ["192.0.2.20"])
        self.assertEqual(rules[2].destination, ["any"])


class NipperReportParserTests(unittest.TestCase):
    def test_imports_finding_summary_and_recommendation(self):
        report = """<html><head><meta name="generator" content="Nipper from Titania"></head><body>
<table summary="Table 1: Findings summary table"><tbody>
<tr><th>Finding ID</th><th>Title</th><th>Risk</th><th>Section</th></tr>
<tr><td>NSA-FLTR-007</td><td>Rules Allow Administrative Access</td><td><font class="rate-crit">Critical</font></td><td><a href="#T325">2.3</a></td></tr>
</tbody></table>
<div class="reportsection"><div class="reportsectiontitlecritical"><a id="T325">2.3 Rules Allow Administrative Access</a></div>
<div class="reportsectionbody"><h3>2.3.1 Finding</h3><p>Administrative rules allow broad access.</p>
<h3>2.3.2 Impact</h3><p>Attackers may reach management services.</p>
<h3>2.3.4 Recommendation</h3><p>Restrict access to trusted hosts.</p></div></div>
</body></html>"""
        model = NipperReportParser().parse(report, "audit.html")

        self.assertEqual(model.devices[0].vendor, "nipper_report")
        self.assertEqual(len(model.imported_findings), 1)
        finding = model.imported_findings[0]
        self.assertEqual(finding.severity, "critical")
        self.assertEqual(finding.rule_ref, "NSA-FLTR-007 (2.3)")
        self.assertIn("Attackers may reach management services", finding.description)
        self.assertEqual(finding.remediation, "Restrict access to trusted hosts.")


if __name__ == "__main__":
    unittest.main()