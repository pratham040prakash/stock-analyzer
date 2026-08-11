import { sectorForSymbol } from "@/lib/stockPool";
import type { PortfolioHoldingRow } from "@/types/portfolioApi";

export const DEFAULT_SECTOR_CAP_PCT = 30;

export type SectorWeightRow = {
  sector: string;
  weight_pct: number;
  value_inr: number;
};

export type SectorCapSummary = {
  cap_pct: number;
  top_sector: string | null;
  top_sector_pct: number;
  breached: boolean;
  headroom_pct: number;
  sectors: SectorWeightRow[];
  policy_note: string;
};

export function buildSectorCapSummary(input: {
  holdings: PortfolioHoldingRow[];
  totalValue?: number | null;
  capPct?: number;
}): SectorCapSummary {
  const capPct = input.capPct ?? DEFAULT_SECTOR_CAP_PCT;
  const investedValue = input.holdings.reduce((sum, row) => sum + row.value, 0);
  const totalValue =
    input.totalValue && input.totalValue > 0 ? input.totalValue : investedValue;

  if (totalValue <= 0 || input.holdings.length === 0) {
    return {
      cap_pct: capPct,
      top_sector: null,
      top_sector_pct: 0,
      breached: false,
      headroom_pct: capPct,
      sectors: [],
      policy_note: "Connect broker to measure sector concentration.",
    };
  }

  const sectorValues = new Map<string, number>();

  for (const holding of input.holdings) {
    const sector = sectorForSymbol(holding.tradingsymbol) ?? "Other";
    sectorValues.set(sector, (sectorValues.get(sector) ?? 0) + holding.value);
  }

  const sectors: SectorWeightRow[] = [...sectorValues.entries()]
    .map(([sector, value_inr]) => ({
      sector,
      value_inr,
      weight_pct: Math.round((value_inr / totalValue) * 1000) / 10,
    }))
    .sort((left, right) => right.weight_pct - left.weight_pct);

  const top = sectors[0];
  const topSectorPct = top?.weight_pct ?? 0;
  const breached = topSectorPct > capPct;
  const headroomPct = Math.max(0, Math.round((capPct - topSectorPct) * 10) / 10);

  let policy_note = `${top?.sector ?? "Portfolio"} is within the ${capPct}% sector cap.`;
  if (breached && top) {
    policy_note = `${top.sector} is ${top.weight_pct.toFixed(0)}% — above the ${capPct}% cap. Trim before new buys in this sector.`;
  } else if (top && topSectorPct >= capPct - 5) {
    policy_note = `${top.sector} is near the ${capPct}% cap (${topSectorPct.toFixed(0)}%).`;
  }

  return {
    cap_pct: capPct,
    top_sector: top?.sector ?? null,
    top_sector_pct: topSectorPct,
    breached,
    headroom_pct: headroomPct,
    sectors,
    policy_note,
  };
}

export function runSectorCapPolicySelfCheck(): void {
  const summary = buildSectorCapSummary({
    holdings: [
      {
        tradingsymbol: "HDFCBANK",
        quantity: 10,
        average_price: 100,
        last_price: 110,
        pnl: 100,
        value: 4000,
        allocation_pct: 40,
      },
      {
        tradingsymbol: "ICICIBANK",
        quantity: 5,
        average_price: 200,
        last_price: 210,
        pnl: 50,
        value: 2000,
        allocation_pct: 20,
      },
      {
        tradingsymbol: "INFY",
        quantity: 8,
        average_price: 150,
        last_price: 160,
        pnl: 80,
        value: 4000,
        allocation_pct: 40,
      },
    ],
    totalValue: 10000,
    capPct: 30,
  });

  if (!summary.breached || summary.top_sector !== "Banking") {
    throw new Error("Sector cap policy self-check failed: banking breach");
  }

  if (summary.top_sector_pct !== 60) {
    throw new Error("Sector cap policy self-check failed: weight math");
  }
}
