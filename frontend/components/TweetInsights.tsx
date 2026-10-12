"use client";

import { useState } from "react";
import { formatCount } from "@/lib/api";
import type { TweetInsights as Insights } from "@/lib/types";

export function TweetInsights({ insights }: { insights: Insights }) {
  const [sort, setSort] = useState<"likes" | "views">("likes");
  if (!insights.total_analyzed) return null;
  const tweets = sort === "likes" ? insights.top_by_likes : insights.top_by_views;

  return (
    <section aria-label="Tweet insights" className="space-y-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-mono text-xs uppercase tracking-[0.15em] text-faint">
          Top tweets · {insights.total_analyzed} analyzed
        </h2>
        <div role="tablist" className="flex rounded-md border border-line p-0.5 font-mono text-xs">
          {(["likes", "views"] as const).map((key) => (
            <button
              key={key}
              role="tab"
              aria-selected={sort === key}
              onClick={() => setSort(key)}
              className={`rounded px-2 py-1 ${sort === key ? "bg-surface-2 text-fg" : "text-muted hover:text-fg"}`}
            >
              by {key}
            </button>
          ))}
        </div>
      </div>
      <p className="font-mono text-xs text-muted">
        avg {formatCount(insights.avg_likes)} likes · {formatCount(insights.avg_views)} views per tweet
      </p>
      <ol className="space-y-2">
        {tweets.map((t, i) => (
          <li key={`${sort}-${i}`} className="rounded-lg border border-line bg-surface p-3">
            <p className="line-clamp-4 whitespace-pre-line text-sm leading-relaxed text-fg/85">{t.text}</p>
            <p className="mt-2 font-mono text-[0.7rem] text-faint">
              ♥ {formatCount(t.likes)} · 👁 {formatCount(t.views)}
            </p>
          </li>
        ))}
      </ol>
    </section>
  );
}
