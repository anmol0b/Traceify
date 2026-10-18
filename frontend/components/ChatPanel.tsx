"use client";

import { ArrowUp, ArrowUpRight, CircleAlert, LoaderCircle } from "lucide-react";
import { motion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { LogoMark } from "@/components/Brand";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { ApiError, streamChat } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";
import { cn } from "@/lib/utils";

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
    <section aria-label="AI chat" className="flex h-full min-h-0 flex-col">
      <header className="flex h-14 shrink-0 items-center justify-between gap-3 border-b px-4 md:px-6">
        <div className="flex min-w-0 items-baseline gap-2 text-sm">
          <span className="font-medium text-foreground">Chat</span>
          <span className="truncate font-mono text-[13px] text-subtle-foreground">@{handle}</span>
        </div>
        <span className="inline-flex shrink-0 items-center gap-2 text-[13px] text-muted-foreground">
          <span
            aria-hidden
            className={cn("size-2 rounded-full", streaming ? "animate-pulse bg-warning" : "bg-success")}
          />
          {streaming ? "Answering" : "Ready"}
        </span>
      </header>

      <div ref={scrollRef} className="min-h-0 flex-1 space-y-6 overflow-y-auto overscroll-contain px-4 py-6 md:px-6" aria-live="polite">
        {messages.map((m, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className={m.role === "user" ? "flex justify-end" : "flex gap-3"}
          >
            {m.role === "assistant" && (
              <div className="grid size-7 shrink-0 place-items-center rounded-full border bg-surface text-foreground">
                <LogoMark className="size-3.5" />
              </div>
            )}
            <div
              className={
                m.role === "user"
                  ? "max-w-[85%] rounded-2xl rounded-br-sm bg-secondary px-4 py-2.5 text-[15px] leading-relaxed text-foreground"
                  : "prose-chat min-w-0 flex-1 pt-0.5 text-[15px] leading-relaxed text-foreground/90"
              }
            >
              {m.role === "assistant" ? (
                m.content ? (
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
                ) : (
                  <span role="status" className="inline-flex h-6 items-center gap-1" aria-label="Thinking">
                    <span className="animate-dot size-1.5 rounded-full bg-foreground" />
                    <span className="animate-dot size-1.5 rounded-full bg-foreground [animation-delay:150ms]" />
                    <span className="animate-dot size-1.5 rounded-full bg-foreground [animation-delay:300ms]" />
                  </span>
                )
              ) : (
                m.content
              )}
            </div>
          </motion.div>
        ))}

        {showSuggestions && (
          <div className="pl-10">
            <p className="mb-2 text-xs text-subtle-foreground">Suggested</p>
            <div className="grid gap-2 sm:grid-cols-2">
              {suggestions.map((s, i) => (
                <motion.button
                  key={s}
                  type="button"
                  onClick={() => ask(s)}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.15 + i * 0.05, ease: [0.16, 1, 0.3, 1] }}
                  whileTap={{ scale: 0.98 }}
                  className="group flex items-start justify-between gap-3 rounded-lg border bg-surface px-3.5 py-3 text-left text-sm text-muted-foreground transition-colors duration-150 outline-none hover:border-input hover:bg-[#111] hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
                >
                  {s}
                  <ArrowUpRight
                    aria-hidden
                    className="mt-0.5 size-3.5 shrink-0 text-subtle-foreground transition-[color,transform] duration-150 group-hover:translate-x-px group-hover:-translate-y-px group-hover:text-foreground"
                  />
                </motion.button>
              ))}
            </div>
          </div>
        )}
      </div>

      {error && (
        <Alert variant="destructive" className="animate-enter mx-4 mb-1 w-auto border-destructive/30 bg-destructive/10 md:mx-6">
          <CircleAlert aria-hidden />
          <AlertDescription className="text-destructive/90">{error}</AlertDescription>
        </Alert>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask(input);
        }}
        className="shrink-0 p-3 md:p-4"
      >
        <div className="flex items-center gap-2 rounded-xl border border-input bg-surface p-1.5 pl-4 transition-[border-color,box-shadow] duration-150 ease-out focus-within:border-ring/70 focus-within:ring-4 focus-within:ring-ring/15">
          <label htmlFor="chat-input" className="sr-only">
            Ask a question
          </label>
          <input
            id="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            maxLength={1000}
            autoComplete="off"
            enterKeyHint="send"
            placeholder={`Ask anything about @${handle}…`}
            className="h-9 min-w-0 flex-1 bg-transparent text-base text-foreground outline-none placeholder:text-subtle-foreground sm:text-[15px]"
          />
          <Button
            type="submit"
            size="icon"
            disabled={streaming || !input.trim()}
            aria-label={streaming ? "Answering" : "Send"}
            className="size-9 rounded-lg hover:bg-primary/85 active:scale-95 disabled:bg-secondary disabled:text-subtle-foreground disabled:opacity-100"
          >
            {streaming ? <LoaderCircle aria-hidden className="animate-spin" /> : <ArrowUp aria-hidden />}
          </Button>
        </div>
      </form>
    </section>
  );
}
