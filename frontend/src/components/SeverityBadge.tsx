import { AlertOctagon, AlertTriangle, CircleAlert, Info, ShieldAlert } from "lucide-react";
import { Severity, SEVERITY_COLOR, SEVERITY_GLOW } from "../lib/theme";

const SEVERITY_ICON: Record<Severity, typeof AlertOctagon> = {
  critical: ShieldAlert,
  high: AlertOctagon,
  medium: AlertTriangle,
  low: CircleAlert,
  info: Info,
};

export default function SeverityBadge({ severity, count }: { severity: Severity; count?: number }) {
  const color = SEVERITY_COLOR[severity];
  const glow = SEVERITY_GLOW[severity];
  const Icon = SEVERITY_ICON[severity];

  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold capitalize"
      style={{ color, background: `${color}1a`, border: `1px solid ${color}66`, boxShadow: `0 0 8px ${glow}` }}
    >
      <Icon size={13} />
      {severity}
      {count !== undefined && <span className="opacity-70">({count})</span>}
    </span>
  );
}
