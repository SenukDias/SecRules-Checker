import { Globe, HardDrive, Layers, Router } from "lucide-react";
import { Handle, Position } from "@xyflow/react";
import { Severity, SEVERITY_COLOR, SEVERITY_GLOW } from "../../lib/theme";
import { TopologyNode } from "../../lib/api";

const ICONS: Record<string, typeof Router> = {
  device: Router,
  interface: HardDrive,
  subnet: Layers,
  public_ip: Globe,
};

export interface HexNodeData extends TopologyNode {
  onSelect?: (node: TopologyNode) => void;
}

export default function HexNode({ data }: { data: HexNodeData }) {
  const severity: Severity = data.severity ?? "info";
  const color = SEVERITY_COLOR[severity];
  const glow = SEVERITY_GLOW[severity];
  const Icon = ICONS[data.type] ?? Router;

  return (
    <div
      className="group relative flex flex-col items-center justify-center cursor-pointer transition-transform hover:scale-110"
      style={{ width: 64, height: 64 }}
      onClick={() => data.onSelect?.(data)}
    >
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      <div
        className="flex items-center justify-center"
        style={{
          width: 56,
          height: 56,
          clipPath: "polygon(25% 5%, 75% 5%, 100% 50%, 75% 95%, 25% 95%, 0% 50%)",
          background: "linear-gradient(145deg, #1b1f29, #12151c)",
          border: `2px solid ${color}`,
          boxShadow: `0 0 14px ${glow}, inset 0 0 8px ${glow}`,
        }}
      >
        <Icon size={22} color={color} strokeWidth={2} />
      </div>
      <span className="absolute top-full mt-1 whitespace-nowrap text-[10px] font-medium text-rulescope-white bg-rulescope-bg/80 px-1.5 py-0.5 rounded">
        {data.label}
      </span>
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </div>
  );
}
