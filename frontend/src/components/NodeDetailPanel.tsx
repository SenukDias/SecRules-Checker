import { X } from "lucide-react";
import { TopologyNode } from "../lib/api";
import { SEVERITY_COLOR, SEVERITY_ORDER, Severity } from "../lib/theme";
import SeverityBadge from "./SeverityBadge";

const TYPE_LABEL: Record<string, string> = {
  device: "Firewall / Router / Switch",
  interface: "Network Interface / VLAN",
  subnet: "Subnet",
  public_ip: "Public IP",
};

export default function NodeDetailPanel({
  node,
  iconUrl,
  onClose,
}: {
  node: TopologyNode | null;
  iconUrl?: string;
  onClose: () => void;
}) {
  if (!node) return null;
  const severity: Severity = node.severity ?? "info";

  const rows: Array<[string, string | number | null | undefined]> = [
    ["Asset type", TYPE_LABEL[node.type] ?? node.type],
    ["Name", node.label],
    ["Zone / VLAN", node.zone],
    ["Vendor", node.vendor],
    ["Device type", node.device_type],
    ["IP address", node.ip_address],
    ["Subnet mask", node.subnet_mask],
    ["ISP", node.isp],
    ["ASN", node.asn],
    ["Country", node.country],
    ["Enrichment confidence", node.confidence],
    ["Interfaces / VLANs", node.interface_count],
    ["Rules parsed", node.rule_count],
    ["Total findings", node.finding_count],
  ];

  const breakdown = node.severity_breakdown ?? {};
  const hasBreakdown = SEVERITY_ORDER.some((s) => (breakdown[s] ?? 0) > 0);

  return (
    <div className="absolute right-0 top-0 bottom-0 w-80 z-20 card rounded-none rounded-l-xl border-r-0 p-5 overflow-y-auto shadow-2xl">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-lg">Information</h3>
        <button onClick={onClose} className="text-rulescope-muted hover:text-rulescope-white">
          <X size={18} />
        </button>
      </div>

      <div className="flex items-center gap-3 mb-4">
        {iconUrl && (
          <div className="grid h-14 w-14 shrink-0 place-items-center rounded-lg bg-rulescope-bg border border-rulescope-border shadow-inner">
            <img src={iconUrl} alt="" className="h-11 w-11 object-contain drop-shadow-[0_10px_10px_rgba(0,0,0,0.45)]" />
          </div>
        )}
        <div>
          <span className="badge" style={{ background: SEVERITY_COLOR[severity] }}>
            {severity.toUpperCase()}
          </span>
          <p className="mt-2 text-xs uppercase tracking-wide text-rulescope-muted">{TYPE_LABEL[node.type] ?? node.type}</p>
        </div>
      </div>

      {hasBreakdown && (
        <div className="mb-4">
          <p className="text-xs uppercase tracking-wide text-rulescope-muted mb-2">Vulnerability breakdown</p>
          <div className="flex flex-wrap gap-1.5">
            {SEVERITY_ORDER.filter((s) => (breakdown[s] ?? 0) > 0).map((s) => (
              <SeverityBadge key={s} severity={s} count={breakdown[s]} />
            ))}
          </div>
        </div>
      )}

      <dl className="space-y-2 text-sm">
        {rows
          .filter(([, value]) => value !== null && value !== undefined && value !== "")
          .map(([label, value]) => (
            <div key={label} className="flex justify-between gap-2 border-b border-rulescope-border pb-2">
              <dt className="text-rulescope-muted">{label}</dt>
              <dd className="text-right font-medium">{value}</dd>
            </div>
          ))}
      </dl>
    </div>
  );
}
