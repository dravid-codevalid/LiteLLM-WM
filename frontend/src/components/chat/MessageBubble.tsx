// File: MessageBubble.tsx. Description: Chat message display. Consists of: styled message bubble supporting user/assistant roles with streaming indicator.
"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  model?: string;
  isStreaming?: boolean;
}

export function MessageBubble({ role, content, model, isStreaming }: MessageBubbleProps) {
  return (
    <div className={`flex ${role === "user" ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 overflow-hidden ${
          role === "user"
            ? "bg-app-accent text-white rounded-br-md"
            : "bg-bg-card border border-border rounded-bl-md"
        }`}
      >
        <div className="text-sm leading-relaxed overflow-x-auto">
          {role === "user" ? (
            <p className="whitespace-pre-wrap">{content}</p>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code(props: any) {
                  const { children, className, node, ...rest } = props;
                  const match = /language-(\w+)/.exec(className || "");
                  return match ? (
                    <SyntaxHighlighter
                      {...rest}
                      PreTag="div"
                      children={String(children).replace(/\n$/, "")}
                      language={match[1]}
                      style={vscDarkPlus}
                      customStyle={{ margin: 0, borderRadius: '0.375rem' }}
                    />
                  ) : (
                    <code {...rest} className="bg-bg-secondary px-1 py-0.5 rounded text-app-accent text-xs">
                      {children}
                    </code>
                  );
                },
                table: ({node, ...props}) => <div className="overflow-x-auto my-4"><table className="min-w-full divide-y divide-border border border-border" {...props} /></div>,
                thead: ({node, ...props}) => <thead className="bg-bg-secondary" {...props} />,
                th: ({node, ...props}) => <th className="px-3 py-2 text-left text-xs font-medium text-text-secondary uppercase tracking-wider" {...props} />,
                td: ({node, ...props}) => <td className="px-3 py-2 whitespace-nowrap text-sm border-t border-border" {...props} />,
                p: ({node, ...props}) => <p className="mb-2 last:mb-0" {...props} />
              }}
            >
              {content}
            </ReactMarkdown>
          )}
        </div>
        {role === "assistant" && isStreaming && (
          <span className="inline-block w-2 h-4 bg-app-accent animate-pulse ml-1" />
        )}
        {model && !isStreaming && (
          <p className="text-[10px] mt-2 opacity-50">{model}</p>
        )}
      </div>
    </div>
  );
}
