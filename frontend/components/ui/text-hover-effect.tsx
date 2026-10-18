"use client";
import React, { useId, useRef, useState } from "react";
import { motion } from "motion/react";

/**
 * Aceternity UI "Text Hover Effect", adapted: a monochrome reveal,
 * a wider viewBox for longer words, and the outline wipes in from the left when scrolled into view.
 */
export const TextHoverEffect = ({
  text,
  duration,
}: {
  text: string;
  duration?: number;
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hovered, setHovered] = useState(false);
  const [maskPosition, setMaskPosition] = useState({ cx: "50%", cy: "50%" });
  const id = useId().replace(/:/g, "");

  const textProps = {
    x: "50%",
    y: "54%",
    textAnchor: "middle",
    dominantBaseline: "middle",
    strokeWidth: 0.7,
    // A static system face: variable fonts like Geist keep overlapping contours that show up when stroked.
    style: { fontSize: 104, letterSpacing: "-0.01em", fontFamily: "Helvetica, Arial, sans-serif" },
    className: "fill-transparent font-bold",
  } as const;

  return (
    <motion.svg
      ref={svgRef}
      initial={{ clipPath: "inset(0 100% 0 0)" }}
      whileInView={{ clipPath: "inset(0 0% 0 0)" }}
      viewport={{ once: true }}
      transition={{ duration: 1.8, ease: [0.65, 0, 0.35, 1] }}
      width="100%"
      height="100%"
      viewBox="0 0 620 120"
      preserveAspectRatio="xMidYMid meet"
      xmlns="http://www.w3.org/2000/svg"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onMouseMove={(e) => {
        const rect = svgRef.current?.getBoundingClientRect();
        if (!rect) return;
        setMaskPosition({
          cx: `${((e.clientX - rect.left) / rect.width) * 100}%`,
          cy: `${((e.clientY - rect.top) / rect.height) * 100}%`,
        });
      }}
      className="select-none"
    >
      <defs>
        <linearGradient id={`${id}-gradient`} gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="620" y2="0">
          <stop offset="0%" stopColor="#ededed" />
          <stop offset="45%" stopColor="#a1a1a1" />
          <stop offset="70%" stopColor="#52a8ff" />
          <stop offset="100%" stopColor="#ededed" />
        </linearGradient>
        <motion.radialGradient
          id={`${id}-reveal`}
          gradientUnits="userSpaceOnUse"
          r="22%"
          initial={{ cx: "50%", cy: "50%" }}
          animate={maskPosition}
          transition={{ duration: duration ?? 0, ease: "easeOut" }}
        >
          <stop offset="0%" stopColor="white" />
          <stop offset="100%" stopColor="black" />
        </motion.radialGradient>
        <mask id={`${id}-mask`}>
          <rect x="0" y="0" width="100%" height="100%" fill={`url(#${id}-reveal)`} />
        </mask>
      </defs>
      <text
        {...textProps}
        className={`${textProps.className} stroke-[#2e2e2e] transition-opacity duration-300`}
        style={{ ...textProps.style, opacity: hovered ? 0.8 : 0 }}
      >
        {text}
      </text>
      <text {...textProps} className={`${textProps.className} stroke-[#333]`}>
        {text}
      </text>
      <text {...textProps} stroke={`url(#${id}-gradient)`} mask={`url(#${id}-mask)`} style={{ ...textProps.style, opacity: hovered ? 1 : 0 }}>
        {text}
      </text>
    </motion.svg>
  );
};
