import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database } from "@/types/database";
import { shiftIstDateKey, tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import { assembleSundayLetter } from "@/lib/dailyLoop/deskOs";
import { sendDeskAlert } from "@/services/desk/interrupt";
import {
  claimDeskAlert,
  listContractHistory,
  listServerContracts,
  writeServerContract,
} from "@/services/desk/contractStore";

type Client = SupabaseClient<Database>;

export async function runSundayLetters(
  admin: Client,
  now = new Date(),
): Promise<{ written: number }> {
  const weekday = now.toLocaleDateString("en-US", {
    timeZone: "Asia/Kolkata",
    weekday: "short",
  });
  if (weekday !== "Sun") {
    return { written: 0 };
  }

  const dateKey = tradingDateKey(now);
  const rows = await listServerContracts(admin, dateKey);
  const seen = new Set(rows.map((row) => row.userId));
  let written = 0;

  for (const row of rows) {
    if (await writeOneSunday(admin, row.userId, dateKey, row.contract)) {
      written += 1;
    }
  }

  const older = await listServerContracts(admin, shiftIstDateKey(dateKey, -1));
  for (const row of older) {
    if (seen.has(row.userId)) {
      continue;
    }
    if (await writeOneSunday(admin, row.userId, dateKey, row.contract)) {
      written += 1;
    }
  }

  return { written };
}

async function writeOneSunday(
  admin: Client,
  userId: string,
  dateKey: string,
  contract: Awaited<ReturnType<typeof listServerContracts>>[number]["contract"],
): Promise<boolean> {
  if (contract.sundayLetter) {
    return false;
  }

  const history = await listContractHistory(
    admin,
    userId,
    shiftIstDateKey(dateKey, -6),
  );
  const letter = assembleSundayLetter({
    weekOf: dateKey,
    history,
  });
  await writeServerContract(admin, userId, {
    ...contract,
    dateKey,
    sundayLetter: letter,
  });

  if (await claimDeskAlert(admin, userId, dateKey, `sunday:${dateKey}`)) {
    await sendDeskAlert({
      title: `APEX Sunday · ${dateKey}`,
      body: letter,
    });
  }

  return true;
}
