"use client";

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ApiError, streamChat } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

const SESSION_QUESTION_CAP = 30;

type Props = { handle: string; starter: string; suggestions: string[] };

export function ChatPanel({ handle, starter, suggestions }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([{ role: "assistant", content: starter }]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [asked, setAsked] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages]);

  useEffect(() => () => abortRef.current?.abort(), []);

  async function ask(question: string) {
    const q = question.trim();
    if (!q || streaming) return;
    if (asked >= SESSION_QUESTION_CAP) {
      setError("You've reached this session's question limit. Reload the page to start over.");
      return;
    }
    const history = messages;
    setMessages([...history, { role: "user", content: q }, { role: "assistant", content: "" }]);
    setInput("");
    setError(null);
    setStreaming(true);
    setAsked((n) => n + 1);

    const controller = new AbortController();
    abortRef.current = controller;
    try {
      await streamChat(
        handle,
        q,
        history,
        (chunk) =>
          setMessages((prev) => {
            const next = prev.slice();
            const last = next[next.length - 1];
            next[next.length - 1] = { ...last, content: last.content + chunk };
            return next;
          }),
        controller.signal,
      );
    } catch (err) {
      if (controller.signal.aborted) return;
      setMessages((prev) => (prev[prev.length - 1]?.content === "" ? prev.slice(0, -2) : prev));
      setInput(q);
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setStreaming(false);
    }
  }

  const showSuggestions = messages.length === 1 && suggestions.length > 0;

  return (
    <section aria-label="AI chat" className="flex h-[70vh] min-h-[480px] flex-col rounded-xl border border-line bg-surface/70">
      <div className="border-b border-line px-4 py-3 font-mono text-xs uppercase tracking-[0.15em] text-faint">
        AI chat · @{handle}
      </div>

      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto px-4 py-4" aria-live="polite">
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "flex justify-end" : "flex"}>
            <div
              className={
                m.role === "user"
                  ? "max-w-[85%] rounded-2xl rounded-br-sm bg-accent/15 px-4 py-2 text-sm text-fg"
                  : "prose-chat max-w-[95%] text-sm leading-relaxed text-fg/90"
              }
            >
              {m.role === "assistant" ? (
                m.content ? (
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
                ) : (
                  <span className="inline-flex gap-1 text-faint" aria-label="Thinking">
                    <span className="animate-pulse">●</span>
                    <span className="animate-pulse [animation-delay:150ms]">●</span>
                    <span className="animate-pulse [animation-delay:300ms]">●</span>
                  </span>
                )
              ) : (
                m.content
              )}
            </div>
          </div>
        ))}

        {showSuggestions && (
          <div className="grid gap-2 pt-2 sm:grid-cols-2">
            {suggestions.map((s) => (
              <button
                key={s}
                onClick={() => ask(s)}
                className="rounded-lg border border-line bg-surface-2/60 px-3 py-2 text-left text-sm text-muted transition hover:border-accent/40 hover:text-fg"
              >
                {s}
              </button>
            ))}
          </div>
        )}
      </div>

      {error && (
        <p role="alert" className="mx-4 mb-2 rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
          {error}
        </p>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask(input);
        }}
        className="flex gap-2 border-t border-line p-3"
      >
        <label htmlFor="chat-input" className="sr-only">
          Ask a question
        </label>
        <input
          id="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          maxLength={1000}
          placeholder={`Ask anything about @${handle}…`}
          className="min-w-0 flex-1 rounded-lg border border-line bg-bg px-3 py-2 text-sm placeholder:text-faint focus:border-accent/60 focus:outline-none"
        />
        <button
          type="submit"
          disabled={streaming || !input.trim()}
          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-accent-fg disabled:opacity-40"
        >
          {streaming ? "…" : "Send"}
        </button>
      </form>
    </section>
  );
}
