import { Cable, Cloud, Layers, Network, Router, ShieldAlert, ShieldCheck } from "lucide-react";
import { Handle, Position } from "reactflow";
import { Severity, SEVERITY_COLOR, SEVERITY_GLOW, zoneColor } from "../../lib/theme";
import { TopologyNode } from "../../lib/api";

export interface IsoNodeData extends TopologyNode {
  onSelect?: (node: TopologyNode) => void;
}

function iconFor(data: IsoNodeData, severity: Severity) {
  if (data.type === "device") {
    if (data.device_type === "switch") return Network;
    if (data.device_type === "router") return Router;
    return severity === "critical" || severity === "high" ? ShieldAlert : ShieldCheck;
  }
  if (data.type === "public_ip") return Cloud;
  if (data.type === "subnet") return Layers;
  return Cable; // interface
}

export default function IsoNode({ data }: { data: IsoNodeData }) {
  const severity: Severity = data.severity ?? "info";
  const isDevice = data.type === "device";
  const color = isDevice ? SEVERITY_COLOR[severity] : zoneColor(data.zone);
  const glow = isDevice ? SEVERITY_GLOW[severity] : `${color}40`;
  const Icon = iconFor(data, severity);
  const count = data.finding_count ?? 0;

  const subLabel =
    data.type === "public_ip"
      ? data.isp || "Unknown ISP"
      : data.type === "device"
        ? data.vendor
        : data.ip_address || undefined;

  return (
    <div
      className="group relative flex flex-col items-center justify-center cursor-pointer transition-transform hover:scale-110"
      style={{ width: 72, height: 72 }}
      onClick={() => data.onSelect?.(data)}
    >
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />

      {/* Isometric diamond platform */}
      <div
        className="absolute rounded-lg"
        style={{
          width: 44,
          height: 44,
          transform: "rotate(45deg)",
          background: "linear-gradient(145deg, #232838, #12151c)",
          border: `2px solid ${color}`,
          boxShadow: `0 6px 14px ${glow}, inset 0 0 10px ${glow}`,
        }}
      />
      <Icon size={isDevice ? 24 : 18} color={color} strokeWidth={2} className="relative z-10" />

      {isDevice && count > 0 && (
        <span
          className="absolute -top-1 -right-1 z-20 rounded-full text-[10px] font-bold text-white flex items-center justify-center"
          style={{ width: 18, height: 18, background: color, boxShadow: `0 0 6px ${glow}` }}
        >
          {count}
        </span>
      )}

      <span className="absolute top-full mt-1 whitespace-nowrap text-[10px] font-semibold text-rulescope-white bg-rulescope-bg/85 px-1.5 py-0.5 rounded">
        {data.label}
      </span>
      {subLabel && (
        <span className="absolute top-full mt-5 whitespace-nowrap text-[9px] text-rulescope-muted">{subLabel}</span>
      )}

      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </div>
  );
}
