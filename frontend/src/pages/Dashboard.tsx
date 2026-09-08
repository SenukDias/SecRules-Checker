import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Trash2 } from "lucide-react";
import { JobSummary, jobsApi, StatsSummary, statsApi } from "../lib/api";
import RiskGauge from "../components/kpi/RiskGauge";
import SeverityDonut from "../components/kpi/SeverityDonut";
import TrendSparkline from "../components/kpi/TrendSparkline";
import ConfirmDialog from "../components/ConfirmDialog";

const STATUS_COLORS: Record<string, string> = {
  pending: "text-rulescope-muted",
  parsing: "text-yellow-400",
  analyzing: "text-yellow-400",
  done: "text-rulescope-green",
  failed: "text-red-500",
};

export default function Dashboard() {
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [stats, setStats] = useState<StatsSummary | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<JobSummary | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  const refresh = () => {
    jobsApi.list().then(setJobs).catch(() => setError("Failed to load jobs"));
    statsApi.summary().then(setStats).catch(() => {});
  };

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 4000);
    return () => clearInterval(interval);
  }, []);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    const file = fileInput.current?.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await jobsApi.upload(file);
      if (fileInput.current) fileInput.current.value = "";
      refresh();
    } catch {
      setError("Upload failed. Check file format/size and try again.");
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(e: React.MouseEvent, job: JobSummary) {
    e.preventDefault();
    e.stopPropagation();
    setPendingDelete(job);
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    await jobsApi.remove(pendingDelete.id);
    setPendingDelete(null);
    refresh();
  }

  return (
    <div className="space-y-8">
      {stats && (
        <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <RiskGauge score={stats.risk_score} />
          <SeverityDonut counts={stats.severity_counts} />
          <TrendSparkline trend={stats.trend} />
        </section>
      )}

      <section className="card p-6">
        <h2 className="text-lg font-semibold mb-1">Upload exported rule set</h2>
        <p className="text-sm text-rulescope-muted mb-4">
          Cisco ASA/IOS, Palo Alto, FortiGate, Juniper configs, or the generic CSV template.
        </p>
        <form onSubmit={handleUpload} className="flex items-center gap-3">
          <input
            ref={fileInput}
            type="file"
            required
            className="text-sm file:mr-4 file:rounded-lg file:border-0 file:bg-rulescope-surfaceAlt file:px-4 file:py-2 file:text-rulescope-white"
          />
          <button className="btn-primary" disabled={uploading} type="submit">
            {uploading ? "Uploading..." : "Analyze"}
          </button>
        </form>
        {error && <p className="text-red-500 text-sm mt-3">{error}</p>}
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">Jobs</h2>
        <div className="card divide-y divide-rulescope-border">
          {jobs.length === 0 && <p className="p-4 text-rulescope-muted text-sm">No uploads yet.</p>}
          {jobs.map((job) => (
            <Link
              key={job.id}
              to={`/jobs/${job.id}`}
              className="flex items-center justify-between px-4 py-3 hover:bg-rulescope-surfaceAlt transition-colors"
            >
              <div>
                <p className="font-medium">{job.filename}</p>
                <p className="text-xs text-rulescope-muted">
                  {job.vendor} &middot; {new Date(job.created_at).toLocaleString()}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span className={`text-sm font-semibold ${STATUS_COLORS[job.status] ?? ""}`}>{job.status}</span>
                <button
                  title="Remove scan"
                  onClick={(e) => handleDelete(e, job)}
                  className="text-rulescope-muted hover:text-red-500 transition-colors"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <ConfirmDialog
        open={pendingDelete !== null}
        title="Remove scan"
        message={`Remove scan "${pendingDelete?.filename}"? This cannot be undone.`}
        confirmLabel="Remove"
        danger
        onConfirm={confirmDelete}
        onCancel={() => setPendingDelete(null)}
      />
    </div>
  );
}
