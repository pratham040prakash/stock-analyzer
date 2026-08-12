/** Per-symbol infographic bar colors — matches reference palette rotation. */

const BAR_PALETTE = [
  {
    fillClass: "from-yellow-400 to-yellow-600",
    dotClass: "bg-yellow-400",
  },
  {
    fillClass: "from-red-400 to-red-600",
    dotClass: "bg-red-400",
  },
  {
    fillClass: "from-orange-400 to-orange-600",
    dotClass: "bg-orange-400",
  },
  {
    fillClass: "from-emerald-400 to-emerald-600",
    dotClass: "bg-emerald-400",
  },
  {
    fillClass: "from-sky-400 to-blue-600",
    dotClass: "bg-sky-400",
  },
  {
    fillClass: "from-violet-400 to-purple-600",
    dotClass: "bg-violet-400",
  },
] as const;

function paletteIndex(symbol: string): number {
  let hash = 0;
  for (let i = 0; i < symbol.length; i += 1) {
    hash = (hash + symbol.charCodeAt(i) * (i + 1)) % 997;
  }

  return hash % BAR_PALETTE.length;
}

export function journeyBarGradient(
  symbol: string,
  state?: { targetReached?: boolean; thesisBroken?: boolean },
): { fillClass: string; dotClass: string } {
  if (state?.targetReached) {
    return {
      fillClass: "from-emerald-300 to-emerald-500",
      dotClass: "bg-emerald-400",
    };
  }

  if (state?.thesisBroken) {
    return {
      fillClass: "from-amber-400 to-amber-600",
      dotClass: "bg-amber-400",
    };
  }

  return BAR_PALETTE[paletteIndex(symbol.trim().toUpperCase())];
}

export function runJourneyBarStyleSelfCheck(): void {
  const first = journeyBarGradient("RELIANCE");
  const again = journeyBarGradient("RELIANCE");
  if (first.fillClass !== again.fillClass) {
    throw new Error("Journey bar style self-check failed: unstable hash");
  }

  const met = journeyBarGradient("X", { targetReached: true });
  if (!met.fillClass.includes("emerald")) {
    throw new Error("Journey bar style self-check failed: target reached tone");
  }
}
