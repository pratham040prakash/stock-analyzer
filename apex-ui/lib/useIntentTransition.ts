"use client";

import { useEffect, useState } from "react";
import type { UserIntent } from "@/types/intent";

type TransitionPhase = "idle" | "out" | "in";

export function useIntentTransition(intent: UserIntent) {
  const [renderIntent, setRenderIntent] = useState(intent);
  const [phase, setPhase] = useState<TransitionPhase>("idle");

  useEffect(() => {
    if (intent === renderIntent) {
      return;
    }

    setPhase("out");
    let enterTimer: number | undefined;

    const exitTimer = window.setTimeout(() => {
      setRenderIntent(intent);
      setPhase("in");
      enterTimer = window.setTimeout(() => {
        setPhase("idle");
      }, 150);
    }, 100);

    return () => {
      window.clearTimeout(exitTimer);
      if (enterTimer !== undefined) {
        window.clearTimeout(enterTimer);
      }
    };
  }, [intent, renderIntent]);

  const contentClassName =
    phase === "out"
      ? "opacity-0 translate-y-1.5 transition-all duration-100 ease-out"
      : phase === "in"
        ? "animate-apex-intent-in"
        : "opacity-100 translate-y-0";

  return { renderIntent, contentClassName, phase };
}
