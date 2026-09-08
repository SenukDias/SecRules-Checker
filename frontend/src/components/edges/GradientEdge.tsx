import { BaseEdge, EdgeProps, getStraightPath } from "reactflow";
import { Severity, SEVERITY_COLOR } from "../../lib/theme";

export default function GradientEdge({ id, sourceX, sourceY, targetX, targetY, data }: EdgeProps) {
  const [path] = getStraightPath({ sourceX, sourceY, targetX, targetY });
  const severity: Severity = (data?.severity as Severity) ?? "info";
  const color = SEVERITY_COLOR[severity];
  const gradientId = `edge-gradient-${id}`;
  const animated = severity === "critical" || severity === "high";

  return (
    <>
      <defs>
        <linearGradient id={gradientId} x1={sourceX} y1={sourceY} x2={targetX} y2={targetY} gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor={color} stopOpacity={0.15} />
          <stop offset="100%" stopColor={color} stopOpacity={0.9} />
        </linearGradient>
      </defs>
      <BaseEdge
        id={id}
        path={path}
        style={{
          stroke: `url(#${gradientId})`,
          strokeWidth: severity === "critical" ? 2.5 : 1.5,
          strokeDasharray: animated ? "6 4" : undefined,
          animation: animated ? "dash-flow 1.2s linear infinite" : undefined,
        }}
      />
    </>
  );
}
