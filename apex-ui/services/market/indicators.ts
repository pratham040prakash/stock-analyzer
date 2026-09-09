export function calculateMA(prices: number[], period: number): number {
  const slice = prices.slice(-period);
  if (slice.length < period) {
    return 0;
  }
  return slice.reduce((a, b) => a + b, 0) / period;
}

/**
 * Wilder RSI(14). First average is the SMA of the first `period` changes,
 * then RMA. Matches the 1y/5y Nifty research (`analyzer/ta.rsi`).
 */
export function calculateRSI(prices: number[], period = 14): number {
  if (prices.length < period + 1) {
    return 50;
  }

  let avgGain = 0;
  let avgLoss = 0;

  for (let index = 1; index <= period; index += 1) {
    const diff = prices[index] - prices[index - 1];
    if (diff > 0) {
      avgGain += diff;
    } else {
      avgLoss -= diff;
    }
  }

  avgGain /= period;
  avgLoss /= period;

  for (let index = period + 1; index < prices.length; index += 1) {
    const diff = prices[index] - prices[index - 1];
    const gain = diff > 0 ? diff : 0;
    const loss = diff < 0 ? -diff : 0;
    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;
  }

  if (avgLoss === 0) {
    return avgGain === 0 ? 50 : 100;
  }

  const rs = avgGain / avgLoss;
  return 100 - 100 / (1 + rs);
}

export function latestPrice(prices: number[]): number {
  return prices[prices.length - 1] ?? 0;
}

export function runIndicatorsSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Indicators self-check failed: ${message}`);
    }
  };

  assert(calculateMA([1, 2, 3, 4, 5], 3) === 4, "SMA must average the last N closes");

  const wilderFixture = [
    44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.1, 45.42, 45.84, 46.08, 45.89,
    46.03, 45.61, 46.28, 46.28, 46.0, 46.03, 46.41, 46.22, 45.64, 46.21, 46.25,
    45.71, 46.45, 45.78, 45.35, 44.03, 44.18, 44.22, 44.57, 43.42, 42.66,
  ];
  const rsi = calculateRSI(wilderFixture);
  assert(
    Math.abs(rsi - 33.090483) < 0.0001,
    `Wilder RSI must match the research fixture (${rsi})`,
  );

  const monotone = Array.from({ length: 20 }, (_, index) => 100 + index);
  assert(calculateRSI(monotone) === 100, "All-up series must be RSI 100");
}
