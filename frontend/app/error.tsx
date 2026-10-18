"use client";

import { CircleAlert, RotateCw } from "lucide-react";
import Link from "next/link";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";

export default function Error({ error, retry }: { error: Error & { digest?: string }; retry: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="relative flex flex-1 flex-col items-center justify-center overflow-hidden px-4 py-24 text-center md:py-32">
      <div aria-hidden className="bg-dots absolute inset-0 [mask-image:radial-gradient(ellipse_50%_50%_at_50%_45%,#000_10%,transparent_75%)]" />
      <div className="relative flex max-w-md flex-col items-center">
        <div className="animate-enter grid size-12 place-items-center rounded-xl border bg-surface text-muted-foreground">
          <CircleAlert aria-hidden className="size-5" strokeWidth={1.75} />
        </div>
        <h1 className="animate-enter mt-6 text-2xl font-semibold tracking-[-0.03em] [--delay:60ms] md:text-3xl">
          Something went wrong
        </h1>
        <p className="animate-enter mt-2 text-pretty text-muted-foreground [--delay:120ms]">
          An unexpected error interrupted this page. Try again, or head back home.
        </p>
        <div className="animate-enter mt-8 flex flex-wrap justify-center gap-2 [--delay:180ms]">
          <Button onClick={() => retry()} className="h-9 rounded-full px-4 hover:bg-primary/85 active:scale-[0.97]">
            <RotateCw aria-hidden />
            Try again
          </Button>
          <Button asChild variant="ghost" className="h-9 rounded-full px-4 text-muted-foreground">
            <Link href="/">Back home</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
