import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { JobSummary, jobsApi } from "../lib/api";

const STATUS_COLORS: Record<string, string> = {
  pending: "text-rulescope-muted",
  parsing: "text-yellow-400",
  analyzing: "text-yellow-400",
  done: "text-rulescope-green",
  failed: "text-red-500",
};

export default function Dashboard() {
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  const refresh = () => jobsApi.list().then(setJobs).catch(() => setError("Failed to load jobs"));

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

  return (
    <div className="space-y-8">
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
              <span className={`text-sm font-semibold ${STATUS_COLORS[job.status] ?? ""}`}>{job.status}</span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
