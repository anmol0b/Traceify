import Link from "next/link";
import { GitHubIcon, LogoMark, REPO_URL, Wordmark } from "@/components/Brand";
import { Button } from "@/components/ui/button";
import { TextHoverEffect } from "@/components/ui/text-hover-effect";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 md:px-6">
        <div className="flex items-center gap-8">
          <Wordmark />
          <nav aria-label="Main" className="hidden items-center gap-6 text-sm text-muted-foreground sm:flex">
            <Link href="/#how-it-works" className="rounded-sm transition-colors duration-150 outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring">
              How it works
            </Link>
            <Link href="/#stack" className="rounded-sm transition-colors duration-150 outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring">
              Stack
            </Link>
          </nav>
        </div>
        <div className="flex items-center gap-2">
          <Button asChild variant="outline" className="h-9 rounded-full border-input bg-transparent px-3.5 dark:bg-transparent">
            <a href={REPO_URL} target="_blank" rel="noreferrer" aria-label="Traceify on GitHub">
              <GitHubIcon />
              <span className="hidden sm:inline">GitHub</span>
            </a>
          </Button>
          <Button asChild className="h-9 rounded-full px-4 hover:bg-primary/85 active:scale-[0.97]">
            <Link href="/#trace">Trace a profile</Link>
          </Button>
        </div>
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="border-t">
      <div className="mx-auto max-w-6xl md:border-x">
        <div className="flex flex-col gap-6 px-4 pt-10 sm:flex-row sm:items-start sm:justify-between md:px-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-[15px] font-semibold tracking-[-0.02em]">
              <LogoMark />
              Traceify
            </div>
            <p className="max-w-xs text-sm text-muted-foreground">
              Public profile intelligence for X. Load a profile, then ask it anything.
            </p>
          </div>
          <nav aria-label="Footer" className="flex gap-6 text-sm text-muted-foreground">
            <a href={REPO_URL} target="_blank" rel="noreferrer" className="transition-colors duration-150 hover:text-foreground">
              Source
            </a>
            <a href={`${REPO_URL}/issues`} target="_blank" rel="noreferrer" className="transition-colors duration-150 hover:text-foreground">
              Issues
            </a>
            <a href={`${REPO_URL}/blob/main/LICENSE`} target="_blank" rel="noreferrer" className="transition-colors duration-150 hover:text-foreground">
              MIT License
            </a>
          </nav>
        </div>
        <div aria-hidden className="-mb-4 h-32 px-2 sm:h-48 md:-mb-8 md:h-64">
          <TextHoverEffect text="TRACEIFY" />
        </div>
        <div className="flex flex-col gap-1 border-t px-4 py-4 text-xs text-subtle-foreground sm:flex-row sm:justify-between md:px-6">
          <p>Public data only.</p>
          <p>Built with FastAPI, Next.js, Neon pgvector &amp; Groq</p>
        </div>
      </div>
    </footer>
  );
}
