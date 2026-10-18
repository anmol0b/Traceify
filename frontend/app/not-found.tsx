import type { Metadata } from "next";
import Link from "next/link";
import { Section } from "@/components/Frame";
import { HandleSearch } from "@/components/HandleSearch";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Page not found — Traceify",
};

export default function NotFound() {
  return (
    <Section className="flex flex-1 overflow-hidden">
      <div aria-hidden className="bg-dots fade-mask-radial absolute inset-0" />
      <div
        aria-hidden
        className="animate-enter pointer-events-none absolute -right-6 -bottom-10 hidden text-[13rem] leading-none font-bold tracking-[-0.06em] text-transparent select-none [-webkit-text-stroke:1px_#262626] [--delay:200ms] md:-right-4 md:-bottom-16 md:block md:text-[22rem]"
      >
        404
      </div>
      <div className="relative flex max-w-xl flex-col justify-center px-4 py-20 md:px-12 md:py-32">
        <p className="animate-enter font-mono text-sm text-subtle-foreground">404 · Not found</p>
        <h1 className="mt-4 text-4xl leading-[1.05] font-semibold tracking-[-0.045em] md:text-6xl">
          <span className="line-mask">
            <span className="animate-rise [--delay:60ms]">This page</span>
          </span>
          <span className="line-mask">
            <span className="animate-rise text-muted-foreground [--delay:140ms]">doesn&apos;t exist.</span>
          </span>
        </h1>
        <p className="animate-enter mt-5 text-lg text-pretty text-muted-foreground [--delay:250ms]">
          The link may be broken or the page may have moved. Look up an X profile instead.
        </p>
        <div className="animate-enter mt-8 max-w-md [--delay:330ms]">
          <HandleSearch />
        </div>
        <div className="animate-enter mt-4 [--delay:400ms]">
          <Button asChild variant="ghost" className="h-9 rounded-full px-4 text-muted-foreground">
            <Link href="/">Back home</Link>
          </Button>
        </div>
      </div>
    </Section>
  );
}
