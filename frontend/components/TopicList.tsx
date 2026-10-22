import type { Topic } from "@/lib/types";

/** What the person tweets about, from clustering their recent tweets. */
export function TopicList({ topics }: { topics: Topic[] }) {
  if (!topics.length) return null;

  return (
    <section aria-labelledby="topics" className="border-b px-4 py-5 md:px-8">
      <h2 id="topics" className="text-[15px] font-medium text-foreground">
        Topics
      </h2>
      <p className="mt-0.5 text-[13px] text-muted-foreground">Share of recent tweets, grouped by meaning</p>
      <ul className="mt-4 space-y-3">
        {topics.map((topic) => (
          <li key={topic.label} className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-3 gap-y-1.5">
            <span className="truncate text-sm text-foreground/90">{topic.label}</span>
            <span className="font-mono text-xs text-subtle-foreground tabular-nums">{Math.round(topic.share * 100)}%</span>
            <div aria-hidden className="col-span-2 h-1 overflow-hidden rounded-full bg-secondary">
              <div className="h-full rounded-full bg-foreground/70" style={{ width: `${Math.max(topic.share * 100, 2)}%` }} />
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
