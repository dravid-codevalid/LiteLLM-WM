// File: page.tsx. Description: Usage analytics dashboard. Consists of: Token and cost metric visualizations for both individual members and workspace admins.
"use client";

import { useEffect, useState } from "react";
import { workspaces, usage, Workspace, UsageSummary, WorkspaceUsage } from "@/lib/api";

export default function UsagePage() {
  const [wsList, setWsList] = useState<Workspace[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [myUsage, setMyUsage] = useState<UsageSummary | null>(null);
  const [wsUsage, setWsUsage] = useState<WorkspaceUsage | null>(null);

  useEffect(() => {
    workspaces.list().then(setWsList);
  }, []);

  useEffect(() => {
    if (!selected) return;
    usage.me(selected).then(setMyUsage).catch(console.error);
    usage.workspace(selected).then(setWsUsage).catch(() => setWsUsage(null));
  }, [selected]);

  const formatCost = (n: number) => `$${n.toFixed(4)}`;

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      <h1 className="text-2xl font-bold">Usage Analytics</h1>

      {/* Workspace selector */}
      <select
        id="usage-workspace-selector"
        value={selected || ""}
        onChange={(e) => setSelected(e.target.value || null)}
        className="bg-bg-secondary border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent w-full max-w-xs"
      >
        <option value="">Select a workspace</option>
        {wsList.map((ws) => (
          <option key={ws.id} value={ws.id}>{ws.name}</option>
        ))}
      </select>

      {myUsage && (
        <div className="card space-y-4">
          <h2 className="font-semibold text-lg">Your Usage</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Stat label="Prompt Tokens" value={myUsage.total_prompt_tokens.toLocaleString()} />
            <Stat label="Completion Tokens" value={myUsage.total_completion_tokens.toLocaleString()} />
            <Stat label="Total Tokens" value={myUsage.total_tokens.toLocaleString()} />
            <Stat label="Total Cost" value={formatCost(myUsage.total_cost)} highlight />
          </div>
        </div>
      )}

      {wsUsage && (
        <div className="card space-y-4">
          <h2 className="font-semibold text-lg">Workspace Total</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Stat label="Total Tokens" value={wsUsage.workspace_total.total_tokens.toLocaleString()} />
            <Stat label="Total Cost" value={formatCost(wsUsage.workspace_total.total_cost)} highlight />
            <Stat label="Records" value={wsUsage.workspace_total.record_count.toLocaleString()} />
          </div>

          {wsUsage.per_user.length > 0 && (
            <>
              <h3 className="font-medium mt-6 text-text-secondary">Per-User Breakdown</h3>
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
                    {wsUsage.per_user.map((u) => (
                      <tr key={u.user_id} className="border-b border-border/50 hover:bg-bg-hover/30">
                        <td className="py-2 px-3 font-medium">{u.username}</td>
                        <td className="py-2 px-3">{u.total_prompt_tokens.toLocaleString()}</td>
                        <td className="py-2 px-3">{u.total_completion_tokens.toLocaleString()}</td>
                        <td className="py-2 px-3">{u.total_tokens.toLocaleString()}</td>
                        <td className="py-2 px-3 text-app-accent">{formatCost(u.total_cost)}</td>
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
  );
}

function Stat({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="bg-bg-secondary rounded-lg p-4">
      <p className="text-text-secondary text-xs">{label}</p>
      <p className={`text-xl font-semibold mt-1 ${highlight ? "text-app-accent" : ""}`}>{value}</p>
    </div>
  );
}
