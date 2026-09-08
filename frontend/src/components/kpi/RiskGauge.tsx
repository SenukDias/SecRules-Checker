import { RadialBar, RadialBarChart, PolarAngleAxis } from "recharts";

function scoreColor(score: number): string {
  if (score >= 80) return "#1f9d55";
  if (score >= 50) return "#e8620c";
  return "#ef4444";
}

export default function RiskGauge({ score }: { score: number }) {
  const color = scoreColor(score);
  const data = [{ name: "risk", value: score, fill: color }];

  return (
    <div className="card p-5 flex flex-col items-center">
      <p className="text-sm text-rulescope-muted self-start mb-1">Risk Score</p>
      <div className="relative w-full h-40">
        <RadialBarChart
          width={200}
          height={160}
          cx="50%"
          cy="70%"
          innerRadius={70}
          outerRadius={100}
          barSize={14}
          data={data}
          startAngle={180}
          endAngle={0}
          className="mx-auto"
        >
          <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
          <RadialBar background={{ fill: "#232838" }} dataKey="value" cornerRadius={8} />
        </RadialBarChart>
        <div className="absolute inset-x-0 bottom-4 text-center">
          <span className="text-3xl font-bold" style={{ color }}>
            {score}
          </span>
          <span className="text-rulescope-muted text-sm">/100</span>
        </div>
      </div>
      <p className="text-xs text-rulescope-muted">Higher is healthier</p>
    </div>
  );
}
