"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { auth, User, workspaces, Workspace, conversations, Conversation } from "@/lib/api";
import { MessageSquare, LayoutGrid } from "lucide-react";

export default function DashboardRoot() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [wsList, setWsList] = useState<Workspace[]>([]);
  
  useEffect(() => {
    auth.me().then(setUser).catch(console.error);
    workspaces.list().then(setWsList).catch(console.error);
  }, []);

  if (!user) return null;

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8 min-h-full">
      <div className="max-w-4xl w-full space-y-12 animate-in fade-in zoom-in duration-500">
        
        {/* Warm Greeting */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-text-primary">
            Welcome back, <span className="bg-gradient-to-r from-app-accent to-purple-400 bg-clip-text text-transparent">{user.username}</span>
          </h1>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto">
            Your Multi-Tenant AI Research Assistant is ready. Select a workspace or jump straight into a conversation to continue your work.
          </p>
        </div>

        {/* Two Bubbles Layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* Workspaces Bubble */}
          <div 
            onClick={() => router.push("/workspaces")}
            className="group relative bg-bg-secondary/50 backdrop-blur-xl border border-border/50 rounded-3xl p-8 hover:bg-bg-hover/80 hover:border-app-accent/50 transition-all duration-300 cursor-pointer overflow-hidden shadow-lg hover:shadow-app-accent/10"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-app-accent/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative flex flex-col items-center text-center space-y-4">
              <div className="w-16 h-16 rounded-2xl bg-app-accent/10 flex items-center justify-center text-app-accent group-hover:scale-110 transition-transform">
                <LayoutGrid size={32} />
              </div>
              <h2 className="text-2xl font-bold">Workspaces</h2>
              <p className="text-text-secondary">
                Manage your environments, team members, and allowed LLM models.
              </p>
              <div className="pt-4 flex items-center text-app-accent font-medium group-hover:translate-x-1 transition-transform">
                Go to Workspaces →
              </div>
            </div>
          </div>

          {/* Chat Bubble */}
          <div 
            onClick={() => {
              if (wsList.length > 0) {
                router.push("/workspaces"); // They still need to pick a workspace first to chat
              } else {
                router.push("/workspaces");
              }
            }}
            className="group relative bg-bg-secondary/50 backdrop-blur-xl border border-border/50 rounded-3xl p-8 hover:bg-bg-hover/80 hover:border-blue-500/50 transition-all duration-300 cursor-pointer overflow-hidden shadow-lg hover:shadow-blue-500/10"
          >
            <div className="absolute inset-0 bg-gradient-to-bl from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative flex flex-col items-center text-center space-y-4">
              <div className="w-16 h-16 rounded-2xl bg-blue-500/10 flex items-center justify-center text-blue-500 group-hover:scale-110 transition-transform">
                <MessageSquare size={32} />
              </div>
              <h2 className="text-2xl font-bold">Conversations</h2>
              <p className="text-text-secondary">
                Start a new AI chat or continue an existing thread in your workspace.
              </p>
              <div className="pt-4 flex items-center text-blue-500 font-medium group-hover:translate-x-1 transition-transform">
                Open Chat →
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
