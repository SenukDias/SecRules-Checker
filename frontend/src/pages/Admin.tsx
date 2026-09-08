import { useEffect, useState } from "react";
import { CustomRule, CustomRuleInput, adminApi } from "../lib/api";

const EMPTY: CustomRuleInput = {
  name: "",
  severity: "medium",
  category: "custom",
  condition: { field: "services", op: "contains_any", value: [] },
  description_template: "Rule '{rule_name}' matched a custom check.",
  remediation: "",
  enabled: true,
};

export default function Admin() {
  const [rules, setRules] = useState<CustomRule[]>([]);
  const [form, setForm] = useState<CustomRuleInput>(EMPTY);
  const [conditionValue, setConditionValue] = useState("");

  const refresh = () => adminApi.listCustomRules().then(setRules);
  useEffect(() => {
    refresh();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    const values = conditionValue.split(",").map((v) => v.trim()).filter(Boolean);
    await adminApi.createCustomRule({ ...form, condition: { ...form.condition, value: values } });
    setForm(EMPTY);
    setConditionValue("");
    refresh();
  }

  async function handleDelete(id: string) {
    await adminApi.deleteCustomRule(id);
    refresh();
  }

  return (
    <div className="space-y-8">
      <section className="card p-6">
        <h2 className="text-lg font-semibold mb-4">New custom rule</h2>
        <form onSubmit={handleCreate} className="grid grid-cols-2 gap-4">
          <label className="flex flex-col gap-1 text-sm">
            Name
            <input
              required
              className="bg-rulescope-surfaceAlt rounded-lg px-3 py-2"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            Severity
            <select
              className="bg-rulescope-surfaceAlt rounded-lg px-3 py-2"
              value={form.severity}
              onChange={(e) => setForm({ ...form, severity: e.target.value })}
            >
              {["critical", "high", "medium", "low", "info"].map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-sm col-span-2">
            Condition field
            <select
              className="bg-rulescope-surfaceAlt rounded-lg px-3 py-2"
              value={form.condition.field as string}
              onChange={(e) => setForm({ ...form, condition: { ...form.condition, field: e.target.value } })}
            >
              {["services", "source", "destination", "action"].map((f) => (
                <option key={f} value={f}>
                  {f}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-sm col-span-2">
            Match any of these values (comma-separated)
            <input
              className="bg-rulescope-surfaceAlt rounded-lg px-3 py-2"
              placeholder="tcp/23, tcp/21"
              value={conditionValue}
              onChange={(e) => setConditionValue(e.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-sm col-span-2">
            Description template
            <input
              className="bg-rulescope-surfaceAlt rounded-lg px-3 py-2"
              value={form.description_template}
              onChange={(e) => setForm({ ...form, description_template: e.target.value })}
            />
          </label>
          <label className="flex flex-col gap-1 text-sm col-span-2">
            Remediation
            <input
              required
              className="bg-rulescope-surfaceAlt rounded-lg px-3 py-2"
              value={form.remediation}
              onChange={(e) => setForm({ ...form, remediation: e.target.value })}
            />
          </label>
          <button type="submit" className="btn-primary col-span-2 w-fit">
            Add rule
          </button>
        </form>
      </section>

      <section className="card divide-y divide-rulescope-border">
        {rules.map((r) => (
          <div key={r.id} className="flex items-center justify-between p-4">
            <div>
              <p className="font-medium">
                {r.name} <span className={`badge badge-${r.severity} ml-2`}>{r.severity}</span>
              </p>
              <p className="text-xs text-rulescope-muted">{r.remediation}</p>
            </div>
            <button className="text-red-500 text-sm" onClick={() => handleDelete(r.id)}>
              Delete
            </button>
          </div>
        ))}
        {rules.length === 0 && <p className="p-4 text-rulescope-muted text-sm">No custom rules yet.</p>}
      </section>
    </div>
  );
}
