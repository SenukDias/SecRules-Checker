import { useMemo, useState } from "react";
import { Background, Controls, Edge, MiniMap, Node, ReactFlow } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { TopologyGraph as TopologyData, TopologyNode } from "../lib/api";
import IsoNode from "./nodes/IsoNode";
import GradientEdge from "./edges/GradientEdge";
import SeverityLegend from "./SeverityLegend";
import NodeDetailPanel from "./NodeDetailPanel";
import { Severity, SEVERITY_COLOR } from "../lib/theme";

const NODE_TYPES = { iso: IsoNode };
const EDGE_TYPES = { gradient: GradientEdge };

const LEAF_SPACING = 130;
const LEVEL_HEIGHT = 170;

/**
 * Real branching tree layout: edges from the backend already point parent -> child
 * (device -> interface/public_ip, interface -> subnet), so we lay this out top-to-bottom
 * as a dendrogram - each parent's children fan out beneath it - instead of a single
 * top-to-bottom list. External/WAN devices have no parent so they become extra roots
 * and are placed alongside the core device(s).
 */
function layout(data: TopologyData, onSelect: (n: TopologyNode) => void): { nodes: Node[]; edges: Edge[] } {
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
    positions.set(nodeId, { x, y: depth * LEVEL_HEIGHT });
    return x;
  }

  roots.forEach((rootId) => place(rootId, 0));
  // Any node not reachable from a root (shouldn't normally happen) still gets placed.
  data.nodes.forEach((n) => {
    if (!visited.has(n.id)) place(n.id, 0);
  });

  const nodes: Node[] = data.nodes.map((n) => toFlowNode(n, positions.get(n.id)!.x, positions.get(n.id)!.y, onSelect));

  const edges: Edge[] = data.edges.map((e, i) => ({
    id: `e-${i}`,
    source: e.source,
    target: e.target,
    type: "gradient",
    data: { severity: e.severity ?? "info" },
  }));

  return { nodes, edges };
}

function toFlowNode(n: TopologyNode, x: number, y: number, onSelect: (n: TopologyNode) => void): Node {
  return {
    id: n.id,
    type: "iso",
    position: { x, y },
    data: { ...n, onSelect },
    draggable: true,
    zIndex: 1,
  };
}

export default function TopologyGraph({ data }: { data: TopologyData }) {
  const [selected, setSelected] = useState<TopologyNode | null>(null);
  const { nodes, edges } = useMemo(() => layout(data, setSelected), [data]);

  return (
    <div className="h-[720px] card relative overflow-hidden">
      <SeverityLegend />
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={NODE_TYPES}
        edgeTypes={EDGE_TYPES}
        fitView
        proOptions={{ hideAttribution: true }}
        minZoom={0.15}
        maxZoom={2.5}
        panOnScroll
        zoomOnScroll
        zoomOnPinch
        panOnDrag
        zoomActivationKeyCode={null}
      >
        <Background color="#2c3244" gap={28} />
        <Controls />
        <MiniMap
          pannable
          zoomable
          maskColor="rgba(18, 21, 28, 0.75)"
          style={{ background: "#1b1f29", border: "1px solid #2c3244" }}
          nodeColor={(n) => (n.type === "iso" ? SEVERITY_COLOR[(n.data?.severity as Severity) ?? "info"] : "#2c324400")}
          nodeStrokeWidth={0}
        />
      </ReactFlow>
      <NodeDetailPanel node={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
