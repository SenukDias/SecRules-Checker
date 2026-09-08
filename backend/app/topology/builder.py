from __future__ import annotations

import ipaddress

import networkx as nx

from app.models.network import NetworkModel

SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


def build_topology(
    model: NetworkModel,
    ip_enrichment: dict[str, dict] | None = None,
    device_summary: dict[str, dict] | None = None,
) -> dict:
    """Build a nodes/edges graph describing devices, their interfaces/subnets, and public IPs.

    `device_summary` maps device name -> {"severity": str, "count": int} from findings.
    Returns a JSON-serializable dict consumable directly by the frontend graph component.
    """
    ip_enrichment = ip_enrichment or {}
    device_summary = device_summary or {}
    graph = nx.Graph()

    for device in model.devices:
        summary = device_summary.get(device.name, {})
        device_severity = summary.get("severity", "info")
        graph.add_node(
            f"device:{device.name}",
            type="device",
            label=device.name,
            vendor=device.vendor,
            device_type=device.device_type,
            severity=device_severity,
            finding_count=summary.get("count", 0),
            severity_breakdown=summary.get("by_severity", {}),
            interface_count=len(device.interfaces),
            rule_count=len(device.rules),
        )

        for iface in device.interfaces:
            iface_id = f"iface:{device.name}:{iface.name}"
            graph.add_node(
                iface_id,
                type="interface",
                label=iface.name,
                zone=iface.zone,
                ip_address=iface.ip_address,
                subnet_mask=iface.subnet_mask,
                is_wan=iface.is_wan,
                severity=device_severity,
            )
            graph.add_edge(f"device:{device.name}", iface_id, severity=device_severity)

            if iface.ip_address and iface.subnet_mask:
                try:
                    network = ipaddress.ip_network(f"{iface.ip_address}/{iface.subnet_mask}", strict=False)
                    subnet_id = f"subnet:{network}"
                    graph.add_node(subnet_id, type="subnet", label=str(network), zone=iface.zone, severity="info")
                    graph.add_edge(iface_id, subnet_id, severity="info")
                except ValueError:
                    pass

        for public_ip in _device_public_ips(model, device):
            ip_id = f"ip:{public_ip}"
            enrichment = ip_enrichment.get(public_ip, {})
            graph.add_node(
                ip_id,
                type="public_ip",
                label=public_ip,
                isp=enrichment.get("isp"),
                asn=enrichment.get("asn"),
                country=enrichment.get("country"),
                confidence=enrichment.get("confidence"),
                severity=device_severity,
            )
            graph.add_edge(f"device:{device.name}", ip_id, severity=device_severity)

    nodes = [{"id": n, **data} for n, data in graph.nodes(data=True)]
    edges = [{"source": u, "target": v, "severity": data.get("severity", "info")} for u, v, data in graph.edges(data=True)]
    return {"nodes": nodes, "edges": edges}


def _device_public_ips(model: NetworkModel, device) -> set[str]:
    ips = set()
    for rule in device.rules:
        for token in rule.source + rule.destination:
            ip = token.split("/")[0]
            try:
                addr = ipaddress.ip_address(ip)
            except ValueError:
                continue
            if not addr.is_private and not addr.is_loopback and not addr.is_link_local:
                ips.add(ip)
    return ips
