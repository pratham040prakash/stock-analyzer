import axios from "axios";
import type { IndexBar } from "@/lib/market/tapeRegime";

export type StockPriceData = {
  prices: number[];
  volumes: number[];
  highs: number[];
  lows: number[];
};

const CACHE_MS = 5 * 60 * 1000;
const cache = new Map<string, { data: StockPriceData; at: number }>();

const EMPTY_DATA: StockPriceData = {
  prices: [],
  volumes: [],
  highs: [],
  lows: [],
};
const INDEX_CACHE_KEY = "__NIFTY50__";

const NIFTY_INDEX_URL =
  "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?range=1y&interval=1d";

function yahooChartUrl(symbol: string): string {
  return `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}.NS?range=3mo&interval=1d`;
}

function finiteNumber(value: unknown, fallback: number): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function parseChartPrices(res: { data?: unknown }): StockPriceData {
  const result = (res.data as { chart?: { result?: unknown[] } })?.chart
    ?.result?.[0];
  const quote = (
    result as {
      indicators?: {
        quote?: {
          close?: unknown[];
          volume?: unknown[];
          high?: unknown[];
          low?: unknown[];
        }[];
      };
    }
  )?.indicators?.quote?.[0];
  const closes: unknown[] = quote?.close ?? [];
  const volumes: unknown[] = quote?.volume ?? [];
  const highs: unknown[] = quote?.high ?? [];
  const lows: unknown[] = quote?.low ?? [];

  const prices: number[] = [];
  const vols: number[] = [];
  const highSeries: number[] = [];
  const lowSeries: number[] = [];

  for (let i = 0; i < closes.length; i++) {
    const close = closes[i];
    if (typeof close !== "number" || Number.isNaN(close)) {
      continue;
    }

    prices.push(close);
    const vol = volumes[i];
    vols.push(typeof vol === "number" && !Number.isNaN(vol) ? vol : 0);
    highSeries.push(finiteNumber(highs[i], close));
    lowSeries.push(finiteNumber(lows[i], close));
  }

  return { prices, volumes: vols, highs: highSeries, lows: lowSeries };
}

export function indexBarsFromPriceData(data: StockPriceData): IndexBar[] {
  return data.prices.map((close, index) => ({
    close,
    high: data.highs[index] ?? close,
    low: data.lows[index] ?? close,
  }));
}

export async function fetchIndexPrices(): Promise<number[]> {
  const cached = cache.get(INDEX_CACHE_KEY);

  if (cached && Date.now() - cached.at < CACHE_MS) {
    return cached.data.prices;
  }

  try {
    const res = await axios.get(NIFTY_INDEX_URL, {
      timeout: 8000,
      headers: { "User-Agent": "APEX/1.0" },
    });

    const data = parseChartPrices(res);
    cache.set(INDEX_CACHE_KEY, { data, at: Date.now() });
    return data.prices;
  } catch {
    return [];
  }
}

export async function fetchIndexBars(): Promise<IndexBar[]> {
  const cached = cache.get(INDEX_CACHE_KEY);

  if (cached && Date.now() - cached.at < CACHE_MS) {
    return indexBarsFromPriceData(cached.data);
  }

  const prices = await fetchIndexPrices();
  if (prices.length === 0) {
    return [];
  }

  const data = cache.get(INDEX_CACHE_KEY)?.data;
  return data ? indexBarsFromPriceData(data) : [];
}

export async function fetchStockData(symbol: string): Promise<StockPriceData> {
  const key = symbol.toUpperCase();
  const cached = cache.get(key);

  if (cached && Date.now() - cached.at < CACHE_MS) {
    return cached.data;
  }

  try {
    const res = await axios.get(yahooChartUrl(key), {
      timeout: 8000,
      headers: { "User-Agent": "APEX/1.0" },
    });

    const data = parseChartPrices(res);
    cache.set(key, { data, at: Date.now() });
    return data;
  } catch {
    return EMPTY_DATA;
  }
}
