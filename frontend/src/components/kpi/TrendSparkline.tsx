import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis } from "recharts";

export default function TrendSparkline({ trend }: { trend: Array<{ date: string; jobs: number }> }) {
  const totalJobs = trend.reduce((sum, t) => sum + t.jobs, 0);

  return (
    <div className="card p-5">
      <div className="flex items-baseline justify-between mb-1">
        <p className="text-sm text-rulescope-muted">Scans (last 14 days)</p>
        <span className="text-2xl font-bold text-rulescope-orange">{totalJobs}</span>
      </div>
      <ResponsiveContainer width="100%" height={100}>
        <AreaChart data={trend}>
          <defs>
            <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#e8620c" stopOpacity={0.6} />
              <stop offset="100%" stopColor="#e8620c" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="date" hide />
          <Tooltip
            contentStyle={{ background: "#1b1f29", border: "1px solid #2c3244", borderRadius: 8, color: "#f5f7fa" }}
            labelFormatter={(label) => {
              const date = new Date(String(label));
              return Number.isNaN(date.getTime()) ? "" : date.toLocaleDateString();
            }}
          />
          <Area type="monotone" dataKey="jobs" stroke="#e8620c" fill="url(#trendGradient)" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
