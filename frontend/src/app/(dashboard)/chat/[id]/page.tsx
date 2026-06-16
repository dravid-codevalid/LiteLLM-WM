// File: page.tsx. Description: Real-time chat interface. Consists of: WebSocket connection handling, message streaming UI, and model selection.
"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { conversations, workspaces, GlobalModel } from "@/lib/api";
import { useChatStore } from "@/store/chatStore";
import { useWebSocket } from "@/hooks/useWebSocket";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { ChatInput } from "@/components/chat/ChatInput";

export default function ChatPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { messages, setMessages, activeUsers, error, clearError } = useChatStore();
  const { send, isStreaming } = useWebSocket({ conversationId: id });
  const [prompt, setPrompt] = useState("");
  const [models, setModels] = useState<GlobalModel[]>([]);
  const [selectedModel, setSelectedModel] = useState("");
  const [title, setTitle] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  // Load conversation data
  useEffect(() => {
    if (!id) return;

    conversations
      .get(id)
      .then((conv) => {
        setTitle(conv.title);
        const chatMsgs = conv.messages.flatMap((m) => [
          { role: "user" as const, content: m.prompt_text, id: m.id },
          { role: "assistant" as const, content: m.response_text, id: m.id, model: m.model_used },
        ]);
        setMessages(chatMsgs);

        workspaces.models.list(conv.workspace_id).then((m) => {
          setModels(m);
          if (m.length > 0) setSelectedModel(m[0].model_name);
        });
      })
      .catch(() => router.push("/workspaces"));
  }, [id]);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    if (!prompt.trim() || !selectedModel || isStreaming) return;
    send(selectedModel, prompt);
    setPrompt("");
  };

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-border px-6 py-4 flex items-center justify-between bg-bg-secondary/50 backdrop-blur-sm">
        <div className="flex items-center gap-4">
          <button onClick={() => router.push("/workspaces")} className="btn-ghost text-sm">
            ← Back
          </button>
          <div className="flex flex-col">
            <h1 className="font-semibold text-lg">{title}</h1>
            <div className="flex items-center gap-2 mt-1">
              {activeUsers.map(u => (
                <div key={u.id} className="flex items-center gap-1 bg-app-accent/10 px-2 py-0.5 rounded-full" title={u.username}>
                  <div className="w-2 h-2 rounded-full bg-success animate-pulse"></div>
                  <span className="text-xs text-text-secondary">{u.username}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </header>

      {/* Error Alert */}
      {error && (
        <div className="bg-danger/10 border border-danger/20 text-danger px-6 py-2 flex justify-between items-center">
          <span className="text-sm">{error}</span>
          <button onClick={clearError} className="text-danger hover:text-danger/80">×</button>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <p className="text-text-secondary text-lg">Start a conversation</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble
            key={i}
            role={msg.role}
            content={msg.content}
            model={msg.model}
            isStreaming={msg.isStreaming}
          />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <ChatInput
        prompt={prompt}
        setPrompt={setPrompt}
        models={models}
        selectedModel={selectedModel}
        setSelectedModel={setSelectedModel}
        isStreaming={isStreaming}
        onSend={handleSend}
      />
    </div>
  );
}
