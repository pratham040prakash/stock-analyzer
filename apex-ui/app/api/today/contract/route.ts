import { apiError, apiOk } from "@/lib/api/response";
import { shiftIstDateKey, tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import { campaignDay } from "@/lib/dailyLoop/deskNight";
import type { TodayContract } from "@/lib/dailyLoop/todayContract";
import { bannedWatchSymbols } from "@/lib/dailyLoop/todayMemory";
import { createAdminClient } from "@/lib/supabase/admin";
import { createClient } from "@/lib/supabase/server";
import {
  listContractHistory,
  readServerContract,
  writeServerContract,
} from "@/services/desk/contractStore";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const requested = new URL(request.url).searchParams.get("date");
  const dateKey =
    requested && /^\d{4}-\d{2}-\d{2}$/.test(requested)
      ? requested
      : tradingDateKey();
  const desk = createAdminClient();
  const contract = await readServerContract(desk, user.id, dateKey);
  const history = await listContractHistory(
    desk,
    user.id,
    shiftIstDateKey(dateKey, -14),
  );
  const day = campaignDay({
    watchSymbol: contract?.watchSymbol,
    dateKey,
    history: history.map((item) => ({
      dateKey: item.dateKey,
      watchSymbol: item.watchSymbol,
      dead: item.watchDead,
    })),
  });

  return apiOk({
    contract: contract
      ? {
          ...contract,
          campaignDay: contract.campaignDay ?? day,
        }
      : null,
    campaignDay: day,
    bannedSymbols: bannedWatchSymbols(history, dateKey),
  });
}

export async function PUT(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  let body: TodayContract;
  try {
    body = (await request.json()) as TodayContract;
  } catch {
    return apiError("Invalid JSON body", 400);
  }

  if (!body?.kiteLine || !body?.rule || !body?.dateKey) {
    return apiError("kiteLine, rule, and dateKey are required", 400);
  }

  const saved = await writeServerContract(createAdminClient(), user.id, body);
  if (!saved) {
    return apiError("Could not save contract", 500);
  }

  return apiOk({ contract: saved });
}
