import { HandleSearch } from "@/components/HandleSearch";

const FEATURES = [
  { icon: "𝕏", title: "Live X profiles", desc: "Bio, stats, and ~100 recent original tweets fetched and cached for 24 hours." },
  { icon: "◎", title: "Semantic search", desc: "Tweets are embedded into pgvector, so each question pulls the most relevant posts." },
  { icon: "◈", title: "Streaming AI chat", desc: "Grounded answers streamed token by token from Groq, quoting real tweets." },
];

const STEPS = [
  { title: "Enter a handle", desc: "Type @username or paste an x.com profile URL." },
  { title: "Review the profile", desc: "See stats, top tweets by likes and views, and engagement averages." },
  { title: "Ask anything", desc: "Chat about their ideas, themes, and best-performing posts." },
];

const EXAMPLES = ["naval", "paulg", "karpathy"];

export default function Home() {
  return (
    <div className="space-y-20">
      <section className="max-w-3xl space-y-6 pt-6">
        <p className="flex items-center gap-2 font-mono text-xs uppercase tracking-[0.2em] text-accent">
          <span className="size-1.5 rounded-full bg-accent" /> Public profile intelligence
        </p>
        <h1 className="font-serif text-5xl leading-[1.05] text-[#f5f5ff] sm:text-6xl">
          Explore anyone&apos;s <em className="text-accent">digital footprint.</em>
        </h1>
        <p className="max-w-xl text-lg font-light text-muted">
          Traceify loads a public X profile and its recent tweets, then lets you have a grounded AI conversation about
          the person.
        </p>
        <div className="max-w-xl">
          <HandleSearch />
        </div>
        <p className="font-mono text-xs text-faint">
          Try:{" "}
          {EXAMPLES.map((h, i) => (
            <span key={h}>
              <a href={`/x/${h}`} className="text-muted underline-offset-4 hover:text-accent hover:underline">
                @{h}
              </a>
              {i < EXAMPLES.length - 1 && " · "}
            </span>
          ))}
        </p>
      </section>

      <section aria-labelledby="features" className="space-y-5">
        <h2 id="features" className="font-mono text-xs uppercase tracking-[0.15em] text-faint">
          What it does
        </h2>
        <div className="grid gap-4 md:grid-cols-3">
          {FEATURES.map((f) => (
            <div key={f.title} className="rounded-xl border border-line bg-surface/60 p-5">
              <div className="font-serif text-2xl text-accent">{f.icon}</div>
              <h3 className="mt-3 font-medium text-[#f5f5ff]">{f.title}</h3>
              <p className="mt-1 text-sm text-muted">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section aria-labelledby="how" className="space-y-5">
        <h2 id="how" className="font-mono text-xs uppercase tracking-[0.15em] text-faint">
          How to use
        </h2>
        <ol className="grid gap-4 md:grid-cols-3">
          {STEPS.map((s, i) => (
            <li key={s.title} className="flex gap-4">
              <span className="font-mono text-sm text-accent">{String(i + 1).padStart(2, "0")}</span>
              <div>
                <h3 className="font-medium text-[#f5f5ff]">{s.title}</h3>
                <p className="mt-1 text-sm text-muted">{s.desc}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
