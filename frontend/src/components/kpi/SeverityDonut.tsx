import { Cell, Pie, PieChart, Tooltip } from "recharts";
import { SEVERITY_COLOR, SEVERITY_ORDER, Severity } from "../../lib/theme";

export default function SeverityDonut({ counts }: { counts: Record<Severity, number> }) {
  const total = SEVERITY_ORDER.reduce((sum, sev) => sum + (counts[sev] ?? 0), 0);
  const data = SEVERITY_ORDER.map((sev) => ({ name: sev, value: counts[sev] ?? 0 }));

  return (
    <div className="card p-5">
      <p className="text-sm text-rulescope-muted mb-1">Findings by Severity</p>
      <div className="flex items-center gap-4">
        <PieChart width={140} height={140}>
          <Pie data={data} dataKey="value" nameKey="name" innerRadius={40} outerRadius={65} paddingAngle={2}>
            {data.map((entry) => (
              <Cell key={entry.name} fill={SEVERITY_COLOR[entry.name as Severity]} stroke="none" />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ background: "#1b1f29", border: "1px solid #2c3244", borderRadius: 8, color: "#f5f7fa" }}
          />
        </PieChart>
        <div className="space-y-1 text-sm">
          {data.map((entry) => (
            <div key={entry.name} className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: SEVERITY_COLOR[entry.name as Severity] }} />
              <span className="capitalize text-rulescope-muted w-16">{entry.name}</span>
              <span className="font-semibold">{entry.value}</span>
            </div>
          ))}
        </div>
      </div>
      <p className="text-xs text-rulescope-muted mt-2">{total} total findings</p>
    </div>
  );
}
