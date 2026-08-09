import { resolveZerodhaAccessToken } from "@/services/broker/accessToken";
import { fetchZerodhaQuote } from "@/services/brokers/zerodha";
import {
  evaluateEntryTimingSafe,
  type EntryDecision,
} from "@/services/execution/entryTiming";
import { fetchStockData } from "@/services/market/stockData";
import { formatInr } from "@/lib/funds";
import { normalizeSymbol } from "@/lib/stockPool";
import type { StockPick } from "@/types/decision";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export type ExploreTriggerState = "confirmed" | "near_entry" | "watch" | "wait";

export type ExploreLiveTrigger = {
  symbol: string;
  state: ExploreTriggerState;
  label: string;
  liveScanLine: string;
  livePrice: number;
  activationLevel?: number;
  gapPct?: number;
  reason: string;
  priceSource: "zerodha" | "market" | "snapshot";
  updatedAt: string;
};

function resolveActivationLevel(pick: StockPick): number | undefined {
  if (pick.activationLevel && pick.activationLevel > 0) {
    return Math.round(pick.activationLevel);
  }

  if (pick.price && pick.price > 0) {
    return Math.round(pick.price * 1.02);
  }

  return undefined;
}

function resolveTriggerView(
  pick: StockPick,
  livePrice: number,
  entryDecision: EntryDecision,
): Pick<
  ExploreLiveTrigger,
  "state" | "label" | "liveScanLine" | "activationLevel" | "gapPct" | "reason"
> {
  const activationLevel = resolveActivationLevel(pick);

  if (entryDecision.enter) {
    return {
      state: "confirmed",
      label: "Trigger confirmed",
      liveScanLine: `${entryDecision.reason} — switch to Grow to deploy.`,
      activationLevel,
      reason: entryDecision.reason,
    };
  }

  if (activationLevel && livePrice > 0 && activationLevel > livePrice) {
    const gapPct = Math.max(1, Math.round(((activationLevel - livePrice) / livePrice) * 100));

    if (gapPct <= 3) {
      return {
        state: "near_entry",
        label: "Near entry",
        liveScanLine: `${gapPct}% below ${formatInr(activationLevel)} activation — watch volume.`,
        activationLevel,
        gapPct,
        reason: entryDecision.reason,
      };
    }
  }

  const score = Math.round(pick.score);

  if (
    score >= 55 ||
    pick.signals.trend >= 55 ||
    pick.signals.momentum >= 55
  ) {
    return {
      state: "watch",
      label: "Watch",
      liveScanLine:
        entryDecision.reason || "Setup developing — reassess next session.",
      activationLevel,
      gapPct:
        activationLevel && livePrice > 0 && activationLevel > livePrice
          ? Math.max(1, Math.round(((activationLevel - livePrice) / livePrice) * 100))
          : undefined,
      reason: entryDecision.reason,
    };
  }

  return {
    state: "wait",
    label: "Wait",
    liveScanLine: entryDecision.reason || "Not ready — wait for structure.",
    activationLevel,
    reason: entryDecision.reason,
  };
}

async function resolveLivePrice(
  supabase: Client,
  userId: string,
  symbol: string,
  snapshotPrice?: number,
): Promise<{ price: number; source: ExploreLiveTrigger["priceSource"] } | null> {
  const token = await resolveZerodhaAccessToken(supabase, userId);

  if (token) {
    const quote = await fetchZerodhaQuote(token.accessToken, symbol);

    if (quote.status === "OK" && quote.lastPrice > 0) {
      return { price: quote.lastPrice, source: "zerodha" };
    }
  }

  try {
    const data = await fetchStockData(symbol);

    if (data.prices.length > 0) {
      const price = data.prices[data.prices.length - 1];

      if (price > 0) {
        return { price, source: "market" };
      }
    }
  } catch {
    // Fall through to snapshot price.
  }

  if (snapshotPrice && snapshotPrice > 0) {
    return { price: snapshotPrice, source: "snapshot" };
  }

  return null;
}

export async function getExploreLiveTriggers(
  supabase: Client,
  userId: string,
  picks: StockPick[],
): Promise<ExploreLiveTrigger[]> {
  const unique = new Map<string, StockPick>();

  for (const pick of picks) {
    const symbol = normalizeSymbol(pick.stock);

    if (!symbol || unique.has(symbol)) {
      continue;
    }

    unique.set(symbol, { ...pick, stock: symbol });
  }

  const triggers: ExploreLiveTrigger[] = [];
  const updatedAt = new Date().toISOString();

  for (const pick of unique.values()) {
    const priceResult = await resolveLivePrice(
      supabase,
      userId,
      pick.stock,
      pick.price,
    );

    if (!priceResult) {
      continue;
    }

    const entryDecision = await evaluateEntryTimingSafe(
      pick.stock,
      priceResult.price,
    );
    const view = resolveTriggerView(pick, priceResult.price, entryDecision);

    triggers.push({
      symbol: pick.stock,
      livePrice: Math.round(priceResult.price),
      priceSource: priceResult.source,
      updatedAt,
      ...view,
    });
  }

  return triggers;
}
