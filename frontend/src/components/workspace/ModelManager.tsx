"use client";

import { useState, useEffect, useCallback } from "react";
import { workspaces, GlobalModel } from "@/lib/api";

interface ModelManagerProps {
  workspaceId: string;
  isAdmin: boolean;
}

export function ModelManager({ workspaceId, isAdmin }: ModelManagerProps) {
  const [globalModels, setGlobalModels] = useState<GlobalModel[]>([]);
  const [allowedModels, setAllowedModels] = useState<GlobalModel[]>([]);
  const [error, setError] = useState("");
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [globals, allowed] = await Promise.all([
        workspaces.availableModels(),
        workspaces.models.list(workspaceId),
      ]);
      setGlobalModels(globals);
      setAllowedModels(allowed);
    } catch (err: any) {
      console.error("Failed to load models:", err);
      setError(err.message);
    }
  }, [workspaceId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const toggleModel = async (modelId: string, isCurrentlyAllowed: boolean) => {
    if (!isAdmin) return;
    setError("");
    setLoadingId(modelId);
    try {
      if (isCurrentlyAllowed) {
        await workspaces.models.remove(workspaceId, modelId);
      } else {
        await workspaces.models.add(workspaceId, modelId);
      }
      await loadData();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoadingId(null);
    }
  };

  if (!isAdmin) {
    return (
      <div className="card space-y-4">
        <h2 className="font-semibold text-lg">Allowed Models</h2>
        <div className="space-y-2">
          {allowedModels.length === 0 ? (
            <p className="text-text-secondary text-sm">No models allowed in this workspace.</p>
          ) : (
            allowedModels.map((m) => (
              <div key={m.id} className="px-4 py-2 bg-bg-secondary rounded-lg">
                <p className="font-medium">{m.model_name}</p>
                <p className="text-xs text-text-secondary">{m.llm_company_name}</p>
              </div>
            ))
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="card space-y-4">
      <h2 className="font-semibold text-lg">Manage Allowed Models</h2>
      {error && <p className="text-danger text-sm">{error}</p>}
      <div className="space-y-2">
        {globalModels.map((model) => {
          const isAllowed = allowedModels.some((m) => m.id === model.id);
          return (
            <div key={model.id} className="flex items-center justify-between px-4 py-2 bg-bg-secondary rounded-lg">
              <div>
                <p className="font-medium">{model.model_name}</p>
                <p className="text-xs text-text-secondary">{model.llm_company_name}</p>
              </div>
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="mr-2"
                  checked={isAllowed}
                  onChange={() => toggleModel(model.id, isAllowed)}
                  disabled={loadingId === model.id}
                />
                <span className="text-sm">{isAllowed ? "Enabled" : "Disabled"}</span>
              </label>
            </div>
          );
        })}
      </div>
    </div>
  );
}
