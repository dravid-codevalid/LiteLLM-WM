// File: useWebSocket.ts. Description: WebSocket lifecycle hook. Consists of: auto-connect/disconnect, reconnection logic with exponential backoff, and clean API for chat components.
"use client";

import { useEffect, useRef, useCallback } from "react";
import { useChatStore } from "@/store/chatStore";

interface UseWebSocketOptions {
  conversationId: string;
  maxReconnectAttempts?: number;
  reconnectDelay?: number;
}

export function useWebSocket({
  conversationId,
  maxReconnectAttempts = 5,
  reconnectDelay = 2000,
}: UseWebSocketOptions) {
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef<NodeJS.Timeout | null>(null);
  const conversationIdRef = useRef(conversationId);

  // Keep ref in sync so reconnection uses the latest ID
  conversationIdRef.current = conversationId;

  // Stable references to store actions (Zustand selectors are stable)
  const connect = useChatStore((s) => s.connect);
  const disconnect = useChatStore((s) => s.disconnect);
  const sendMessage = useChatStore((s) => s.sendMessage);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const setOnReconnect = useChatStore((s) => s.setOnReconnect);

  const attemptReconnect = useCallback(() => {
    if (reconnectAttempts.current >= maxReconnectAttempts) {
      console.warn(`WS: Max reconnect attempts (${maxReconnectAttempts}) reached. Giving up.`);
      return;
    }

    reconnectAttempts.current += 1;
    const delay = reconnectDelay * Math.pow(2, reconnectAttempts.current - 1);

    reconnectTimer.current = setTimeout(() => {
      connect(conversationIdRef.current);
    }, delay);
  }, [connect, maxReconnectAttempts, reconnectDelay]);

  useEffect(() => {
    if (!conversationId) return;

    // Reset reconnect counter on fresh connect
    reconnectAttempts.current = 0;

    // Register the reconnection callback in the store
    setOnReconnect(attemptReconnect);

    // Initial connection
    connect(conversationId);

    return () => {
      // Clean up on unmount or conversationId change
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
        reconnectTimer.current = null;
      }
      setOnReconnect(null);
      disconnect();
    };
  }, [conversationId]); // Only re-run when conversationId changes

  const send = useCallback(
    (model: string, prompt: string) => {
      if (!isStreaming) {
        sendMessage(model, prompt);
      }
    },
    [sendMessage, isStreaming]
  );

  return { send, isStreaming };
}
