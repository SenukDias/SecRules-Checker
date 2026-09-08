"""Shared ACL address/service tokenizer for Cisco ASA and IOS parsers.

Cisco ACL address specs are: `any` | `any4` | `any6` | `host <ip>` |
`<ip> <wildcard-mask>` | `object <name>` | `object-group <name>`. A naive
single regex can't reliably disambiguate two consecutive address specs
(e.g. `host 10.0.0.20 host 8.8.8.8`), so this tokenizes word-by-word instead.
"""
from __future__ import annotations

_ANY_KEYWORDS = {"any", "any4", "any6"}
_REF_KEYWORDS = {"object", "object-group"}


def _looks_like_ip(token: str) -> bool:
    parts = token.split(".")
    return len(parts) == 4 and all(p.isdigit() for p in parts)


def consume_address(tokens: list[str], i: int) -> tuple[str, int]:
    """Consume one address spec starting at tokens[i]; return (normalized, next_index)."""
    token = tokens[i]
    if token.lower() in _ANY_KEYWORDS:
        return "any", i + 1
    if token.lower() == "host" and i + 1 < len(tokens):
        return tokens[i + 1], i + 2
    if token.lower() in _REF_KEYWORDS and i + 1 < len(tokens):
        return tokens[i + 1], i + 2
    if _looks_like_ip(token) and i + 1 < len(tokens) and _looks_like_ip(tokens[i + 1]):
        return f"{token}/{tokens[i + 1]}", i + 2
    return token, i + 1


def parse_acl_tokens(tokens: list[str]) -> dict:
    """tokens = words after 'permit'/'deny', e.g. ['tcp','any','host','10.0.0.5','eq','3389','log']."""
    proto = tokens[0] if tokens else "ip"
    idx = 1
    source, idx = consume_address(tokens, idx)
    destination, idx = consume_address(tokens, idx)

    port = None
    log = False
    while idx < len(tokens):
        word = tokens[idx].lower()
        if word in ("eq", "gt", "lt", "neq") and idx + 1 < len(tokens):
            port = tokens[idx + 1]
            idx += 2
            continue
        if word == "range" and idx + 2 < len(tokens):
            port = f"{tokens[idx + 1]}-{tokens[idx + 2]}"
            idx += 3
            continue
        if word == "log":
            log = True
        idx += 1

    service = f"{proto}/{port}" if port else proto
    return {"source": source, "destination": destination, "service": service, "log": log}
