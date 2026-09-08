import { zoneColor } from "../../lib/theme";

export interface ZoneClusterData {
  label: string;
  radius: number;
}

export default function ZoneClusterNode({ data }: { data: ZoneClusterData }) {
  const color = zoneColor(data.label === "core" || data.label === "external" ? null : data.label);
  const size = data.radius * 2;

  return (
    <div
      className="pointer-events-none flex items-start justify-start"
      style={{
        width: size,
        height: size,
        borderRadius: "9999px",
        border: `1.5px dashed ${color}55`,
        background: `radial-gradient(circle, ${color}0d 0%, transparent 70%)`,
      }}
    >
      <span
        className="text-[11px] uppercase tracking-wide font-semibold px-2 py-0.5 rounded-full -translate-x-2 -translate-y-2"
        style={{ color, background: "#12151ccc", border: `1px solid ${color}55` }}
      >
        {data.label}
      </span>
    </div>
  );
}
