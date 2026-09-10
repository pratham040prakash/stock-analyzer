import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database } from "@/types/database";
import { tradingDateKey, shiftIstDateKey } from "@/lib/dailyLoop/disciplineDates";
import { isNseCashSessionOpen } from "@/lib/broker/marketSession";
import {
  buildHoldInterruptCopy,
  buildWatchInterruptCopy,
  holdNotifyKey,
  watchNotifyKey,
} from "@/lib/dailyLoop/todayMemory";
import { buildBookHoldRule } from "@/lib/dailyLoop/firstBuyToday";
import { cutInrFromInvalidation } from "@/lib/dailyLoop/todayMemory";
import {
  campaignDay,
  mergeSessionExtrema,
} from "@/lib/dailyLoop/deskNight";
import { getActiveBrokerConnection } from "@/services/broker/connections";
import { fetchZerodhaHoldings, fetchZerodhaQuotes } from "@/services/brokers/zerodha";
import { listInvestmentTheses } from "@/services/thesis/thesisRepository";
import { sendDeskAlert } from "@/services/desk/interrupt";
import {
  claimDeskAlert,
  listContractHistory,
  listServerContracts,
  writeServerContract,
} from "@/services/desk/contractStore";

type Client = SupabaseClient<Database>;

export async function runSessionWatch(
  admin: Client,
  now = new Date(),
): Promise<{ watched: number; alerts: number; skipped: string | null }> {
  if (!isNseCashSessionOpen(now)) {
    return { watched: 0, alerts: 0, skipped: "market_closed" };
  }

  const dateKey = tradingDateKey(now);
  const rows = await listServerContracts(admin, dateKey);
  let alerts = 0;

  for (const row of rows) {
    const sent = await watchOneUser(admin, row.userId, row.contract, dateKey);
    alerts += sent;
  }

  return { watched: rows.length, alerts, skipped: null };
}

async function watchOneUser(
  admin: Client,
  userId: string,
  contract: Awaited<ReturnType<typeof listServerContracts>>[number]["contract"],
  dateKey: string,
): Promise<number> {
  const connection = await getActiveBrokerConnection(admin, userId);
  if (!connection?.accessToken || connection.status !== "active") {
    return 0;
  }

  const symbols = [
    ...(contract.heldSymbols ?? []),
    contract.watchSymbol,
  ]
    .map((symbol) => symbol?.trim().toUpperCase())
    .filter((symbol): symbol is string => Boolean(symbol));

  if (symbols.length === 0) {
    return 0;
  }

  const quotes = await fetchZerodhaQuotes(connection.accessToken, symbols);
  const holdings = await fetchZerodhaHoldings(connection.accessToken);
  const avgBySymbol = new Map<string, number>();
  if (holdings.status === "OK") {
    for (const holding of holdings.data) {
      const name = holding.tradingsymbol?.trim().toUpperCase();
      if (name && holding.average_price > 0) {
        avgBySymbol.set(name, holding.average_price);
      }
    }
  }

  let next = { ...contract };
  let alerts = 0;

  for (const symbol of symbols) {
    const quote = quotes.get(symbol);
    if (!quote) {
      continue;
    }

    next.sessionHighBySymbol = mergeSessionExtrema(
      next.sessionHighBySymbol,
      symbol,
      quote.high ?? quote.lastPrice,
      "high",
    );
    next.sessionLowBySymbol = mergeSessionExtrema(
      next.sessionLowBySymbol,
      symbol,
      quote.low ?? quote.lastPrice,
      "low",
    );
  }

  const watch = contract.watchSymbol?.trim().toUpperCase();
  if (watch && contract.triggerInr) {
    const quote = quotes.get(watch);
    const live = quote?.lastPrice;
    const high = next.sessionHighBySymbol?.[watch];
    const low = next.sessionLowBySymbol?.[watch];
    const through =
      (live !== undefined && live >= contract.triggerInr) ||
      (high !== undefined && high >= contract.triggerInr);
    const kill = contract.triggerInr * 0.97;
    const dead =
      (live !== undefined && live < kill) || (low !== undefined && low < kill);
    next.watchThrough = through;
    next.watchDead = dead;

    const key = watchNotifyKey({ symbol: watch, through, dead });
    if ((through || dead) && (await claimDeskAlert(admin, userId, dateKey, key))) {
      const copy = buildWatchInterruptCopy({
        symbol: watch,
        through,
        dead,
        gapLabel: contract.gapLabel,
      });
      if (await sendDeskAlert(copy)) {
        alerts += 1;
      }
    }
  }

  const theses = await listInvestmentTheses(admin, userId);
  const cuts: Record<string, number> = { ...(contract.holdCutsBySymbol ?? {}) };
  for (const thesis of theses) {
    const cut = cutInrFromInvalidation(thesis.invalidation);
    if (cut) {
      cuts[thesis.symbol.trim().toUpperCase()] = cut;
    }
  }
  next.holdCutsBySymbol = cuts;

  for (const symbol of contract.heldSymbols ?? []) {
    const name = symbol.trim().toUpperCase();
    const quote = quotes.get(name);
    if (!quote) {
      continue;
    }

    const hold = buildBookHoldRule({
      lastPriceInr: quote.lastPrice,
      cutInr: cuts[name],
      averagePriceInr: avgBySymbol.get(name) ?? null,
    });
    if (!hold.ruleBroken) {
      continue;
    }

    const key = holdNotifyKey(name);
    if (await claimDeskAlert(admin, userId, dateKey, key)) {
      const copy = buildHoldInterruptCopy({ symbol: name, cutLabel: hold.cutLabel });
      if (await sendDeskAlert(copy)) {
        alerts += 1;
      }
    }
  }

  const history = await listContractHistory(admin, userId, shiftIstDateKey(dateKey, -14));
  next.campaignDay = campaignDay({
    watchSymbol: next.watchSymbol,
    dateKey,
    history: history.map((item) => ({
      dateKey: item.dateKey,
      watchSymbol: item.watchSymbol,
      dead: item.watchDead,
    })),
  });

  await writeServerContract(admin, userId, next);
  return alerts;
}
