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

export function zoneColor(zone: string | null | undefined): string {
  if (!zone) return "#8b93a7";
  return ZONE_COLOR[zone.toLowerCase()] ?? "#3ecf7e";
}
