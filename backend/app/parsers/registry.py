from __future__ import annotations

from app.models.network import NetworkModel
from app.parsers.base import BaseParser
from app.parsers.cisco_asa import CiscoASAParser
from app.parsers.cisco_ios import CiscoIOSParser
from app.parsers.extreme_exos import ExtremeXOSParser
from app.parsers.fortigate import FortiGateParser
from app.parsers.generic_csv import GenericCsvParser
from app.parsers.juniper import JuniperParser
from app.parsers.juniper_switch import JuniperSwitchParser
from app.parsers.nipper_report import NipperReportParser
from app.parsers.paloalto import PaloAltoParser

# Order matters: more specific detectors first, generic_csv/heuristic last.
PARSERS: list[type[BaseParser]] = [
    NipperReportParser,
    CiscoASAParser,
    CiscoIOSParser,
    PaloAltoParser,
    FortiGateParser,
    JuniperParser,
    JuniperSwitchParser,
    ExtremeXOSParser,
    GenericCsvParser,
]


class UnsupportedFormatError(Exception):
    pass


def detect_vendor(raw_text: str, filename: str) -> type[BaseParser]:
    for parser_cls in PARSERS:
        if parser_cls.detect(raw_text, filename):
            return parser_cls
    raise UnsupportedFormatError(
        "Could not detect a supported vendor format. Use the generic CSV template "
        "(columns: name, action, source, destination, service) as a fallback."
    )


def parse_export(raw_text: str, filename: str) -> tuple[str, NetworkModel]:
    parser_cls = detect_vendor(raw_text, filename)
    parser = parser_cls()
    model = parser.parse(raw_text, filename)
    return parser_cls.vendor, model
