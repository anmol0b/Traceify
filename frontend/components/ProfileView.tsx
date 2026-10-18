"use client";

import {
  ArrowLeft,
  AtSign,
  Check,
  CircleAlert,
  Hourglass,
  LoaderCircle,
  Lock,
  RefreshCw,
  RotateCw,
  Timer,
  UserX,
  WifiOff,
  Zap,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
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

const ERRORS: Record<string, { title: string; icon: LucideIcon }> = {
  not_found: { title: "Account not found", icon: UserX },
  private_account: { title: "This account is private", icon: Lock },
  invalid_handle: { title: "That doesn't look like an X handle", icon: AtSign },
  rate_limited: { title: "Slow down a little", icon: Timer },
  upstream_rate_limited: { title: "The data provider is busy", icon: Hourglass },
  network: { title: "Can't reach the API", icon: WifiOff },
};

/** Errors where trying the same handle again can't succeed. */
const NOT_RETRYABLE = new Set(["not_found", "private_account", "invalid_handle"]);

const COLUMNS = "grid flex-1 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)]";
const CHAT_PANEL = "h-[80dvh] min-h-[520px] lg:sticky lg:top-16 lg:h-[calc(100dvh-4rem)] lg:min-h-0";

function toApiError(err: unknown) {
  return err instanceof ApiError ? err : new ApiError(0, "error", String(err));
}

function Toolbar({ children }: { children?: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-3 border-b px-4 py-3 sm:flex-row sm:items-center sm:justify-between md:px-6">
      <div className="flex min-w-0 items-center gap-2 sm:w-full sm:max-w-md">
        <Button asChild variant="ghost" size="icon" className="size-10 shrink-0 rounded-full text-muted-foreground">
          <Link href="/" aria-label="Back home">
            <ArrowLeft aria-hidden />
          </Link>
        </Button>
        <HandleSearch compact />
      </div>
      <div className="flex items-center gap-2 self-end sm:self-auto">{children}</div>
    </div>
  );
}

export function ProfileView({ handle }: { handle: string }) {
  const [state, setState] = useState<State>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const [refresh, setRefresh] = useState<"idle" | "loading" | "done">("idle");
  const doneTimer = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    const controller = new AbortController();
    getProfile(handle, controller.signal)
      .then((data) => setState({ status: "ready", data, version: 0 }))
      .catch((err) => {
        if (controller.signal.aborted) return;
        setState({ status: "error", error: toApiError(err) });
      });
    return () => controller.abort();
  }, [handle, attempt]);

  useEffect(() => () => clearTimeout(doneTimer.current), []);

  function retry() {
    setState({ status: "loading" });
    setAttempt((n) => n + 1);
  }

  async function refreshData() {
    setRefresh("loading");
    try {
      const data = await refreshProfile(handle);
      setState((prev) => ({ status: "ready", data, version: prev.status === "ready" ? prev.version + 1 : 0 }));
      setRefresh("done");
      doneTimer.current = setTimeout(() => setRefresh("idle"), 2000);
    } catch (err) {
      setRefresh("idle");
      setState({ status: "error", error: toApiError(err) });
    }
  }

  if (state.status === "loading") return <ProfileSkeleton />;

  if (state.status === "error") {
    const { title, icon: Icon } = ERRORS[state.error.code] ?? { title: "Something went wrong", icon: CircleAlert };
    return (
      <div className="relative flex flex-1 flex-col items-center justify-center overflow-hidden px-4 py-20 text-center md:py-28">
        <div aria-hidden className="bg-dots absolute inset-0 [mask-image:radial-gradient(ellipse_50%_50%_at_50%_45%,#000_10%,transparent_75%)]" />
        <div className="relative flex w-full max-w-md flex-col items-center">
          <div className="animate-enter grid size-12 place-items-center rounded-xl border bg-surface text-muted-foreground">
            <Icon aria-hidden className="size-5" strokeWidth={1.75} />
          </div>
          <h1 className="animate-enter mt-6 text-2xl font-semibold tracking-[-0.03em] text-balance [--delay:60ms] md:text-3xl">
            {title}
          </h1>
          <p className="animate-enter mt-2 text-pretty text-muted-foreground [--delay:120ms]">{state.error.message}</p>
          <div className="animate-enter mt-8 w-full [--delay:180ms]">
            <HandleSearch initial={`@${handle}`} />
          </div>
          <div className="animate-enter mt-4 flex flex-wrap justify-center gap-2 [--delay:240ms]">
            {!NOT_RETRYABLE.has(state.error.code) && (
              <Button onClick={retry} className="h-9 rounded-full px-4 hover:bg-primary/85 active:scale-[0.97]">
                <RotateCw aria-hidden />
                Try again
              </Button>
            )}
            <Button asChild variant="ghost" className="h-9 rounded-full px-4 text-muted-foreground">
              <Link href="/">Back home</Link>
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const { data, version } = state;
  return (
    <div className="flex flex-1 flex-col">
      <Toolbar>
        {data.from_cache && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Badge variant="outline" tabIndex={0} className="h-7 cursor-default gap-1 rounded-full border-input px-2.5 text-[13px] text-muted-foreground">
                <Zap aria-hidden />
                Cached
              </Badge>
            </TooltipTrigger>
            <TooltipContent>Served from the 24-hour cache</TooltipContent>
          </Tooltip>
        )}
        <Button
          variant="outline"
          onClick={refreshData}
          disabled={refresh !== "idle"}
          aria-busy={refresh === "loading" || undefined}
          className="h-9 min-w-28 rounded-full border-input bg-transparent px-3.5 disabled:opacity-100 dark:bg-transparent"
        >
          {refresh === "loading" ? (
            <LoaderCircle aria-hidden className="animate-spin" />
          ) : refresh === "done" ? (
            <Check aria-hidden className="animate-enter text-success" />
          ) : (
            <RefreshCw aria-hidden />
          )}
          <span aria-live="polite">{refresh === "loading" ? "Refreshing" : refresh === "done" ? "Updated" : "Refresh"}</span>
        </Button>
      </Toolbar>

      <div className={COLUMNS}>
        <div className="animate-enter min-w-0 lg:border-r">
          <ProfileCard profile={data.profile} />
          <TweetInsights insights={data.profile.insights} />
        </div>
        <div className="animate-enter border-t [--delay:100ms] lg:border-t-0">
          <div className={CHAT_PANEL}>
            <ChatPanel
              key={`${handle}-${version}`}
              handle={data.profile.handle}
              starter={data.starter_message}
              suggestions={data.suggested_questions}
            />
          </div>
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
    <div className="flex flex-1 flex-col">
      <Toolbar>
        <Skeleton className="h-9 w-28 rounded-full" />
      </Toolbar>

      <div className={COLUMNS} aria-busy="true" aria-label="Loading profile">
        <div className="min-w-0 lg:border-r">
          <div className="px-4 py-8 md:px-8">
            <div className="flex items-center gap-4 md:gap-5">
              <Skeleton className="size-16 rounded-full md:size-[72px]" />
              <div className="flex-1 space-y-2.5">
                <Skeleton className="h-7 w-48 max-w-full" />
                <Skeleton className="h-4 w-24" />
              </div>
            </div>
            <div className="mt-6 space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-4/5" />
            </div>
            <p role="status" aria-live="polite" className="mt-6 flex items-start gap-2 text-sm text-muted-foreground">
              <LoaderCircle aria-hidden className="mt-0.5 size-4 shrink-0 animate-spin" />
              <span key={slow ? "slow" : "fast"} className="animate-enter">
                {slow
                  ? "Waking up the server — the free-tier backend sleeps when idle, so this can take up to ~30s…"
                  : "Fetching profile and recent tweets…"}
              </span>
            </p>
          </div>
          <div className="grid grid-cols-3 divide-x border-y">
            {[0, 1, 2].map((i) => (
              <div key={i} className="space-y-2 px-4 py-5 md:px-8">
                <Skeleton className="h-3.5 w-16" />
                <Skeleton className="h-7 w-14" />
              </div>
            ))}
          </div>
          <div className="flex items-center justify-between border-b px-4 py-4 md:px-8">
            <div className="space-y-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-3.5 w-48" />
            </div>
            <Skeleton className="h-9 w-36 rounded-full" />
          </div>
          <div className="divide-y">
            {[0, 1, 2].map((i) => (
              <div key={i} className="flex gap-4 px-4 py-5 md:px-8">
                <Skeleton className="h-3.5 w-5" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/5" />
                  <Skeleton className="mt-3 h-3.5 w-28" />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="border-t lg:border-t-0">
          <div className={`flex flex-col ${CHAT_PANEL}`}>
            <div className="flex h-14 items-center justify-between border-b px-4 md:px-6">
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-4 w-16" />
            </div>
            <div className="flex flex-1 gap-3 px-4 py-6 md:px-6">
              <Skeleton className="size-7 shrink-0 rounded-full" />
              <div className="flex-1 space-y-2 pt-1">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
                <Skeleton className="h-4 w-2/5" />
              </div>
            </div>
            <div className="p-3 md:p-4">
              <Skeleton className="h-12 rounded-xl" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
