"""Multi-source IP/ISP enrichment with cross-checking for redundancy.

Only the extracted public IP addresses are sent to these external services -
never the uploaded configuration content.
"""
from __future__ import annotations

import asyncio
from collections import Counter
from typing import Any

import httpx

from app.config import get_settings

settings = get_settings()


async def _lookup_ip_api(client: httpx.AsyncClient, ip: str) -> dict[str, Any] | None:
    if not settings.ipapi_enabled:
        return None
    try:
        resp = await client.get(f"http://ip-api.com/json/{ip}", params={"fields": "status,isp,as,country,query"}, timeout=5)
        data = resp.json()
        if data.get("status") != "success":
            return None
        return {"isp": data.get("isp"), "asn": data.get("as"), "country": data.get("country"), "source": "ip-api.com"}
    except (httpx.HTTPError, ValueError):
        return None


async def _lookup_ipwhois(client: httpx.AsyncClient, ip: str) -> dict[str, Any] | None:
    if not settings.ipwhois_enabled:
        return None
    try:
        resp = await client.get(f"https://ipwho.is/{ip}", timeout=5)
        data = resp.json()
        if not data.get("success", True) and "success" in data:
            return None
        connection = data.get("connection", {}) or {}
        return {
            "isp": connection.get("isp") or connection.get("org"),
            "asn": f"AS{connection.get('asn')}" if connection.get("asn") else None,
            "country": data.get("country"),
            "source": "ipwho.is",
        }
    except (httpx.HTTPError, ValueError):
        return None


async def _lookup_freeipapi(client: httpx.AsyncClient, ip: str) -> dict[str, Any] | None:
    if not settings.freeipapi_enabled:
        return None
    try:
        resp = await client.get(f"https://freeipapi.com/api/json/{ip}", timeout=5)
        data = resp.json()
        return {
            "isp": data.get("isp") or data.get("asnOrganization"),
            "asn": data.get("asn"),
            "country": data.get("countryName"),
            "source": "freeipapi.com",
        }
    except (httpx.HTTPError, ValueError):
        return None


def _merge_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    results = [r for r in results if r]
    if not results:
        return {"isp": None, "asn": None, "country": None, "confidence": "unknown", "sources": []}

    def majority(field: str) -> Any:
        values = [r[field] for r in results if r.get(field)]
        if not values:
            return None
        return Counter(values).most_common(1)[0][0]

    isp = majority("isp")
    asn = majority("asn")
    country = majority("country")
    agreement = sum(1 for r in results if r.get("isp") == isp) if isp else 0
    confidence = "high" if agreement >= 2 else "medium" if agreement == 1 else "low"

    return {
        "isp": isp,
        "asn": asn,
        "country": country,
        "confidence": confidence,
        "sources": [r["source"] for r in results],
    }


async def enrich_ips(ips: set[str], cache: dict[str, dict] | None = None) -> dict[str, dict]:
    """Look up each public IP across multiple free providers and cross-check results."""
    cache = cache if cache is not None else {}
    to_fetch = [ip for ip in ips if ip not in cache]

    async with httpx.AsyncClient() as client:
        for ip in to_fetch:
            provider_results = await asyncio.gather(
                _lookup_ip_api(client, ip),
                _lookup_ipwhois(client, ip),
                _lookup_freeipapi(client, ip),
            )
            cache[ip] = _merge_results(list(provider_results))

    return {ip: cache[ip] for ip in ips}
