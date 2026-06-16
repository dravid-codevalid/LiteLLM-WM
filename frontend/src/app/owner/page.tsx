// File: page.tsx. Description: Owner-only administration portal. Consists of: GlobalModel CRUD, cross-workspace financial analytics with charts.
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { auth, admin, GlobalModelAdmin, User, LiteLLMModel } from "@/lib/api";
import { SearchableDropdown } from "@/components/owner/SearchableDropdown";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

const CHART_COLORS = ["#6366f1", "#818cf8", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];

interface WorkspaceUsageData {
  workspace_id: string | null;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  total_cost: number;
  record_count: number;
}

interface WorkspaceDetail {
  total: {
    total_prompt_tokens: number;
    total_completion_tokens: number;
    total_tokens: number;
    total_cost: number;
    record_count: number;
  };
  per_user: Array<{
    user_id: string;
    username: string;
    total_prompt_tokens: number;
    total_completion_tokens: number;
    total_tokens: number;
    total_cost: number;
  }>;
}

export default function OwnerPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [models, setModels] = useState<GlobalModelAdmin[]>([]);
  const [litellmModels, setLitellmModels] = useState<LiteLLMModel[]>([]);
  const [form, setForm] = useState({
    llm_company_name: "",
    model_type: "chat",
    model_name: "",
    api_key: "",
    fallback_input_cost_per_million: "",
    fallback_output_cost_per_million: "",
  });
  const [error, setError] = useState("");

  // Analytics state
  const [globalUsage, setGlobalUsage] = useState<WorkspaceUsageData[]>([]);
  const [selectedWs, setSelectedWs] = useState<string | null>(null);
  const [wsDetail, setWsDetail] = useState<WorkspaceDetail | null>(null);

  useEffect(() => {
    auth
      .me()
      .then((u) => {
        if (!u.is_owner) {
          router.push("/workspaces");
          return;
        }
        setUser(u);
      })
      .catch((err) => {
        console.error("Auth failed in OwnerPage:", err);
        router.push("/login");
      });

    loadModels();
    loadGlobalUsage();
    admin.litellmModels().then(setLitellmModels).catch(console.error);
  }, [router]);

  const loadModels = () => {
    admin.models.list().then(setModels).catch(console.error);
  };

  const loadGlobalUsage = () => {
    admin.usage.global().then((data) => setGlobalUsage(data as WorkspaceUsageData[])).catch(console.error);
  };

  const loadWorkspaceDetail = async (wsId: string) => {
    setSelectedWs(wsId);
    try {
      const data = await admin.usage.workspace(wsId);
      setWsDetail(data as WorkspaceDetail);
    } catch {
      setWsDetail(null);
    }
  };

  const isKnownModel = form.model_name.length > 0 && litellmModels.some(
    (m) => m.model_name.toLowerCase() === form.model_name.toLowerCase()
  );

  const uniqueProviders = Array.from(
    new Set(litellmModels.map((m) => m.provider))
  ).sort();

  const filteredModelNames = litellmModels
    .filter((m) => {
      if (!form.llm_company_name) return true;
      return m.provider.toLowerCase() === form.llm_company_name.toLowerCase();
    })
    .map((m) => m.model_name);

  const handleModelChange = (modelName: string) => {
    const matched = litellmModels.find(
      (m) => m.model_name.toLowerCase() === modelName.toLowerCase()
    );
    if (matched) {
      setForm((prev) => ({
        ...prev,
        model_name: modelName,
        llm_company_name: matched.provider,
        model_type: matched.model_type || prev.model_type,
      }));
    } else {
      setForm((prev) => ({ ...prev, model_name: modelName }));
    }
  };

  const handleProviderChange = (provider: string) => {
    setForm((prev) => {
      const matched = litellmModels.find(
        (m) => m.model_name.toLowerCase() === prev.model_name.toLowerCase()
      );
      const isStillValid = matched && matched.provider.toLowerCase() === provider.toLowerCase();
      return {
        ...prev,
        llm_company_name: provider,
        model_name: isStillValid ? prev.model_name : "",
      };
    });
  };

  const createModel = async () => {
    setError("");
    try {
      const manualPricing = !isKnownModel && form.model_name.length > 0;
      const payload = {
        llm_company_name: form.llm_company_name,
        model_type: form.model_type,
        model_name: form.model_name,
        api_key: form.api_key,
        requires_manual_pricing: manualPricing,
        fallback_input_cost_per_million: manualPricing && form.fallback_input_cost_per_million
          ? parseFloat(form.fallback_input_cost_per_million)
          : null,
        fallback_output_cost_per_million: manualPricing && form.fallback_output_cost_per_million
          ? parseFloat(form.fallback_output_cost_per_million)
          : null,
      };

      await admin.models.create(payload);
      setForm({
        llm_company_name: "",
        model_type: "chat",
        model_name: "",
        api_key: "",
        fallback_input_cost_per_million: "",
        fallback_output_cost_per_million: "",
      });
      loadModels();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const deleteModel = async (id: string) => {
    await admin.models.delete(id);
    loadModels();
  };

  const handleLogout = async () => {
    await auth.logout();
    router.push("/login");
  };

  if (!user) return null;

  const totalCost = globalUsage.reduce((sum, ws) => sum + ws.total_cost, 0);
  const totalTokens = globalUsage.reduce((sum, ws) => sum + ws.total_tokens, 0);
  const totalRecords = globalUsage.reduce((sum, ws) => sum + ws.record_count, 0);

  const barChartData = globalUsage.map((ws, i) => ({
    name: ws.workspace_id ? `WS-${ws.workspace_id.slice(0, 6)}` : "Deleted",
    cost: ws.total_cost,
    tokens: ws.total_tokens,
    id: ws.workspace_id,
  }));

  const pieData = globalUsage.map((ws, i) => ({
    name: ws.workspace_id ? `WS-${ws.workspace_id.slice(0, 6)}` : "Deleted",
    value: ws.total_cost,
  }));

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Header */}
      <header className="border-b border-border px-8 py-4 flex justify-between items-center bg-bg-secondary/50 backdrop-blur-sm">
        <h1 className="text-xl font-bold bg-gradient-to-r from-app-accent to-purple-400 bg-clip-text text-transparent">
          Owner Portal
        </h1>
        <div className="flex items-center gap-4">
          <span className="text-text-secondary text-sm">{user.username}</span>
          <button onClick={handleLogout} className="btn-ghost text-sm">
            Sign Out
          </button>
        </div>
      </header>

      <div className="max-w-6xl mx-auto p-8 space-y-8">
        {/* ---- Usage Analytics Section ---- */}
        <div className="space-y-6">
          <h2 className="text-xl font-bold">Usage Analytics</h2>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <SummaryCard label="Total Cost" value={`$${totalCost.toFixed(4)}`} highlight />
            <SummaryCard label="Total Tokens" value={totalTokens.toLocaleString()} />
            <SummaryCard label="Total Records" value={totalRecords.toLocaleString()} />
            <SummaryCard label="Active Workspaces" value={globalUsage.length.toString()} />
          </div>

          {/* Charts */}
          {globalUsage.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Bar Chart - Cost by Workspace */}
              <div className="card">
                <h3 className="font-semibold mb-4 text-text-secondary text-sm uppercase tracking-wide">
                  Cost by Workspace
                </h3>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={barChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2a2a45" />
                    <XAxis dataKey="name" stroke="#8888a8" fontSize={12} />
                    <YAxis stroke="#8888a8" fontSize={12} tickFormatter={(v) => `$${v}`} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1a1a2e",
                        border: "1px solid #2a2a45",
                        borderRadius: "8px",
                        color: "#e8e8f0",
                      }}
                      formatter={(value) => [`$${Number(value ?? 0).toFixed(4)}`, "Cost"]}
                    />
                    <Bar
                      dataKey="cost"
                      fill="#6366f1"
                      radius={[6, 6, 0, 0]}
                      cursor="pointer"
                      onClick={(data) => data.id && loadWorkspaceDetail(data.id)}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Pie Chart - Cost Distribution */}
              <div className="card">
                <h3 className="font-semibold mb-4 text-text-secondary text-sm uppercase tracking-wide">
                  Cost Distribution
                </h3>
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={3}
                      dataKey="value"
                    >
                      {pieData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1a1a2e",
                        border: "1px solid #2a2a45",
                        borderRadius: "8px",
                        color: "#e8e8f0",
                      }}
                      formatter={(value) => [`$${Number(value ?? 0).toFixed(4)}`, "Cost"]}
                    />
                    <Legend
                      wrapperStyle={{ color: "#8888a8", fontSize: "12px" }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {globalUsage.length === 0 && (
            <div className="card text-center text-text-secondary py-8">
              <p>No usage data yet. Start using models to see analytics.</p>
            </div>
          )}

          {/* Workspace Detail Drill-down */}
          {wsDetail && selectedWs && (
            <div className="card space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="font-semibold text-lg">
                  Workspace Detail:{" "}
                  <span className="font-mono text-app-accent">{selectedWs.slice(0, 8)}...</span>
                </h3>
                <button onClick={() => { setWsDetail(null); setSelectedWs(null); }} className="btn-ghost text-sm">
                  Close
                </button>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <SummaryCard label="Total Cost" value={`$${wsDetail.total.total_cost.toFixed(4)}`} highlight />
                <SummaryCard label="Total Tokens" value={wsDetail.total.total_tokens.toLocaleString()} />
                <SummaryCard label="Prompt Tokens" value={wsDetail.total.total_prompt_tokens.toLocaleString()} />
                <SummaryCard label="Records" value={wsDetail.total.record_count.toLocaleString()} />
              </div>

              {wsDetail.per_user.length > 0 && (
                <>
                  <h4 className="font-medium mt-4 text-text-secondary">Per-User Breakdown</h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-text-secondary text-left border-b border-border">
                          <th className="py-2 px-3">User</th>
                          <th className="py-2 px-3">Prompt</th>
                          <th className="py-2 px-3">Completion</th>
                          <th className="py-2 px-3">Total</th>
                          <th className="py-2 px-3">Cost</th>
                        </tr>
                      </thead>
                      <tbody>
                        {wsDetail.per_user.map((u) => (
                          <tr key={u.user_id} className="border-b border-border/50 hover:bg-bg-hover/30">
                            <td className="py-2 px-3 font-medium">{u.username}</td>
                            <td className="py-2 px-3">{u.total_prompt_tokens.toLocaleString()}</td>
                            <td className="py-2 px-3">{u.total_completion_tokens.toLocaleString()}</td>
                            <td className="py-2 px-3">{u.total_tokens.toLocaleString()}</td>
                            <td className="py-2 px-3 text-app-accent">${u.total_cost.toFixed(4)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        {/* ---- Model Management Section ---- */}
        <div className="space-y-6">
          <h2 className="text-xl font-bold">Model Management</h2>

          {/* Add model form */}
          <div className="card space-y-4">
            <h3 className="font-semibold text-lg">Add Global Model</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-text-secondary block mb-1">Model Provider / Company</label>
                <SearchableDropdown
                  id="model-company"
                  placeholder="e.g., OpenAI"
                  options={uniqueProviders}
                  value={form.llm_company_name}
                  onChange={handleProviderChange}
                />
              </div>
              <div>
                <label className="text-xs text-text-secondary block mb-1">Model Type</label>
                <select
                  id="model-type"
                  className="input-field"
                  value={form.model_type}
                  onChange={(e) => setForm({ ...form, model_type: e.target.value })}
                >
                  <option value="chat">Chat</option>
                  <option value="completion">Completion</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-text-secondary block mb-1">Model Name</label>
                <SearchableDropdown
                  id="model-name"
                  placeholder="e.g., gpt-4o"
                  options={filteredModelNames}
                  value={form.model_name}
                  onChange={handleModelChange}
                />
              </div>
              <div>
                <label className="text-xs text-text-secondary block mb-1">API Key</label>
                <input
                  id="model-api-key"
                  type="password"
                  className="input-field"
                  placeholder="API Key"
                  value={form.api_key}
                  onChange={(e) => setForm({ ...form, api_key: e.target.value })}
                  required
                />
              </div>

              {!isKnownModel && form.model_name.length > 0 && (
                <div className="col-span-1 md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-xl border border-app-accent/20 bg-app-accent/5 animate-in fade-in slide-in-from-top-1 duration-200">
                  <div className="col-span-1 md:col-span-2">
                    <h4 className="text-sm font-semibold text-app-accent">Custom Model Detected</h4>
                    <p className="text-xs text-text-secondary mt-0.5">
                      This model is not pre-configured in LiteLLM. Please specify fallback token pricing to enable accurate cost ledger calculations.
                    </p>
                  </div>
                  <div>
                    <label className="text-xs text-text-secondary block mb-1">Input cost per million tokens ($)</label>
                    <input
                      id="model-fallback-input"
                      type="number"
                      step="0.000001"
                      className="input-field"
                      placeholder="e.g. 2.50"
                      value={form.fallback_input_cost_per_million}
                      onChange={(e) => setForm({ ...form, fallback_input_cost_per_million: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs text-text-secondary block mb-1">Output cost per million tokens ($)</label>
                    <input
                      id="model-fallback-output"
                      type="number"
                      step="0.000001"
                      className="input-field"
                      placeholder="e.g. 10.00"
                      value={form.fallback_output_cost_per_million}
                      onChange={(e) => setForm({ ...form, fallback_output_cost_per_million: e.target.value })}
                      required
                    />
                  </div>
                </div>
              )}
            </div>
            {error && <p className="text-danger text-sm">{error}</p>}
            <button id="create-model" onClick={createModel} className="btn-primary">
              Add Model
            </button>
          </div>

          {/* Models list */}
          <div className="card space-y-4">
            <h3 className="font-semibold text-lg">Global Models ({models.length})</h3>
            <div className="space-y-3">
              {models.map((m) => (
                <div key={m.id} className="flex items-center justify-between bg-bg-secondary rounded-lg px-4 py-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-3">
                      <span className="font-medium">{m.model_name}</span>
                      <span className="text-xs bg-app-accent/10 text-app-accent px-2 py-0.5 rounded-full">
                        {m.llm_company_name}
                      </span>
                      <span className="text-xs text-text-secondary">{m.model_type}</span>
                    </div>
                    <p className="text-xs text-text-secondary font-mono">{m.api_key_masked}</p>
                  </div>
                  <button onClick={() => deleteModel(m.id)} className="btn-danger text-xs px-2 py-1">
                    Delete
                  </button>
                </div>
              ))}
              {models.length === 0 && (
                <p className="text-text-secondary text-sm text-center py-4">No models configured</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function SummaryCard({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="bg-bg-secondary rounded-lg p-4">
      <p className="text-text-secondary text-xs">{label}</p>
      <p className={`text-xl font-semibold mt-1 ${highlight ? "text-app-accent" : ""}`}>{value}</p>
    </div>
  );
}
