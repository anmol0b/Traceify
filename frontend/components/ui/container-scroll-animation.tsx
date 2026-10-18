"use client";
import React, { useRef } from "react";
import { motion, useReducedMotion, useScroll, useTransform } from "motion/react";
import { cn } from "@/lib/utils";

/**
 * Aceternity UI "Container Scroll Animation", adapted: no title slot, a compact height,
 * a monochrome frame, and a flat card when the user prefers reduced motion.
 * The card starts tilted back and settles flat as it scrolls into the middle of the viewport.
 */
export const ContainerScroll = ({ children, className }: { children: React.ReactNode; className?: string }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const reduceMotion = useReducedMotion();
  const { scrollYProgress } = useScroll({ target: containerRef, offset: ["start end", "center center"] });

  const rotateX = useTransform(scrollYProgress, [0, 1], [24, 0]);
  const scale = useTransform(scrollYProgress, [0, 1], [0.92, 1]);
  const y = useTransform(scrollYProgress, [0, 1], [40, 0]);

  return (
    <div ref={containerRef} className={cn("relative [perspective:1200px]", className)}>
      <motion.div
        style={reduceMotion ? undefined : { rotateX, scale, y, transformOrigin: "50% 0%" }}
        className="mx-auto w-full max-w-5xl rounded-[18px] border border-input bg-surface p-1.5 shadow-[0_0_0_1px_#000,0_40px_80px_-30px_#000,0_24px_120px_-40px_#ffffff14] md:p-2"
      >
        <div className="overflow-hidden rounded-xl border bg-background">{children}</div>
      </motion.div>
    </div>
  );
};
