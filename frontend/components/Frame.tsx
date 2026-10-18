import { cn } from "@/lib/utils";

/** The small "+" drawn where the page frame meets a section divider. */
export function Crosshair({ className }: { className?: string }) {
  return (
    <svg
      aria-hidden
      viewBox="0 0 11 11"
      className={cn("pointer-events-none absolute z-10 hidden size-[11px] text-[#4d4d4d] md:block", className)}
    >
      <path d="M5.5 0v11M0 5.5h11" stroke="currentColor" />
    </svg>
  );
}

/** A full-width band of the framed page, closed off with a bottom rule and corner crosshairs. */
export function Section({ className, children, ...props }: React.ComponentProps<"section">) {
  return (
    <section className={cn("relative border-b", className)} {...props}>
      {children}
      <Crosshair className="-bottom-[5px] -left-[6px]" />
      <Crosshair className="-right-[6px] -bottom-[5px]" />
    </section>
  );
}
