import { SEVERITY_COLOR, SEVERITY_ORDER } from "../lib/theme";

export default function SeverityLegend() {
  return (
    <div className="absolute left-4 top-4 z-10 flex flex-col items-center gap-2 card px-2 py-3">
      <span className="text-[10px] text-rulescope-muted tracking-wide">HIGH</span>
      <div
        className="w-2 h-32 rounded-full"
        style={{ background: `linear-gradient(to bottom, ${SEVERITY_ORDER.map((s) => SEVERITY_COLOR[s]).join(",")})` }}
      />
      <span className="text-[10px] text-rulescope-muted tracking-wide">INFO</span>
    </div>
  );
}
