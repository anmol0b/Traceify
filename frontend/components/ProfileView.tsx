"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError, getProfile, refreshProfile } from "@/lib/api";
import type { ProfileResponse } from "@/lib/types";
import { ChatPanel } from "./ChatPanel";
import { HandleSearch } from "./HandleSearch";
import { ProfileCard } from "./ProfileCard";
import { TweetInsights } from "./TweetInsights";

type State =
  | { status: "loading" }
  | { status: "error"; error: ApiError }
  | { status: "ready"; data: ProfileResponse; version: number };

const ERROR_TITLES: Record<string, string> = {
  not_found: "Account not found",
  private_account: "This account is private",
  invalid_handle: "That doesn't look like an X handle",
  rate_limited: "Slow down a little",
  upstream_rate_limited: "The data provider is busy",
  network: "Can't reach the API",
};

export function ProfileView({ handle }: { handle: string }) {
  const [state, setState] = useState<State>({ status: "loading" });
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    getProfile(handle, controller.signal)
      .then((data) => setState({ status: "ready", data, version: 0 }))
      .catch((err) => {
        if (controller.signal.aborted) return;
        setState({ status: "error", error: err instanceof ApiError ? err : new ApiError(0, "error", String(err)) });
      });
    return () => controller.abort();
  }, [handle]);

  async function refresh() {
    setRefreshing(true);
    try {
      const data = await refreshProfile(handle);
      setState((prev) => ({ status: "ready", data, version: prev.status === "ready" ? prev.version + 1 : 0 }));
    } catch (err) {
      setState({ status: "error", error: err instanceof ApiError ? err : new ApiError(0, "error", String(err)) });
    } finally {
      setRefreshing(false);
    }
  }

  if (state.status === "loading") return <ProfileSkeleton />;

  if (state.status === "error") {
    return (
      <div className="mx-auto max-w-xl space-y-6 py-10 text-center">
        <div className="font-serif text-5xl text-faint">∅</div>
        <h1 className="font-serif text-3xl">{ERROR_TITLES[state.error.code] ?? "Something went wrong"}</h1>
        <p className="text-muted">{state.error.message}</p>
        <HandleSearch initial={`@${handle}`} />
        <Link href="/" className="inline-block font-mono text-xs text-muted hover:text-fg">
          ← Back home
        </Link>
      </div>
    );
  }

  const { data, version } = state;
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="max-w-md flex-1">
          <HandleSearch compact />
        </div>
        <div className="flex items-center gap-3 font-mono text-xs text-faint">
          {data.from_cache && <span>⚡ cached</span>}
          <button
            onClick={refresh}
            disabled={refreshing}
            className="rounded-md border border-line px-3 py-2 text-muted hover:text-fg disabled:opacity-50"
          >
            {refreshing ? "Refreshing…" : "↻ Refresh data"}
          </button>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-[1fr_1.2fr]">
        <div className="space-y-8">
          <ProfileCard profile={data.profile} />
          <TweetInsights insights={data.profile.insights} />
        </div>
        <div className="lg:sticky lg:top-6 lg:self-start">
          <ChatPanel
            key={`${handle}-${version}`}
            handle={data.profile.handle}
            starter={data.starter_message}
            suggestions={data.suggested_questions}
          />
        </div>
      </div>
    </div>
  );
}

export function ProfileSkeleton() {
  const [slow, setSlow] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setSlow(true), 6000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="grid animate-pulse gap-8 lg:grid-cols-[1fr_1.2fr]" aria-busy="true" aria-label="Loading profile">
      <div className="space-y-5">
        <div className="flex gap-4">
          <div className="size-20 rounded-full bg-surface-2" />
          <div className="flex-1 space-y-3 pt-2">
            <div className="h-7 w-1/2 rounded bg-surface-2" />
            <div className="h-4 w-1/3 rounded bg-surface-2" />
          </div>
        </div>
        <div className="h-16 rounded bg-surface-2" />
        <div className="grid grid-cols-3 gap-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-16 rounded-lg bg-surface-2" />
          ))}
        </div>
        <p className="font-mono text-xs text-faint" aria-live="polite">
          {slow
            ? "Waking up the server — the free-tier backend sleeps when idle, so this can take up to ~30s…"
            : "Fetching profile and recent tweets…"}
        </p>
      </div>
      <div className="h-[70vh] min-h-[480px] rounded-xl bg-surface-2/60" />
    </div>
  );
}
