import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database } from "@/types/database";
import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import { assembleCloseLetter, gradeFromTape } from "@/lib/dailyLoop/deskNight";
import { persistDecisionReceipt } from "@/services/receipts/persistReceipt";
import { sendDeskAlert } from "@/services/desk/interrupt";
import { listServerContracts, writeServerContract } from "@/services/desk/contractStore";

type Client = SupabaseClient<Database>;

export async function runCloseLetters(
  admin: Client,
  now = new Date(),
): Promise<{ written: number }> {
  const dateKey = tradingDateKey(now);
  const rows = await listServerContracts(admin, dateKey);
  let written = 0;

  for (const row of rows) {
    if (row.contract.closeLetter) {
      continue;
    }

    const watch = row.contract.watchSymbol?.trim().toUpperCase();
    const grade = gradeFromTape({
      watchSymbol: watch,
      triggerInr: row.contract.triggerInr,
      sessionHigh: watch ? row.contract.sessionHighBySymbol?.[watch] : null,
      sessionLow: watch ? row.contract.sessionLowBySymbol?.[watch] : null,
      killInr: row.contract.triggerInr ? Math.round(row.contract.triggerInr * 0.97) : null,
      outcome: row.contract.outcome,
    });
    const letter = assembleCloseLetter({
      dateKey,
      heldSymbols: row.contract.heldSymbols,
      watchSymbol: watch,
      gapLabel: row.contract.gapLabel,
      outcome: row.contract.outcome,
      grade,
      campaignDay: row.contract.campaignDay,
    });

    await writeServerContract(admin, row.userId, {
      ...row.contract,
      closeLetter: letter,
    });
    await persistDecisionReceipt(admin, row.userId, {
      symbol: watch || row.contract.heldSymbols?.[0] || "BOOK",
      executionKind: "WAIT",
      verdictWord: "Close",
      headline: letter,
      subline: row.contract.kiteLine,
      orderId: `close:${dateKey}`,
    });
    await sendDeskAlert({
      title: `APEX close · ${dateKey}`,
      body: letter,
    });
    written += 1;
  }

  return { written };
}
