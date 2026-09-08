import ReactFlow, { Background, Controls, Edge, MarkerType, Node } from "reactflow";
import "reactflow/dist/style.css";
import { TopologyGraph as TopologyData } from "../lib/api";

const TYPE_COLOR: Record<string, string> = {
  device: "#e8620c",
  interface: "#3ecf7e",
  subnet: "#8b93a7",
  public_ip: "#d32f2f",
};

function layout(data: TopologyData): { nodes: Node[]; edges: Edge[] } {
  const grouped: Record<string, string[]> = { device: [], interface: [], subnet: [], public_ip: [] };
  data.nodes.forEach((n) => grouped[n.type]?.push(n.id));

  const columns = ["public_ip", "device", "interface", "subnet"];
  const positioned: Record<string, { x: number; y: number }> = {};
  columns.forEach((col, colIdx) => {
    grouped[col].forEach((id, rowIdx) => {
      positioned[id] = { x: colIdx * 260, y: rowIdx * 110 };
    });
  });

  const nodes: Node[] = data.nodes.map((n) => ({
    id: n.id,
    position: positioned[n.id] ?? { x: 0, y: 0 },
    data: {
      label: (
        <div className="text-xs">
          <div className="font-semibold">{n.label as string}</div>
          {n.type === "public_ip" && (
            <div className="text-[10px] text-rulescope-muted">
              {(n.isp as string) || "Unknown ISP"} {n.country ? `(${n.country as string})` : ""}
            </div>
          )}
          {n.type === "interface" && n.ip_address ? (
            <div className="text-[10px] text-rulescope-muted">{n.ip_address as string}</div>
          ) : null}
        </div>
      ),
    },
    style: {
      background: "#1b1f29",
      color: "#f5f7fa",
      border: `2px solid ${TYPE_COLOR[n.type] ?? "#2c3244"}`,
      borderRadius: 10,
      padding: 8,
    },
  }));

  const edges: Edge[] = data.edges.map((e, i) => ({
    id: `e-${i}`,
    source: e.source,
    target: e.target,
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { stroke: "#2c3244" },
  }));

  return { nodes, edges };
}

export default function TopologyGraph({ data }: { data: TopologyData }) {
  const { nodes, edges } = layout(data);

  return (
    <div className="h-[520px] card">
      <ReactFlow nodes={nodes} edges={edges} fitView proOptions={{ hideAttribution: true }}>
        <Background color="#2c3244" gap={24} />
        <Controls />
      </ReactFlow>
    </div>
  );
}
