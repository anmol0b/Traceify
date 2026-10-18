"use client"

import { useEffect, useRef, type ComponentPropsWithoutRef } from "react"
import { useInView, useMotionValue, useReducedMotion, useSpring } from "motion/react"

import { cn } from "@/lib/utils"

interface NumberTickerProps extends ComponentPropsWithoutRef<"span"> {
  value: number
  startValue?: number
  direction?: "up" | "down"
  delay?: number
  decimalPlaces?: number
  /** Custom formatter for the displayed value (e.g. compact notation). */
  format?: (value: number) => string
}

export function NumberTicker({
  value,
  startValue = 0,
  direction = "up",
  delay = 0,
  className,
  decimalPlaces = 0,
  format,
  ...props
}: NumberTickerProps) {
  const ref = useRef<HTMLSpanElement>(null)
  const reduceMotion = useReducedMotion()
  const motionValue = useMotionValue(direction === "down" ? value : startValue)
  const springValue = useSpring(motionValue, {
    damping: 60,
    stiffness: 100,
  })
  const isInView = useInView(ref, { once: true, margin: "0px" })

  // Subscribe before the effect below so a reduced-motion jump is rendered too.
  useEffect(
    () =>
      springValue.on("change", (latest) => {
        if (ref.current) {
          const rounded = Number(latest.toFixed(decimalPlaces))
          ref.current.textContent = format
            ? format(rounded)
            : Intl.NumberFormat("en-US", {
                minimumFractionDigits: decimalPlaces,
                maximumFractionDigits: decimalPlaces,
              }).format(rounded)
        }
      }),
    [springValue, decimalPlaces, format]
  )

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | null = null
    const target = direction === "down" ? startValue : value

    if (reduceMotion) {
      springValue.jump(target)
    } else if (isInView) {
      timer = setTimeout(() => {
        motionValue.set(target)
      }, delay * 1000)
    }

    return () => {
      if (timer !== null) {
        clearTimeout(timer)
      }
    }
  }, [motionValue, springValue, reduceMotion, isInView, delay, value, direction, startValue])

  return (
    <span
      ref={ref}
      className={cn("inline-block tabular-nums", className)}
      {...props}
    >
      {format ? format(startValue) : startValue}
    </span>
  )
}
