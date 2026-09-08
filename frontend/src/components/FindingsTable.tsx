import { useState } from "react";
import { Finding } from "../lib/api";
import SeverityBadge from "./SeverityBadge";
import { SEVERITY_COLOR, Severity } from "../lib/theme";

const SEVERITIES: Finding["severity"][] = ["critical", "high", "medium", "low", "info"];

export default function FindingsTable({ findings }: { findings: Finding[] }) {
  const [filter, setFilter] = useState<string>("all");
  const visible = filter === "all" ? findings : findings.filter((f) => f.severity === filter);

  return (
    <div className="card">
      <div className="flex gap-2 p-4 border-b border-rulescope-border flex-wrap items-center">
        <button
          className={`rounded-full px-3 py-1 text-xs font-semibold ${
            filter === "all" ? "bg-rulescope-orange text-white" : "bg-rulescope-surfaceAlt text-rulescope-muted"
          }`}
          onClick={() => setFilter("all")}
        >
          All ({findings.length})
        </button>
        {SEVERITIES.map((sev) => (
          <button
            key={sev}
            onClick={() => setFilter(sev)}
            className={filter === sev ? "ring-2 ring-white/60 rounded-full" : "opacity-70 hover:opacity-100"}
          >
            <SeverityBadge severity={sev} count={findings.filter((f) => f.severity === sev).length} />
          </button>
        ))}
      </div>
      <table className="w-full text-sm">
        <thead className="text-left text-rulescope-muted">
          <tr>
            <th className="p-3">Severity</th>
            <th className="p-3">Category</th>
            <th className="p-3">Device</th>
            <th className="p-3">Rule</th>
            <th className="p-3">Description</th>
            <th className="p-3">Remediation</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-rulescope-border">
          {visible.map((f) => (
            <tr key={f.id} style={{ borderLeft: `3px solid ${SEVERITY_COLOR[f.severity as Severity]}` }}>
              <td className="p-3">
                <SeverityBadge severity={f.severity} />
              </td>
              <td className="p-3">{f.category}</td>
              <td className="p-3">{f.device_name}</td>
              <td className="p-3 font-mono text-xs">{f.rule_ref}</td>
              <td className="p-3 max-w-sm">{f.description}</td>
              <td className="p-3 max-w-sm text-rulescope-muted">{f.remediation}</td>
            </tr>
          ))}
          {visible.length === 0 && (
            <tr>
              <td colSpan={6} className="p-4 text-center text-rulescope-muted">
                No findings for this filter.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
