import { calculateRSI } from "@/services/market/indicators";

/** Wilder ADX below this is chop. Validated on Nifty 1y + 5y backtraces. */
export const ADX_CHOP_THRESHOLD = 25;
export const RSI_MID_LOW = 40;
export const RSI_MID_HIGH = 60;
export const ADX_PERIOD = 14;

export type IndexBar = {
  high: number;
  low: number;
  close: number;
};

export type TapeRegime = {
  adx: number;
  rsi: number;
  isChop: boolean;
  midRange: boolean;
  hardWait: boolean;
  oversoldBounce: boolean;
  label: string;
  briefLine: string;
};

export const UNAVAILABLE_TAPE: TapeRegime = {
  adx: 0,
  rsi: 50,
  isChop: false,
  midRange: true,
  hardWait: false,
  oversoldBounce: false,
  label: "Tape unavailable",
  briefLine: "Index tape is unavailable — stay with your plan.",
};

function average(values: number[]): number {
  if (values.length === 0) {
    return 0;
  }

  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

export function barsFromCloses(closes: number[]): IndexBar[] {
  return closes
    .filter((close) => Number.isFinite(close))
    .map((close) => ({ high: close, low: close, close }));
}

/**
 * Wilder ADX from high / low / close. Returns 0 when the series is too short
 * so callers can fail open (do not lock Wait on missing tape).
 */
export function calculateADX(bars: IndexBar[], period = ADX_PERIOD): number {
  if (bars.length < period * 2 + 1) {
    return 0;
  }

  const trueRanges: number[] = [];
  const plusDms: number[] = [];
  const minusDms: number[] = [];

  for (let index = 1; index < bars.length; index += 1) {
    const current = bars[index];
    const previous = bars[index - 1];
    const highLow = current.high - current.low;
    const highClose = Math.abs(current.high - previous.close);
    const lowClose = Math.abs(current.low - previous.close);
    trueRanges.push(Math.max(highLow, highClose, lowClose));

    const upMove = current.high - previous.high;
    const downMove = previous.low - current.low;
    plusDms.push(upMove > downMove && upMove > 0 ? upMove : 0);
    minusDms.push(downMove > upMove && downMove > 0 ? downMove : 0);
  }

  let atr = average(trueRanges.slice(0, period));
  let plusDm = average(plusDms.slice(0, period));
  let minusDm = average(minusDms.slice(0, period));
  const dxValues: number[] = [];

  const pushDx = () => {
    const plusDi = (100 * plusDm) / (atr || 1);
    const minusDi = (100 * minusDm) / (atr || 1);
    const diSum = plusDi + minusDi;
    dxValues.push(diSum === 0 ? 0 : (100 * Math.abs(plusDi - minusDi)) / diSum);
  };

  pushDx();

  for (let index = period; index < trueRanges.length; index += 1) {
    atr = (atr * (period - 1) + trueRanges[index]) / period;
    plusDm = (plusDm * (period - 1) + plusDms[index]) / period;
    minusDm = (minusDm * (period - 1) + minusDms[index]) / period;
    pushDx();
  }

  if (dxValues.length < period) {
    return 0;
  }

  let adx = average(dxValues.slice(0, period));
  for (let index = period; index < dxValues.length; index += 1) {
    adx = (adx * (period - 1) + dxValues[index]) / period;
  }

  return adx;
}

export function tapeRegimeCopy(input: {
  hardWait: boolean;
  oversoldBounce: boolean;
  isChop: boolean;
}): Pick<TapeRegime, "label" | "briefLine"> {
  if (input.hardWait) {
    return {
      label: "Range-bound — Wait on new buys",
      briefLine:
        "Nifty is chopping in the middle of its range. Mid-range chop has no edge — Wait.",
    };
  }

  if (input.oversoldBounce) {
    return {
      label: "Oversold — bounce setup, not a chase",
      briefLine:
        "Index RSI is washed out. That historically favors patience for a bounce, not chasing strength.",
    };
  }

  if (!input.isChop) {
    return {
      label: "Trend on — stick to your plan",
      briefLine: "Index has a trend. Follow the plan — do not add extra trades.",
    };
  }

  return {
    label: "Quiet tape — no rush",
    briefLine: "Tape is quiet. Stay with Wait unless a trim is required.",
  };
}

export function resolveTapeRegime(bars: IndexBar[]): TapeRegime {
  if (bars.length < ADX_PERIOD * 2 + 1) {
    return UNAVAILABLE_TAPE;
  }

  const closes = bars.map((bar) => bar.close);
  const adx = calculateADX(bars);
  const rsi = calculateRSI(closes);
  const measured = adx > 0;
  const isChop = measured && adx < ADX_CHOP_THRESHOLD;
  const midRange = rsi >= RSI_MID_LOW && rsi <= RSI_MID_HIGH;
  const oversoldBounce = rsi < RSI_MID_LOW;
  const hardWait = isChop && midRange;
  const copy = tapeRegimeCopy({ hardWait, oversoldBounce, isChop });

  return {
    adx,
    rsi,
    isChop,
    midRange,
    hardWait,
    oversoldBounce,
    label: copy.label,
    briefLine: copy.briefLine,
  };
}

export function runTapeRegimeSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Tape regime self-check failed: ${message}`);
    }
  };

  const trending: IndexBar[] = Array.from({ length: 80 }, (_, index) => {
    const close = 100 + index * 2;
    return { high: close + 0.6, low: close - 0.2, close };
  });
  const chop: IndexBar[] = Array.from({ length: 80 }, (_, index) => {
    const close = 100 + (index % 2 === 0 ? 0.35 : -0.35);
    return { high: close + 0.2, low: close - 0.2, close };
  });

  const trendAdx = calculateADX(trending);
  const chopAdx = calculateADX(chop);
  assert(trendAdx >= ADX_CHOP_THRESHOLD, `Trending ADX should be strong (${trendAdx})`);
  assert(chopAdx > 0 && chopAdx < ADX_CHOP_THRESHOLD, `Chop ADX should be weak (${chopAdx})`);

  const shortTape = resolveTapeRegime(trending.slice(0, 10));
  assert(!shortTape.hardWait, "Short series must fail open");

  const chopTape = resolveTapeRegime(chop);
  assert(chopTape.isChop, "Sine series must read as chop");
  assert(chopTape.hardWait, "Mid-range chop must hard-wait new buys");

  const trendTape = resolveTapeRegime(trending);
  assert(!trendTape.isChop, "Monotone series must not read as chop");
  assert(!trendTape.hardWait, "Strong trend must not hard-wait");

  const washed: IndexBar[] = Array.from({ length: 80 }, (_, index) => {
    const close = 200 - index * 1.4;
    return { high: close + 0.3, low: close - 0.8, close };
  });
  const oversold = resolveTapeRegime(washed);
  assert(oversold.oversoldBounce, "Sustained decline must flag oversold bounce");
  assert(!oversold.hardWait, "Oversold is not the mid-range Wait lock");
}
