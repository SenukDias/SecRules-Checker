import axios from "axios";
import { keycloak } from "./auth";
import { Severity } from "./theme";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
});

api.interceptors.request.use((config) => {
  if (keycloak.token) {
    config.headers.Authorization = `Bearer ${keycloak.token}`;
  }
  return config;
});

export interface JobSummary {
  id: string;
  filename: string;
  vendor: string;
  status: string;
  error?: string | null;
  created_at: string;
}

export interface Finding {
  id: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  category: string;
  rule_ref: string;
  device_name: string;
  description: string;
  remediation: string;
}

export interface TopologyNode {
  id: string;
  type: "device" | "interface" | "subnet" | "public_ip";
  label: string;
  severity?: Severity;
  zone?: string | null;
  vendor?: string;
  device_type?: string;
  ip_address?: string | null;
  subnet_mask?: string | null;
  isp?: string | null;
  asn?: string | null;
  country?: string | null;
  confidence?: string | null;
}

export interface TopologyGraph {
  nodes: TopologyNode[];
  edges: Array<{ source: string; target: string; severity?: Severity }>;
}

export interface StatsSummary {
  total_jobs: number;
  jobs_by_status: Record<string, number>;
  severity_counts: Record<Severity, number>;
  total_findings: number;
  risk_score: number;
  trend: Array<{ date: string; jobs: number }>;
}

export interface CustomRule {
  id: string;
  name: string;
  severity: string;
  category: string;
  condition: Record<string, unknown>;
  description_template: string;
  remediation: string;
  enabled: boolean;
  created_by: string;
}

export type CustomRuleInput = Omit<CustomRule, "id" | "created_by">;

export const adminApi = {
  listCustomRules: () => api.get<CustomRule[]>("/admin/custom-rules").then((r) => r.data),
  createCustomRule: (rule: CustomRuleInput) => api.post<CustomRule>("/admin/custom-rules", rule).then((r) => r.data),
  deleteCustomRule: (id: string) => api.delete(`/admin/custom-rules/${id}`),
};

export const statsApi = {
  summary: () => api.get<StatsSummary>("/stats/summary").then((r) => r.data),
};

export const jobsApi = {
  list: () => api.get<JobSummary[]>("/jobs").then((r) => r.data),
  get: (id: string) => api.get<JobSummary>(`/jobs/${id}`).then((r) => r.data),
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/jobs", form, { headers: { "Content-Type": "multipart/form-data" } }).then((r) => r.data);
  },
  findings: (id: string) => api.get<Finding[]>(`/jobs/${id}/findings`).then((r) => r.data),
  topology: (id: string) => api.get<TopologyGraph>(`/jobs/${id}/topology`).then((r) => r.data),
  exportReport: (id: string, format: "pdf" | "html" | "xlsx", topologyImageBase64?: string) =>
    api
      .post(
        `/jobs/${id}/report`,
        { format, topology_image_base64: topologyImageBase64 },
        { responseType: "blob" }
      )
      .then((r) => r.data as Blob),
};
