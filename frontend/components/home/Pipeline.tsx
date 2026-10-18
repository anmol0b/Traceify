"use client";

import { motion, type Variants } from "motion/react";
import { LogoMark } from "@/components/Brand";

const EASE = [0.16, 1, 0.3, 1] as const;

const list: Variants = { hidden: {}, show: { transition: { staggerChildren: 0.12, delayChildren: 0.1 } } };
const item: Variants = {
  hidden: { opacity: 0, y: 6 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: EASE } },
};

function FetchVisual() {
  const rows: [string, string][] = [
    ["profile", "saved"],
    ["tweets", "100"],
    ["retweets, replies", "skipped"],
    ["cache", "24h"],
  ];
  return (
    <motion.div variants={list} className="w-full max-w-60 font-mono text-[11px] leading-6">
      <motion.p variants={item} className="text-foreground">
        GET /api/profiles/naval
      </motion.p>
      <motion.p variants={item} className="flex items-center gap-1.5 text-muted-foreground">
        <span aria-hidden className="size-1.5 rounded-full bg-success" /> 200 OK
      </motion.p>
      {rows.map(([k, v]) => (
        <motion.p key={k} variants={item} className="flex gap-2 text-subtle-foreground">
          <span>{k}</span>
          <span aria-hidden className="flex-1 translate-y-[-3px] border-b border-dotted border-[#333]" />
          <span className="text-muted-foreground">{v}</span>
        </motion.p>
      ))}
    </motion.div>
  );
}

function EmbedVisual() {
  const cols = 18;
  const rows = 7;
  return (
    <motion.div variants={item} className="flex flex-col items-center gap-4">
      <div aria-hidden className="grid gap-[5px]" style={{ gridTemplateColumns: `repeat(${cols}, 4px)` }}>
        {Array.from({ length: cols * rows }, (_, i) => {
          const col = i % cols;
          const row = Math.floor(i / cols);
          return (
            <span
              key={i}
              className="animate-wave size-1 rounded-[1px] bg-foreground"
              style={{ "--delay": `${col * 90 + row * 60}ms` } as React.CSSProperties}
            />
          );
        })}
      </div>
      <p className="font-mono text-[11px] text-subtle-foreground">bge-small-en-v1.5 · 384 dims</p>
    </motion.div>
  );
}

function RetrieveVisual() {
  const matches = [
    { id: "tweet 14", score: 0.82 },
    { id: "tweet 03", score: 0.77 },
    { id: "tweet 57", score: 0.71 },
  ];
  return (
    <motion.div variants={list} className="w-full max-w-60 space-y-3 font-mono text-[11px]">
      <motion.p variants={item} className="inline-flex rounded-md border border-input bg-background px-2 py-1 text-muted-foreground">
        q: &ldquo;views on startups&rdquo;
      </motion.p>
      {matches.map((m) => (
        <motion.div key={m.id} variants={item} className="flex items-center gap-3">
          <span className="w-14 shrink-0 text-subtle-foreground">{m.id}</span>
          <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-[#1f1f1f]">
            <motion.span
              className="block h-full origin-left rounded-full bg-foreground"
              style={{ width: `${m.score * 100}%` }}
              variants={{ hidden: { scaleX: 0 }, show: { scaleX: 1, transition: { duration: 0.9, ease: EASE } } }}
            />
          </span>
          <span className="w-8 text-right text-muted-foreground tabular-nums">{m.score.toFixed(2)}</span>
        </motion.div>
      ))}
    </motion.div>
  );
}

function AnswerVisual() {
  const lines = ["100%", "92%", "64%"];
  return (
    <motion.div variants={list} className="w-full max-w-60 space-y-3">
      <motion.div variants={item} className="ml-auto w-fit rounded-xl rounded-br-sm bg-secondary px-3 py-1.5 text-[11px] text-foreground">
        What do they write about most?
      </motion.div>
      <motion.div variants={item} className="flex gap-2">
        <span className="grid size-5 shrink-0 place-items-center rounded-full border bg-background">
          <LogoMark className="size-2.5" />
        </span>
        <div className="flex-1 space-y-0.5 pt-0.5">
          {lines.map((w, i) => (
            <div key={i} className="flex h-3 items-center gap-1" style={{ width: w }}>
              <motion.span
                className="block h-1.5 flex-1 origin-left rounded-full bg-[#333]"
                variants={{
                  hidden: { scaleX: 0 },
                  show: { scaleX: 1, transition: { duration: 0.6, delay: 0.5 + i * 0.35, ease: "linear" } },
                }}
              />
              {i === lines.length - 1 && <span aria-hidden className="animate-blink h-3 w-px shrink-0 bg-foreground" />}
            </div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}

const STEPS = [
  {
    title: "Fetch",
    desc: "The profile and about 100 recent original tweets are pulled from X, with retweets and replies left out, then cached for 24 hours.",
    visual: FetchVisual,
  },
  {
    title: "Embed",
    desc: "Each tweet becomes a 384-dimension vector and is stored in Neon Postgres with pgvector.",
    visual: EmbedVisual,
  },
  {
    title: "Retrieve",
    desc: "Your question is embedded too, and a cosine search over an HNSW index pulls the tweets that match it best.",
    visual: RetrieveVisual,
  },
  {
    title: "Answer",
    desc: "Groq streams the reply token by token, written from the profile, its engagement stats and the matched tweets.",
    visual: AnswerVisual,
  },
];

export function Pipeline() {
  return (
    <ol className="grid gap-px border-t bg-border sm:grid-cols-2 lg:grid-cols-4">
      {STEPS.map(({ title, desc, visual: Visual }, i) => (
        <motion.li
          key={title}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-80px" }}
          className="flex flex-col bg-background"
        >
          <div className="grid h-48 place-items-center border-b px-6">
            <Visual />
          </div>
          <div className="p-6 md:p-8">
            <p className="font-mono text-xs text-subtle-foreground">0{i + 1}</p>
            <h3 className="mt-3 text-[15px] font-medium text-foreground">{title}</h3>
            <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{desc}</p>
          </div>
        </motion.li>
      ))}
    </ol>
  );
}
