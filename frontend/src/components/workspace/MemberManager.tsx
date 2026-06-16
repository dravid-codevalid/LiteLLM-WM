// File: MemberManager.tsx. Description: Workspace member management. Consists of: list of members, and form to add members by username with error handling.
"use client";

import { useState, useEffect, useCallback } from "react";
import { workspaces, auth, User, Member } from "@/lib/api";

interface MemberManagerProps {
  workspaceId: string;
  isAdmin: boolean;
  currentUserId?: string;
}

export function MemberManager({ workspaceId, isAdmin, currentUserId }: MemberManagerProps) {
  const [username, setUsername] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [suggestions, setSuggestions] = useState<User[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(false);

  const loadMembers = useCallback(async () => {
    try {
      const list = await workspaces.members.list(workspaceId);
      setMembers(list);
    } catch (err: any) {
      console.error("Failed to load members:", err);
    }
  }, [workspaceId]);

  useEffect(() => {
    loadMembers();
  }, [loadMembers]);

  useEffect(() => {
    if (username.length > 0 && showSuggestions) {
      const delay = setTimeout(() => {
        auth.searchUsers(username).then(setSuggestions).catch(() => setSuggestions([]));
      }, 300);
      return () => clearTimeout(delay);
    } else {
      setSuggestions([]);
    }
  }, [username, showSuggestions]);

  const addMember = async (memberUsername: string) => {
    if (!memberUsername.trim()) return;
    setError("");
    setSuccess("");
    setLoading(true);
    try {
      await workspaces.members.add(workspaceId, memberUsername);
      setSuccess(`Added "${memberUsername}" to workspace`);
      setUsername("");
      setShowSuggestions(false);
      await loadMembers();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const removeMember = async (memberId: string) => {
    setError("");
    setSuccess("");
    try {
      await workspaces.members.remove(workspaceId, memberId);
      setSuccess("Member removed");
      await loadMembers();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="card space-y-4">
      <h2 className="font-semibold text-lg">Members</h2>
      <div className="space-y-2">
        {members.map((member) => (
          <div key={member.id} className="flex items-center justify-between px-4 py-2 bg-bg-secondary rounded-lg">
            <div>
              <p className="font-medium">{member.username}</p>
              <p className="text-xs text-text-secondary">{member.email}</p>
            </div>
            {isAdmin && currentUserId && member.id !== currentUserId && (
              <button 
                onClick={() => removeMember(member.id)} 
                className="text-danger hover:underline text-sm font-medium transition-colors"
              >
                Remove
              </button>
            )}
          </div>
        ))}
      </div>
      
      {isAdmin && (
        <div className="space-y-2 mt-4">
          <div className="flex gap-3 relative">
            <input
              id="add-member-username"
              className="input-field flex-1"
              placeholder="Username to add"
              value={username}
              onChange={(e) => {
                setUsername(e.target.value);
                setShowSuggestions(true);
              }}
              onFocus={() => setShowSuggestions(true)}
              onKeyDown={(e) => e.key === "Enter" && addMember(username)}
            />
            <button onClick={() => addMember(username)} className="btn-primary">
              Add
            </button>

            {showSuggestions && suggestions.length > 0 && (
              <div className="absolute top-full left-0 right-20 mt-1 bg-bg-secondary border border-border rounded-lg shadow-lg overflow-hidden z-10">
                {suggestions.map((user) => (
                  <div
                    key={user.id}
                    className="px-4 py-2 hover:bg-bg-hover cursor-pointer text-sm"
                    onClick={() => {
                      setUsername(user.username);
                      setShowSuggestions(false);
                      addMember(user.username);
                    }}
                  >
                    {user.username}
                  </div>
                ))}
              </div>
            )}
          </div>
          {error && <p className="text-danger text-sm">{error}</p>}
          {success && <p className="text-success text-sm">{success}</p>}
        </div>
      )}
    </div>
  );
}
