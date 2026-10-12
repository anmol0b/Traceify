"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { normalizeHandle } from "@/lib/handle";

export function HandleSearch({ initial = "", compact = false }: { initial?: string; compact?: boolean }) {
  const router = useRouter();
  const [value, setValue] = useState(initial);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function submit(event: React.FormEvent) {
    event.preventDefault();
    const handle = normalizeHandle(value);
    if (!handle) {
      setError("Enter a handle like @naval or a URL like x.com/naval.");
      return;
    }
    setError(null);
    startTransition(() => router.push(`/x/${handle}`));
  }

  return (
    <form onSubmit={submit} className="w-full" noValidate>
      <div className={`flex gap-2 ${compact ? "" : "flex-col sm:flex-row"}`}>
        <label htmlFor="handle" className="sr-only">
          X handle or profile URL
        </label>
        <input
          id="handle"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="@naval or x.com/naval"
          autoComplete="off"
          spellCheck={false}
          aria-invalid={!!error}
          aria-describedby={error ? "handle-error" : undefined}
          className="min-w-0 flex-1 rounded-lg border border-line bg-surface px-4 py-3 font-mono text-sm text-fg placeholder:text-faint focus:border-accent/60 focus:outline-none focus:ring-2 focus:ring-accent/20"
        />
        <button
          type="submit"
          disabled={pending}
          className="rounded-lg bg-accent px-5 py-3 text-sm font-medium text-accent-fg transition hover:brightness-110 disabled:opacity-60"
        >
          {pending ? "Loading…" : "Trace profile →"}
        </button>
      </div>
      {error && (
        <p id="handle-error" className="mt-2 font-mono text-xs text-danger">
          {error}
        </p>
      )}
    </form>
  );
}
