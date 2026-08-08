import {
  calculateMA,
  calculateRSI,
  latestPrice,
} from "@/services/market/indicators";
import { fetchStockData } from "@/services/market/stockData";
import {
  FALLBACK_STOCK_UNIVERSE,
  getStockUniverse,
} from "@/services/decision/nifty50";

const FILTER_CACHE_MS = 5 * 60 * 1000;
const FILTER_BATCH_SIZE = 8;

let filterCache: { stocks: string[]; at: number } | null = null;

async function passesPrefilter(stock: string): Promise<string | null> {
  const data = await fetchStockData(stock);

  if (!data || data.prices.length < 50) {
    return null;
  }

  const price = latestPrice(data.prices);
  const ma50 = calculateMA(data.prices, 50);
  const rsi = calculateRSI(data.prices);

  if (price > ma50 && rsi > 50) {
    return stock;
  }

  return null;
}

async function runBatched<T, R>(
  items: T[],
  batchSize: number,
  fn: (item: T) => Promise<R>,
): Promise<R[]> {
  const results: R[] = [];

  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize);
    const batchResults = await Promise.all(batch.map(fn));
    results.push(...batchResults);
  }

  return results;
}

export async function filterStocks(stocks: string[]): Promise<string[]> {
  const screened = await runBatched(stocks, FILTER_BATCH_SIZE, passesPrefilter);

  return screened.filter((stock): stock is string => stock !== null);
}

export async function getFilteredShortlist(
  universe: string[] = getStockUniverse(),
): Promise<string[]> {
  if (filterCache && Date.now() - filterCache.at < FILTER_CACHE_MS) {
    return filterCache.stocks;
  }

  const filtered = await filterStocks(universe);
  const shortlist =
    filtered.length > 0 ? filtered : [...FALLBACK_STOCK_UNIVERSE];

  filterCache = { stocks: shortlist, at: Date.now() };
  return shortlist;
}
