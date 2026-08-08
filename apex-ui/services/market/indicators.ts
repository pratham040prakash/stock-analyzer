export function calculateMA(prices: number[], period: number): number {
  const slice = prices.slice(-period);
  if (slice.length < period) {
    return 0;
  }
  return slice.reduce((a, b) => a + b, 0) / period;
}

export function calculateRSI(prices: number[], period = 14): number {
  if (prices.length < period + 1) {
    return 50;
  }

  let gains = 0;
  let losses = 0;

  for (let i = prices.length - period; i < prices.length - 1; i++) {
    const diff = prices[i + 1] - prices[i];
    if (diff > 0) {
      gains += diff;
    } else {
      losses -= diff;
    }
  }

  const rs = gains / (losses || 1);
  return 100 - 100 / (1 + rs);
}

export function latestPrice(prices: number[]): number {
  return prices[prices.length - 1] ?? 0;
}
