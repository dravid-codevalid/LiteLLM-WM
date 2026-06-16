// File: chatStore.ts. Description: Client state management. Consists of: Zustand store handling WebSocket connections, message streaming, and chat history.
"use client";

import { create } from "zustand";
import { auth } from "@/lib/api";

interface ChatMessage {
  id?: string;
  role: "user" | "assistant";
  content: string;
  model?: string;
  isStreaming?: boolean;
}

interface ChatStore {
  messages: ChatMessage[];
  isStreaming: boolean;
  ws: WebSocket | null;
  activeUsers: { id: string; username: string }[];
  error: string | null;
  onReconnect: (() => void) | null;
  connect: (conversationId: string) => void;
  disconnect: () => void;
  sendMessage: (model: string, prompt: string) => void;
  setMessages: (msgs: ChatMessage[]) => void;
  clearError: () => void;
  setOnReconnect: (cb: (() => void) | null) => void;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [],
  isStreaming: false,
  ws: null,
  activeUsers: [],
  error: null,
  onReconnect: null,

  connect: (conversationId: string) => {
    const existing = get().ws;
    if (existing) {
      existing.onclose = null; // prevent reconnect trigger from cleanup close
      existing.close();
    }

    // Fetch WS auth token via proxied REST API (cookie sent automatically),
    // then connect directly to backend with token as query param
    auth
      .wsToken()
      .then(({ token }) => {
        const wsUrl = `ws://127.0.0.1:8000/ws/chat/${conversationId}?token=${encodeURIComponent(token)}`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          set({ error: null });
        };

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);

          if (data.type === "message_chunk") {
            set((state) => {
              const msgs = [...state.messages];
              const last = msgs[msgs.length - 1];
              if (last?.role === "assistant" && last.isStreaming) {
                msgs[msgs.length - 1] = { ...last, content: last.content + data.content };
              } else {
                msgs.push({ role: "assistant", content: data.content, isStreaming: true });
              }
              return { messages: msgs };
            });
          }

          if (data.type === "message_complete") {
            set((state) => {
              const msgs = [...state.messages];
              const last = msgs[msgs.length - 1];
              if (last?.role === "assistant") {
                msgs[msgs.length - 1] = { ...last, isStreaming: false, id: data.message_id, model: data.model_used };
              }
              return { messages: msgs, isStreaming: false };
            });
          }

          if (data.type === "presence_update") {
            set({ activeUsers: data.active_users });
          }

          if (data.type === "error") {
            set({ isStreaming: false, error: data.detail });
            console.error("WS error:", data.detail);
          }
        };

        ws.onclose = (event) => {
          if (event.code !== 1000) {
            set({ error: `WebSocket disconnected (code ${event.code}): ${event.reason || "Unknown reason"}` });
            // Trigger reconnection for transient failures (not auth failures)
            const { onReconnect } = get();
            if (onReconnect && event.code !== 4001) {
              onReconnect();
            }
          }
        };

        ws.onerror = (event) => {
          console.error("WS error event:", event);
        };

        set({ ws });
      })
      .catch((err) => {
        console.error("Failed to fetch WS token:", err);
        set({ error: "Authentication failed. Please log in again." });
      });
  },

  disconnect: () => {
    const { ws } = get();
    if (ws) {
      ws.onclose = null; // prevent reconnect trigger
      ws.close(1000, "Client disconnect");
    }
    set({ ws: null });
  },

  sendMessage: (model: string, prompt: string) => {
    const { ws } = get();
    if (!ws) {
      set({ error: "WebSocket is not connected." });
      return;
    }
    if (ws.readyState !== WebSocket.OPEN) {
      set({ error: `WebSocket is not open. State: ${ws.readyState}` });
      return;
    }

    set((state) => ({
      messages: [...state.messages, { role: "user", content: prompt }],
      isStreaming: true,
      error: null,
    }));

    ws.send(JSON.stringify({ type: "send_message", model, prompt }));
  },

  setMessages: (msgs: ChatMessage[]) => set({ messages: msgs }),
  clearError: () => set({ error: null }),
  setOnReconnect: (cb: (() => void) | null) => set({ onReconnect: cb }),
}));
