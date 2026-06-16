// File: WorkspaceCard.tsx. Description: Workspace card display. Consists of: clickable card showing workspace name, ID preview, and delete action.
"use client";

import { Workspace } from "@/lib/api";

interface WorkspaceCardProps {
  workspace: Workspace;
  isSelected: boolean;
  isAdmin: boolean;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

export function WorkspaceCard({ workspace, isSelected, isAdmin, onSelect, onDelete }: WorkspaceCardProps) {
  return (
    <div
      className={`card cursor-pointer transition-all duration-200 ${
        isSelected ? "border-app-accent ring-1 ring-app-accent/30" : "hover:border-border/80"
      }`}
      onClick={() => onSelect(workspace.id)}
    >
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-semibold text-lg">{workspace.name}</h3>
          <p className="text-text-secondary text-xs mt-1 font-mono">
            {workspace.id.slice(0, 8)}...
          </p>
        </div>
        {isAdmin && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(workspace.id);
            }}
            className="btn-danger text-xs px-2 py-1"
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
}
