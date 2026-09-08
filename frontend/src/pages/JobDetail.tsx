import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Finding, JobSummary, TopologyGraph as TopologyData, jobsApi } from "../lib/api";
import IsoflowTopology from "../components/IsoflowTopology";
import FindingsTable from "../components/FindingsTable";

type Tab = "topology" | "findings";

export default function JobDetail() {
  const { jobId } = useParams<{ jobId: string }>();
  const [job, setJob] = useState<JobSummary | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [topology, setTopology] = useState<TopologyData | null>(null);
  const [tab, setTab] = useState<Tab>("topology");
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    if (!jobId) return;
    const load = () => jobsApi.get(jobId).then(setJob);
    load();
    const interval = setInterval(load, 3000);
    return () => clearInterval(interval);
  }, [jobId]);

  useEffect(() => {
    if (!jobId || job?.status !== "done") return;
    jobsApi.findings(jobId).then(setFindings);
    jobsApi.topology(jobId).then(setTopology);
  }, [jobId, job?.status]);

  async function handleExport(format: "pdf" | "html" | "xlsx") {
    if (!jobId) return;
    setExporting(true);
    try {
      const blob = await jobsApi.exportReport(jobId, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `rulescope-report.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  }

  if (!job) return <p className="text-rulescope-muted">Loading...</p>;

  if (job.status !== "done") {
    return (
      <div className="card p-6">
        <h2 className="text-lg font-semibold">{job.filename}</h2>
        <p className="text-rulescope-muted mt-2">
          Status: <span className="text-rulescope-orange font-semibold">{job.status}</span>
        </p>
        {job.error && <p className="text-red-500 mt-2">{job.error}</p>}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">{job.filename}</h2>
          <p className="text-sm text-rulescope-muted">Vendor: {job.vendor}</p>
        </div>
        <div className="flex gap-2">
          <button className="btn-primary" disabled={exporting} onClick={() => handleExport("pdf")}>
            Export PDF
          </button>
          <button className="btn-secondary" disabled={exporting} onClick={() => handleExport("html")}>
            HTML
          </button>
          <button className="btn-secondary" disabled={exporting} onClick={() => handleExport("xlsx")}>
            Excel
          </button>
        </div>
      </div>

      <div className="flex gap-2 border-b border-rulescope-border">
        {(["topology", "findings"] as Tab[]).map((t) => (
          <button
            key={t}
            className={`px-4 py-2 capitalize ${
              tab === t ? "border-b-2 border-rulescope-orange text-rulescope-orange" : "text-rulescope-muted"
            }`}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "topology" && topology && <IsoflowTopology data={topology} />}
      {tab === "findings" && <FindingsTable findings={findings} />}
    </div>
  );
}
