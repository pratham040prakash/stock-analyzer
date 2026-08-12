import type { ExploreSetup } from "@/lib/dailyLoop/capitalDecision";

export function formatExploreSetupBadge(stage: ExploreSetup["stage"]): string {
  switch (stage) {
    case "Close to readiness":
      return "Almost ready";
    case "Developing setup":
      return "Building";
    case "Early formation":
      return "Early watch";
  }
}

export function formatExploreSetupSummary(setup: ExploreSetup): string {
  return setup.activation.replace(/^Break above/i, "Buy above").replace(
    /^Break below/i,
    "Sell below",
  );
}

export function formatExplorePipelineSummaryPlain(summary: string | undefined): string | undefined {
  if (!summary) {
    return undefined;
  }

  return summary
    .replace(/close to activation/gi, "almost ready")
    .replace(/setup/gi, "stock")
    .replace(/setups/gi, "stocks")
    .replace(/building/gi, "still building");
}

export function runExploreSetupPresentationSelfCheck(): void {
  const badge = formatExploreSetupBadge("Close to readiness");
  if (badge !== "Almost ready") {
    throw new Error("Explore setup presentation self-check failed");
  }
}
