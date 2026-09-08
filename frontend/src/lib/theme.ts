export type Severity = "critical" | "high" | "medium" | "low" | "info";

export const SEVERITY_COLOR: Record<Severity, string> = {
  critical: "#ef4444",
  high: "#e8620c",
  medium: "#d4a017",
  low: "#1f9d55",
  info: "#64748b",
};

export const SEVERITY_GLOW: Record<Severity, string> = {
  critical: "rgba(239, 68, 68, 0.55)",
  high: "rgba(232, 98, 12, 0.55)",
  medium: "rgba(212, 160, 23, 0.5)",
  low: "rgba(31, 157, 85, 0.5)",
  info: "rgba(100, 116, 139, 0.35)",
};

export const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low", "info"];

export const ZONE_COLOR: Record<string, string> = {
  outside: "#ef4444",
  untrust: "#ef4444",
  dmz: "#e8620c",
  mgmt: "#d4a017",
  inside: "#1f9d55",
  trust: "#1f9d55",
};

// Distinct hues for arbitrary zones/VLANs that aren't one of the well-known keywords above.
const PALETTE = [
  "#3ecf7e",
  "#38bdf8",
  "#a78bfa",
  "#f472b6",
  "#facc15",
  "#fb923c",
  "#2dd4bf",
  "#818cf8",
  "#4ade80",
  "#f87171",
];

function hashString(value: string): number {
  let hash = 0;
  for (let i = 0; i < value.length; i++) {
    hash = (hash * 31 + value.charCodeAt(i)) >>> 0;
  }
  return hash;
}

export function zoneColor(zone: string | null | undefined): string {
  if (!zone) return "#8b93a7";
  const known = ZONE_COLOR[zone.toLowerCase()];
  if (known) return known;
  return PALETTE[hashString(zone.toLowerCase()) % PALETTE.length];
}
