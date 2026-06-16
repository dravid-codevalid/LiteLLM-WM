// File: page.tsx. Description: Workspace management page. Consists of: UI for creating/deleting workspaces, adding members, and starting conversations.
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { workspaces, Workspace, conversations, Conversation, auth, GlobalModel, User } from "@/lib/api";
import { WorkspaceCard } from "@/components/workspace/WorkspaceCard";
import { MemberManager } from "@/components/workspace/MemberManager";
import { ModelManager } from "@/components/workspace/ModelManager";

export default function WorkspacesPage() {
  const router = useRouter();
  const [wsList, setWsList] = useState<Workspace[]>([]);
  const [newName, setNewName] = useState("");
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [globalModels, setGlobalModels] = useState<GlobalModel[]>([]);
  const [creating, setCreating] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [convList, setConvList] = useState<Conversation[]>([]);
  const [newConvTitle, setNewConvTitle] = useState("");
  const [error, setError] = useState("");
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    auth.me().then(setUser).catch(console.error);
    workspaces.list().then(setWsList).catch(console.error);
    workspaces.availableModels().then(setGlobalModels).catch(console.error);
  }, []);

  useEffect(() => {
    if (selected) {
      conversations.list(selected).then(setConvList).catch(console.error);
    }
  }, [selected]);

  const selectedWs = wsList.find((w) => w.id === selected);
  const isAdmin = user && selectedWs && user.id === selectedWs.admin_id;

  const toggleModelSelection = (modelId: string) => {
    setSelectedModels((prev) => 
      prev.includes(modelId) ? prev.filter((id) => id !== modelId) : [...prev, modelId]
    );
  };

  const createWorkspace = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const ws = await workspaces.create(newName, selectedModels);
      setWsList((prev) => [...prev, ws]);
      setNewName("");
      setSelectedModels([]);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setCreating(false);
    }
  };

  const createConversation = async () => {
    if (!selected || !newConvTitle.trim()) return;
    try {
      const conv = await conversations.create(selected, newConvTitle);
      setNewConvTitle("");
      router.push(`/chat/${conv.id}`);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const deleteWorkspace = async (id: string) => {
    try {
      await workspaces.delete(id);
      setWsList((prev) => prev.filter((w) => w.id !== id));
      if (selected === id) setSelected(null);
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      <h1 className="text-2xl font-bold">Workspaces</h1>

      {/* Create workspace */}
      <div className="card space-y-4">
        <h2 className="font-semibold text-lg">Create New Workspace</h2>
        <div className="flex gap-3">
          <input
            id="new-workspace-name"
            className="input-field flex-1"
            placeholder="New workspace name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && createWorkspace()}
          />
          <button id="create-workspace" onClick={createWorkspace} className="btn-primary" disabled={creating}>
            Create
          </button>
        </div>
        {globalModels.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium text-text-secondary">Allowed Models</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-48 overflow-y-auto p-2 border border-border rounded-lg bg-bg-secondary/50">
              {globalModels.map((model) => (
                <label key={model.id} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-bg-hover p-1.5 rounded transition-colors">
                  <input
                    type="checkbox"
                    checked={selectedModels.includes(model.id)}
                    onChange={() => toggleModelSelection(model.id)}
                  />
                  <span>{model.model_name} <span className="text-xs text-text-secondary">({model.llm_company_name})</span></span>
                </label>
              ))}
            </div>
          </div>
        )}
      </div>

      {error && <p className="text-danger text-sm">{error}</p>}

      {/* Workspace list */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {wsList.map((ws) => (
          <WorkspaceCard
            key={ws.id}
            workspace={ws}
            isSelected={selected === ws.id}
            isAdmin={user ? user.id === ws.admin_id : false}
            onSelect={setSelected}
            onDelete={deleteWorkspace}
          />
        ))}
      </div>

      {/* Selected workspace panel */}
      {selected && (
        <div className="space-y-6">
          <MemberManager workspaceId={selected} isAdmin={!!isAdmin} currentUserId={user?.id} />
          <ModelManager workspaceId={selected} isAdmin={!!isAdmin} />

          <div className="card space-y-4">
            <h2 className="font-semibold text-lg">Conversations</h2>
            <div className="flex gap-3">
              <input
                id="new-conv-title"
                className="input-field flex-1"
                placeholder="New conversation title"
                value={newConvTitle}
                onChange={(e) => setNewConvTitle(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && createConversation()}
              />
              <button onClick={createConversation} className="btn-primary">New Chat</button>
            </div>

            <div className="space-y-2">
              {convList.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => router.push(`/chat/${conv.id}`)}
                  className="flex justify-between items-center px-4 py-3 bg-bg-secondary rounded-lg cursor-pointer hover:bg-bg-hover transition-all"
                >
                  <span className="font-medium">{conv.title}</span>
                  <span className="text-text-secondary text-xs">
                    {new Date(conv.created_at).toLocaleDateString()}
                  </span>
                </div>
              ))}
              {convList.length === 0 && (
                <p className="text-text-secondary text-sm text-center py-4">No conversations yet</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
