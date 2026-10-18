"use client";

import { ArrowRight, LoaderCircle } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useCallback, useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

type Particle = { x: number; y: number; r: number; color: string };

type Props = {
  placeholders: string[];
  /** Return false to reject the value (no vanish animation, input keeps its text). */
  onSubmit: (value: string) => boolean;
  onValueChange?: (value: string) => void;
  defaultValue?: string;
  size?: "lg" | "sm";
  pending?: boolean;
  invalid?: boolean;
  label: string;
  describedBy?: string;
  className?: string;
};

/**
 * Aceternity UI "Placeholders And Vanish Input", adapted: accessible label, validation
 * before the vanish, a pending state, two sizes, and no particle effect for reduced motion.
 */
export function PlaceholdersAndVanishInput({
  placeholders,
  onSubmit,
  onValueChange,
  defaultValue = "",
  size = "lg",
  pending = false,
  invalid = false,
  label,
  describedBy,
  className,
}: Props) {
  const [currentPlaceholder, setCurrentPlaceholder] = useState(0);
  const [value, setValue] = useState(defaultValue);
  const [animating, setAnimating] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null;
    const start = () => {
      if (!interval) interval = setInterval(() => setCurrentPlaceholder((p) => (p + 1) % placeholders.length), 3000);
    };
    const stop = () => {
      if (interval) clearInterval(interval);
      interval = null;
    };
    const onVisibility = () => (document.visibilityState === "visible" ? start() : stop());
    start();
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      stop();
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [placeholders]);

  const draw = useCallback(() => {
    const input = inputRef.current;
    const ctx = canvasRef.current?.getContext("2d", { willReadFrequently: true });
    if (!input || !ctx || !canvasRef.current) return;
    canvasRef.current.width = 800;
    canvasRef.current.height = 800;
    ctx.clearRect(0, 0, 800, 800);
    const styles = getComputedStyle(input);
    ctx.font = `${parseFloat(styles.fontSize) * 2}px ${styles.fontFamily}`;
    ctx.fillStyle = "#FFF";
    ctx.fillText(input.value, 16, 40);

    const { data } = ctx.getImageData(0, 0, 800, 800);
    const particles: Particle[] = [];
    for (let y = 0; y < 800; y++) {
      for (let x = 0; x < 800; x++) {
        const i = 4 * (y * 800 + x);
        if (data[i] !== 0 && data[i + 1] !== 0 && data[i + 2] !== 0) {
          particles.push({ x, y, r: 1, color: `rgba(${data[i]}, ${data[i + 1]}, ${data[i + 2]}, ${data[i + 3]})` });
        }
      }
    }
    particlesRef.current = particles;
  }, []);

  const vanish = () => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setValue("");
      return;
    }
    setAnimating(true);
    draw();
    const start = particlesRef.current.reduce((max, p) => (p.x > max ? p.x : max), 0);
    const frame = (pos: number) => {
      requestAnimationFrame(() => {
        const next: Particle[] = [];
        for (const p of particlesRef.current) {
          if (p.x < pos) {
            next.push(p);
          } else if (p.r > 0) {
            p.x += Math.random() > 0.5 ? 1 : -1;
            p.y += Math.random() > 0.5 ? 1 : -1;
            p.r -= 0.05 * Math.random();
            next.push(p);
          }
        }
        particlesRef.current = next;
        const ctx = canvasRef.current?.getContext("2d");
        if (ctx) {
          ctx.clearRect(pos, 0, 800, 800);
          for (const p of next) {
            if (p.x > pos) {
              ctx.beginPath();
              ctx.rect(p.x, p.y, p.r, p.r);
              ctx.fillStyle = p.color;
              ctx.strokeStyle = p.color;
              ctx.stroke();
            }
          }
        }
        if (next.length > 0) {
          frame(pos - 8);
        } else {
          setValue("");
          setAnimating(false);
        }
      });
    };
    frame(start);
  };

  const lg = size === "lg";

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (animating || pending) return;
        if (onSubmit(inputRef.current?.value ?? "")) vanish();
      }}
      role="search"
      noValidate
      className={cn(
        "relative w-full overflow-hidden rounded-full border border-input bg-surface shadow-[0_1px_0_0_#ffffff0a_inset,0_8px_24px_-12px_#000] transition-[border-color,box-shadow] duration-150 ease-out focus-within:border-ring/70 focus-within:ring-4 focus-within:ring-ring/15",
        lg ? "h-12" : "h-10",
        invalid && "border-destructive/60 focus-within:border-destructive/70 focus-within:ring-destructive/15",
        className,
      )}
    >
      <canvas
        ref={canvasRef}
        aria-hidden
        className={cn(
          "pointer-events-none absolute origin-top-left scale-50 pr-20",
          lg ? "top-[20%] left-3" : "top-[14%] left-2",
          animating ? "opacity-100" : "opacity-0",
        )}
      />
      <input
        ref={inputRef}
        value={value}
        onChange={(e) => {
          if (animating) return;
          setValue(e.target.value);
          onValueChange?.(e.target.value);
        }}
        type="text"
        aria-label={label}
        aria-invalid={invalid || undefined}
        aria-describedby={describedBy}
        autoComplete="off"
        autoCapitalize="none"
        spellCheck={false}
        enterKeyHint="go"
        className={cn(
          "relative z-10 h-full w-full rounded-full border-none bg-transparent font-mono text-base text-foreground focus:outline-none sm:text-[15px]",
          lg ? "pr-14 pl-5" : "pr-12 pl-4",
          animating && "text-transparent",
        )}
      />

      <button
        type="submit"
        disabled={!value || pending}
        aria-label={pending ? "Loading profile" : "Trace profile"}
        className={cn(
          "absolute top-1/2 right-1.5 z-20 flex -translate-y-1/2 items-center justify-center rounded-full bg-primary text-primary-foreground transition-[background-color,transform,opacity] duration-150 ease-out outline-none hover:bg-primary/85 focus-visible:ring-2 focus-visible:ring-ring active:scale-90 disabled:bg-secondary disabled:text-subtle-foreground",
          lg ? "size-9" : "size-7",
        )}
      >
        {pending ? (
          <LoaderCircle aria-hidden className="size-4 animate-spin" />
        ) : (
          <ArrowRight aria-hidden className="size-4" />
        )}
      </button>

      <div aria-hidden className="pointer-events-none absolute inset-0 flex items-center rounded-full">
        <AnimatePresence mode="wait">
          {!value && (
            <motion.p
              key={`placeholder-${currentPlaceholder}`}
              initial={{ y: 5, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -15, opacity: 0 }}
              transition={{ duration: 0.3, ease: "linear" }}
              className={cn(
                "w-[calc(100%-4rem)] truncate text-left font-mono text-base text-subtle-foreground sm:text-[15px]",
                lg ? "pl-5" : "pl-4",
              )}
            >
              {placeholders[currentPlaceholder]}
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    </form>
  );
}
