"use client";

import { useRouter } from "next/navigation";
import { useId, useState, useTransition } from "react";
import { PlaceholdersAndVanishInput } from "@/components/ui/placeholders-and-vanish-input";
import { normalizeHandle } from "@/lib/handle";
import { cn } from "@/lib/utils";

const PLACEHOLDERS = ["@naval", "x.com/paulg", "@karpathy", "twitter.com/sama"];

type Props = { initial?: string; compact?: boolean; className?: string };

export function HandleSearch({ initial = "", compact = false, className }: Props) {
  const router = useRouter();
  const errorId = useId();
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function submit(raw: string) {
    const handle = normalizeHandle(raw);
    if (!handle) {
      setError("Enter a handle like @naval or a URL like x.com/naval.");
      return false;
    }
    setError(null);
    startTransition(() => router.push(`/x/${handle}`));
    return true;
  }

  return (
    <div className={cn("w-full", className)}>
      <PlaceholdersAndVanishInput
        placeholders={PLACEHOLDERS}
        defaultValue={initial}
        onSubmit={submit}
        onValueChange={() => error && setError(null)}
        size={compact ? "sm" : "lg"}
        pending={pending}
        invalid={!!error}
        label="X handle or profile URL"
        describedBy={error ? errorId : undefined}
      />
      {error && (
        <p id={errorId} role="alert" className="animate-enter mt-2 px-5 text-left text-sm text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}
