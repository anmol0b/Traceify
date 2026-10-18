"use client";

import { Eye, Heart } from "lucide-react";
import { motion } from "motion/react";
import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { formatCount } from "@/lib/api";
import type { TweetInsights as Insights, TweetStat } from "@/lib/types";
import { cn } from "@/lib/utils";

const SORTS = [
  { key: "likes", label: "Likes", icon: Heart },
  { key: "views", label: "Views", icon: Eye },
] as const;

type Sort = (typeof SORTS)[number]["key"];

function TweetList({ tweets, sort }: { tweets: TweetStat[]; sort: Sort }) {
  return (
    <ol className="divide-y">
      {tweets.map((t, i) => (
        <motion.li
          key={i}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: i * 0.04, ease: [0.16, 1, 0.3, 1] }}
          className="flex gap-4 px-4 py-5 transition-colors duration-150 hover:bg-surface md:px-8"
        >
          <span aria-hidden className="w-5 shrink-0 pt-0.5 font-mono text-xs text-subtle-foreground tabular-nums">
            {String(i + 1).padStart(2, "0")}
          </span>
          <div className="min-w-0 flex-1">
            <p className="line-clamp-4 text-[15px] leading-relaxed whitespace-pre-line text-foreground/90">{t.text}</p>
            <div className="mt-3 flex items-center gap-5 text-[13px] text-subtle-foreground">
              <span className={cn("inline-flex items-center gap-1.5", sort === "likes" && "text-foreground")}>
                <Heart aria-hidden className="size-3.5" />
                <span className="tabular-nums">{formatCount(t.likes)}</span>
                <span className="sr-only">likes</span>
              </span>
              <span className={cn("inline-flex items-center gap-1.5", sort === "views" && "text-foreground")}>
                <Eye aria-hidden className="size-3.5" />
                <span className="tabular-nums">{formatCount(t.views)}</span>
                <span className="sr-only">views</span>
              </span>
            </div>
          </div>
        </motion.li>
      ))}
    </ol>
  );
}

export function TweetInsights({ insights }: { insights: Insights }) {
  const [sort, setSort] = useState<Sort>("likes");
  if (!insights.total_analyzed) return null;

  return (
    <section aria-labelledby="top-tweets">
      <Tabs value={sort} onValueChange={(v) => setSort(v as Sort)} className="gap-0">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b px-4 py-4 md:px-8">
          <div>
            <h2 id="top-tweets" className="text-[15px] font-medium text-foreground">
              Top tweets
            </h2>
            <p className="mt-0.5 text-[13px] text-muted-foreground">
              {insights.total_analyzed} analyzed · avg {formatCount(insights.avg_likes)} likes ·{" "}
              {formatCount(insights.avg_views)} views
            </p>
          </div>
          <TabsList aria-label="Sort tweets by" className="rounded-full border bg-surface p-1 group-data-horizontal/tabs:h-9">
            {SORTS.map(({ key, label, icon: Icon }) => (
              <TabsTrigger
                key={key}
                value={key}
                className="rounded-full px-3 text-[13px] group-data-[variant=default]/tabs-list:data-active:shadow-none data-active:bg-transparent dark:data-active:border-transparent dark:data-active:bg-transparent"
              >
                {sort === key && (
                  <motion.span
                    layoutId="tweet-sort-indicator"
                    className="absolute inset-0 rounded-full bg-secondary ring-1 ring-input"
                    transition={{ type: "spring", bounce: 0.15, duration: 0.4 }}
                  />
                )}
                <span className="relative inline-flex items-center gap-1.5">
                  <Icon aria-hidden className="size-3.5" />
                  {label}
                </span>
              </TabsTrigger>
            ))}
          </TabsList>
        </div>
        {SORTS.map(({ key }) => (
          <TabsContent key={key} value={key}>
            <TweetList tweets={key === "likes" ? insights.top_by_likes : insights.top_by_views} sort={key} />
          </TabsContent>
        ))}
      </Tabs>
    </section>
  );
}
