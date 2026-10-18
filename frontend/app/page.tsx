import Link from "next/link";
import { Section } from "@/components/Frame";
import { HandleSearch } from "@/components/HandleSearch";
import { Pipeline } from "@/components/home/Pipeline";
import { ProductPreview } from "@/components/home/ProductPreview";

const FACTS = [
  { value: "~100", label: "recent tweets read per profile" },
  { value: "384-d", label: "embeddings searched with pgvector" },
  { value: "24h", label: "cache before a profile is refetched" },
];

const EXAMPLES = ["naval", "paulg", "karpathy"];

const STACK = ["Next.js", "FastAPI", "Neon Postgres", "pgvector", "fastembed", "Groq"];

export default function Home() {
  return (
    <>
      <Section id="trace" className="scroll-mt-16 overflow-hidden">
        <div aria-hidden className="bg-dots fade-mask-radial absolute inset-0" />
        <div className="relative grid gap-12 px-4 pt-16 pb-14 md:px-12 md:pt-28 md:pb-20 lg:grid-cols-[minmax(0,1fr)_15rem] lg:items-end">
          <div className="max-w-2xl">
            <h1 className="text-[2.75rem] leading-[1.02] font-semibold tracking-[-0.05em] sm:text-6xl md:text-[4.5rem]">
              <span className="line-mask">
                <span className="animate-rise">Explore anyone&apos;s</span>
              </span>
              <span className="line-mask">
                <span className="animate-rise text-muted-foreground [--delay:90ms]">digital footprint.</span>
              </span>
            </h1>
            <p className="animate-enter mt-6 max-w-lg text-lg leading-relaxed text-pretty text-muted-foreground [--delay:250ms]">
              Traceify loads a public X profile and its recent tweets, then lets you have a grounded AI conversation
              about the person.
            </p>
            <div className="animate-enter mt-10 max-w-md [--delay:350ms]">
              <HandleSearch />
            </div>
            <p className="animate-enter mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 pl-5 text-sm text-subtle-foreground [--delay:450ms]">
              Try
              {EXAMPLES.map((h) => (
                <Link
                  key={h}
                  href={`/x/${h}`}
                  className="rounded-sm py-1 font-mono text-muted-foreground underline decoration-[#333] underline-offset-4 transition-colors duration-150 outline-none hover:text-foreground hover:decoration-foreground focus-visible:ring-2 focus-visible:ring-ring"
                >
                  @{h}
                </Link>
              ))}
            </p>
          </div>

          <dl className="animate-enter grid grid-cols-3 gap-4 border-t pt-6 [--delay:550ms] lg:grid-cols-1 lg:gap-0 lg:divide-y lg:border-t-0 lg:pt-0">
            {FACTS.map((f) => (
              <div key={f.value} className="flex flex-col lg:py-4 lg:last:pb-0">
                <dt className="text-xs leading-snug text-muted-foreground md:text-sm">{f.label}</dt>
                <dd className="order-first text-2xl font-semibold tracking-[-0.04em] text-foreground md:text-3xl">{f.value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </Section>

      <Section aria-label="Product preview" className="overflow-hidden">
        <ProductPreview />
      </Section>

      <Section id="how-it-works" aria-labelledby="how-it-works-title" className="scroll-mt-16">
        <div className="px-4 py-16 md:px-12 md:py-24">
          <h2 id="how-it-works-title" className="max-w-3xl text-3xl leading-[1.1] font-semibold tracking-[-0.04em] text-balance md:text-[2.75rem]">
            From a handle to a grounded answer.{" "}
            <span className="text-muted-foreground">
              Every question is matched against the person&apos;s own tweets before a reply is written.
            </span>
          </h2>
        </div>
        <Pipeline />
      </Section>

      <Section id="stack" aria-labelledby="stack-title" className="scroll-mt-16">
        <div className="grid md:grid-cols-[14rem_minmax(0,1fr)]">
          <h2 id="stack-title" className="flex items-center px-4 py-6 text-sm text-muted-foreground md:border-r md:px-12 md:py-0">
            Built with
          </h2>
          <ul className="grid grid-cols-2 gap-px border-t bg-border sm:grid-cols-3 md:border-t-0 lg:grid-cols-6">
            {STACK.map((name) => (
              <li
                key={name}
                className="grid h-20 place-items-center bg-background px-3 text-center text-[15px] font-medium tracking-[-0.01em] text-muted-foreground transition-colors duration-150 hover:text-foreground"
              >
                {name}
              </li>
            ))}
          </ul>
        </div>
      </Section>
    </>
  );
}
