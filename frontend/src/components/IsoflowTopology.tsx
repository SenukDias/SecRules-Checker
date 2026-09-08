import { useMemo, useState } from "react";
import { Isoflow } from "isoflow";
import type { Model } from "isoflow";
import { TopologyGraph as TopologyData, TopologyNode } from "../lib/api";
import { SEVERITY_COLOR, SEVERITY_ORDER, Severity, zoneColor } from "../lib/theme";
import NodeDetailPanel from "./NodeDetailPanel";

const LEAF_SPACING = 2;
const LEVEL_HEIGHT = 3;

const ICON_BY_KIND: Record<string, string> = {
  router: "network-router",
  switch: "network-switch",
  firewall: "network-firewall",
  interface: "network-access-point",
  subnet: "network-switch",
  public_ip: "network-internet",
};

const NETWORK_ICON_BASE = "https://isoflow-pub-data.s3.eu-west-2.amazonaws.com/editor/assets/networkMapIcons/previews";
const NETWORK_MAP_ICONS = [
  { id: "network-firewall", name: "Firewall", url: `${NETWORK_ICON_BASE}/firewall.png` },
  { id: "network-router", name: "Router", url: `${NETWORK_ICON_BASE}/router.png` },
  { id: "network-switch", name: "Switch", url: `${NETWORK_ICON_BASE}/switch.png` },
  { id: "network-internet", name: "Internet", url: `${NETWORK_ICON_BASE}/internet.png` },
  { id: "network-access-point", name: "Access point", url: `${NETWORK_ICON_BASE}/access-point.png` },
  { id: "network-ptp-dish", name: "Point-to-point dish", url: `${NETWORK_ICON_BASE}/ptp-dish.png` },
  { id: "network-comms-tower", name: "Communications tower", url: `${NETWORK_ICON_BASE}/comms-tower.png` },
];

const CANVAS_ICONS = NETWORK_MAP_ICONS;
const ICON_URL_BY_ID = new Map(CANVAS_ICONS.map((icon) => [icon.id, icon.url]));

const TYPE_LABEL: Record<TopologyNode["type"], string> = {
  device: "Device",
  interface: "Interface",
  subnet: "Subnet",
  public_ip: "Public IP",
};

function iconIdFor(node: TopologyNode): string {
  if (node.type === "device") {
    return ICON_BY_KIND[node.device_type ?? ""] ?? "network-router";
  }
  return ICON_BY_KIND[node.type] ?? "network-router";
}

function clusterKeyFor(node: TopologyNode): string {
  if (node.type === "device") return "core";
  if (node.type === "public_ip") return "external";
  return (node.zone ?? "unzoned").toLowerCase();
}

/** Same dendrogram layout used by the ReactFlow topology view, scaled to Isoflow's small grid-tile units. */
function layoutTiles(data: TopologyData): Map<string, { x: number; y: number }> {
  const childrenOf = new Map<string, string[]>();
  const hasParent = new Set<string>();
  data.edges.forEach((e) => {
    if (!childrenOf.has(e.source)) childrenOf.set(e.source, []);
    childrenOf.get(e.source)!.push(e.target);
    hasParent.add(e.target);
  });

  const nodeById = new Map(data.nodes.map((n) => [n.id, n]));
  const roots = data.nodes.filter((n) => !hasParent.has(n.id)).map((n) => n.id);

  const positions = new Map<string, { x: number; y: number }>();
  let nextLeafSlot = 0;
  const visited = new Set<string>();

  function place(nodeId: string, depth: number): number {
    if (visited.has(nodeId)) return positions.get(nodeId)?.x ?? 0;
    visited.add(nodeId);
    const children = (childrenOf.get(nodeId) ?? []).filter((c) => nodeById.has(c));
    let x: number;
    if (children.length === 0) {
      x = nextLeafSlot * LEAF_SPACING;
      nextLeafSlot += 1;
    } else {
      const childXs = children.map((c) => place(c, depth + 1));
      x = childXs.reduce((sum, v) => sum + v, 0) / childXs.length;
    }
    positions.set(nodeId, { x: Math.round(x), y: depth * LEVEL_HEIGHT });
    return x;
  }

  roots.forEach((rootId) => place(rootId, 0));
  data.nodes.forEach((n) => {
    if (!visited.has(n.id)) place(n.id, 0);
  });

  return positions;
}

function buildModel(data: TopologyData): Model {
  const tiles = layoutTiles(data);

  const colors = SEVERITY_ORDER.map((sev) => ({ id: `sev-${sev}`, value: SEVERITY_COLOR[sev] }));

  const clusters = new Map<string, TopologyNode[]>();
  data.nodes.forEach((n) => {
    const key = clusterKeyFor(n);
    if (!clusters.has(key)) clusters.set(key, []);
    clusters.get(key)!.push(n);
  });
  const zoneColorIds = new Map<string, string>();
  clusters.forEach((_, key) => {
    const id = `zone-${key}`;
    zoneColorIds.set(key, id);
    colors.push({ id, value: zoneColor(key) });
  });

  const rectangles = [...clusters.entries()].map(([key, members]) => {
    const tilePositions = members.map((m) => tiles.get(m.id)!);
    const minX = Math.min(...tilePositions.map((t) => t.x)) - 1;
    const maxX = Math.max(...tilePositions.map((t) => t.x)) + 1;
    const minY = Math.min(...tilePositions.map((t) => t.y)) - 1;
    const maxY = Math.max(...tilePositions.map((t) => t.y)) + 1;
    return {
      id: `rect-${key}`,
      color: zoneColorIds.get(key)!,
      from: { x: minX, y: minY },
      to: { x: maxX, y: maxY },
    };
  });

  const items = data.nodes.map((n) => ({
    id: n.id,
    name: "",
    icon: iconIdFor(n),
  }));

  const viewItems = data.nodes.map((n) => ({ id: n.id, tile: tiles.get(n.id)!, labelHeight: 0 }));

  const connectors = data.edges.map((e, i) => {
    const severity: Severity = (e.severity as Severity) ?? "info";
    return {
      id: `conn-${i}`,
      color: `sev-${severity}`,
      width: severity === "critical" ? 3 : 2,
      style: (severity === "critical" || severity === "high" ? "DASHED" : "SOLID") as "DASHED" | "SOLID",
      anchors: [{ id: `${e.source}-a`, ref: { item: e.source } }, { id: `${e.target}-a`, ref: { item: e.target } }],
    };
  });

  return {
    title: "RuleScope Topology",
    items,
    icons: CANVAS_ICONS,
    colors,
    views: [
      {
        id: "main",
        name: "Topology",
        items: viewItems,
        rectangles,
        connectors,
      },
    ],
  };
}

export default function IsoflowTopology({ data }: { data: TopologyData }) {
  const [selected, setSelected] = useState<TopologyNode | null>(null);
  const model = useMemo(() => buildModel(data), [data]);
  const nodeById = useMemo(() => new Map(data.nodes.map((n) => [n.id, n])), [data]);
  const selectedIconUrl = selected ? ICON_URL_BY_ID.get(iconIdFor(selected)) : undefined;

  return (
    <div className="h-[720px] card relative overflow-hidden">
      <Isoflow
        initialData={{ ...model, fitToView: true, view: "main" }}
        editorMode="EXPLORABLE_READONLY"
        onModelUpdated={() => {}}
        width="100%"
        height="100%"
      />
      <div className="absolute left-4 top-4 z-10 w-[min(360px,calc(100%-2rem))] rounded-xl border border-rulescope-border bg-rulescope-surface/95 p-3 shadow-2xl backdrop-blur">
        <div className="mb-2 flex items-center justify-between gap-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-rulescope-muted">Components</p>
          <p className="text-[10px] text-rulescope-muted">{data.nodes.length} items</p>
        </div>
        <div className="grid gap-1.5 max-h-[300px] overflow-y-auto pr-1">
          {data.nodes.map((n) => {
            const iconId = iconIdFor(n);
            const iconUrl = ICON_URL_BY_ID.get(iconId);
            const isSelected = selected?.id === n.id;
            const severity = n.severity ?? "info";

            return (
              <button
                key={n.id}
                onClick={() => setSelected(nodeById.get(n.id) ?? null)}
                aria-label={`Preview ${n.label}`}
                className={`group flex min-w-0 items-center gap-2 rounded-lg border px-2 py-1.5 text-left transition ${
                  isSelected ? "border-rulescope-orange" : "border-rulescope-border hover:border-rulescope-green"
                }`}
              >
                <span className="relative grid h-9 w-9 shrink-0 place-items-center rounded-md bg-rulescope-bg/70">
                  {iconUrl && <img src={iconUrl} alt="" className="h-7 w-7 object-contain drop-shadow-[0_8px_8px_rgba(0,0,0,0.45)]" />}
                  <span
                    className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full border border-rulescope-bg"
                    style={{ background: SEVERITY_COLOR[severity] }}
                  />
                </span>
                <span className="min-w-0">
                  <span className="block truncate text-xs font-semibold text-rulescope-white">{n.label}</span>
                  <span className="block truncate text-[10px] uppercase tracking-wide text-rulescope-muted">
                    {TYPE_LABEL[n.type]}
                    {n.zone ? ` / ${n.zone}` : ""}
                  </span>
                </span>
              </button>
            );
          })}
        </div>
      </div>
      <NodeDetailPanel node={selected} iconUrl={selectedIconUrl} onClose={() => setSelected(null)} />
    </div>
  );
}
