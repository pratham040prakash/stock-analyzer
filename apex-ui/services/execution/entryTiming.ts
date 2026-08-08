import { calculateRSI } from "@/services/market/indicators";
import { fetchStockData } from "@/services/market/stockData";

export type EntryInput = {
  price: number;
  recentHigh: number;
  recentLow: number;
  volume: number;
  avgVolume: number;
  momentum: number;
};

export type EntryDecision = {
  enter: boolean;
  reason: string;
};

const RECENT_WINDOW = 20;
const VOLUME_MULTIPLIER = 1.2;
const MOMENTUM_THRESHOLD = 60;

export function isBreakout(price: number, recentHigh: number): boolean {
  return price > recentHigh;
}

export function isVolumeStrong(volume: number, avgVolume: number): boolean {
  if (avgVolume <= 0) {
    return false;
  }

  return volume > avgVolume * VOLUME_MULTIPLIER;
}

export function isMomentumStrong(momentum: number): boolean {
  return momentum > MOMENTUM_THRESHOLD;
}

function hasValidEntryInput(input: EntryInput): boolean {
  return (
    Number.isFinite(input.price) &&
    Number.isFinite(input.recentHigh) &&
    Number.isFinite(input.recentLow) &&
    Number.isFinite(input.volume) &&
    Number.isFinite(input.avgVolume) &&
    Number.isFinite(input.momentum) &&
    input.price > 0 &&
    input.recentHigh > 0 &&
    input.avgVolume > 0
  );
}

export function shouldEnterTrade(input: EntryInput): EntryDecision {
  if (!hasValidEntryInput(input)) {
    return {
      enter: false,
      reason: "Missing entry data",
    };
  }

  const breakout = isBreakout(input.price, input.recentHigh);
  const volume = isVolumeStrong(input.volume, input.avgVolume);
  const momentum = isMomentumStrong(input.momentum);

  if (breakout && volume && momentum) {
    return {
      enter: true,
      reason: "Confirmed breakout",
    };
  }

  return {
    enter: false,
    reason: "Waiting for confirmation",
  };
}

/** Never throws — missing data means do not enter. */
export function shouldEnterTradeSafe(input: Partial<EntryInput>): EntryDecision {
  try {
    if (
      input.price === undefined ||
      input.recentHigh === undefined ||
      input.recentLow === undefined ||
      input.volume === undefined ||
      input.avgVolume === undefined ||
      input.momentum === undefined
    ) {
      return {
        enter: false,
        reason: "Missing entry data",
      };
    }

    return shouldEnterTrade({
      price: input.price,
      recentHigh: input.recentHigh,
      recentLow: input.recentLow,
      volume: input.volume,
      avgVolume: input.avgVolume,
      momentum: input.momentum,
    });
  } catch (error) {
    console.error("Entry timing check failed:", error);
    return {
      enter: false,
      reason: "Entry timing unavailable",
    };
  }
}

export function buildEntryInputFromMarketData(
  prices: number[],
  volumes: number[],
  livePrice?: number,
): EntryInput | null {
  if (prices.length < RECENT_WINDOW + 1) {
    return null;
  }

  const price = livePrice ?? prices[prices.length - 1];
  const recentPrices = prices.slice(-(RECENT_WINDOW + 1), -1);

  if (recentPrices.length === 0) {
    return null;
  }

  const recentHigh = Math.max(...recentPrices);
  const recentLow = Math.min(...recentPrices);

  const volumeWindow = volumes.slice(-RECENT_WINDOW);
  const validVolumes = volumeWindow.filter((value) => value > 0);

  if (validVolumes.length === 0) {
    return null;
  }

  const avgVolume =
    validVolumes.reduce((sum, value) => sum + value, 0) / validVolumes.length;
  const volume = volumes[volumes.length - 1] ?? 0;
  const momentum = Math.round(calculateRSI(prices));

  if (!Number.isFinite(price) || price <= 0) {
    return null;
  }

  return {
    price,
    recentHigh,
    recentLow,
    volume,
    avgVolume,
    momentum,
  };
}

export async function evaluateEntryTimingSafe(
  stock: string,
  livePrice?: number,
): Promise<EntryDecision> {
  try {
    const data = await fetchStockData(stock);
    const input = buildEntryInputFromMarketData(
      data.prices,
      data.volumes,
      livePrice,
    );

    if (!input) {
      return {
        enter: false,
        reason: "Missing entry data",
      };
    }

    return shouldEnterTrade(input);
  } catch (error) {
    console.error("Entry timing evaluation failed:", error);
    return {
      enter: false,
      reason: "Entry timing unavailable",
    };
  }
}
