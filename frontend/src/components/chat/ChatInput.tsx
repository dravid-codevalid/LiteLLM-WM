// File: ChatInput.tsx. Description: Chat input bar. Consists of: prompt text field, model selector, and send button.
"use client";

import { GlobalModel } from "@/lib/api";

interface ChatInputProps {
  prompt: string;
  setPrompt: (value: string) => void;
  models: GlobalModel[];
  selectedModel: string;
  setSelectedModel: (value: string) => void;
  isStreaming: boolean;
  onSend: () => void;
}

export function ChatInput({
  prompt,
  setPrompt,
  models,
  selectedModel,
  setSelectedModel,
  isStreaming,
  onSend,
}: ChatInputProps) {
  return (
    <div className="border-t border-border px-6 py-4 bg-bg-secondary/50 backdrop-blur-sm">
      <div className="flex gap-3 max-w-4xl mx-auto">
        <select
          id="model-selector"
          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value)}
          className="bg-bg-secondary border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-app-accent"
        >
          {models.map((m) => (
            <option key={m.id} value={m.model_name}>
              {m.model_name}
            </option>
          ))}
          {models.length === 0 && <option value="">No models available</option>}
        </select>
        <input
          id="chat-input"
          className="input-field flex-1"
          placeholder={isStreaming ? "Waiting for response..." : "Type your message..."}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && onSend()}
          disabled={isStreaming}
        />
        <button
          id="chat-send"
          onClick={onSend}
          className="btn-primary"
          disabled={isStreaming || !prompt.trim() || !selectedModel}
        >
          {isStreaming ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}
