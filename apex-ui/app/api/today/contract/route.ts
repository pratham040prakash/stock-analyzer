import { apiError, apiOk } from "@/lib/api/response";
import { shiftIstDateKey, tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import { campaignDay } from "@/lib/dailyLoop/deskNight";
import {
  assembleSundayLetter,
  describeInterruptChannel,
} from "@/lib/dailyLoop/deskOs";
import {
  assembleHorizonLines,
  assembleYearBook,
  circuitBreakerTripped,
  firstWrongName,
  waitStreak,
  watchFaceState,
} from "@/lib/dailyLoop/deskHorizon";
import type { TodayContract } from "@/lib/dailyLoop/todayContract";
import { bannedWatchSymbols } from "@/lib/dailyLoop/todayMemory";
import { createAdminClient } from "@/lib/supabase/admin";
import { createClient } from "@/lib/supabase/server";
import {
  listContractHistory,
  readServerContract,
  writeServerContract,
} from "@/services/desk/contractStore";
import { getTodayDailyDecision } from "@/services/decision/repository";

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

  const sundayLetter =
    contract?.sundayLetter ??
    assembleSundayLetter({
      weekOf: dateKey,
      history,
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
    interrupt: describeInterruptChannel(),
    lastWatchAt: contract?.lastWatchAt ?? null,
    sundayLetter,
    horizon: {
      lines: assembleHorizonLines({ contract, history }),
      watchFace: watchFaceState(contract),
      yearBook: assembleYearBook(history),
      waitStreak: waitStreak(history),
      firstWrongName: firstWrongName(history),
      circuitBreaker: circuitBreakerTripped(history),
    },
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

  // Wave 1: contract's watchSymbol must match today's frozen artifact
  // when both are set. Freeform contracts that contradict the decision
  // are refused so Today cannot be overridden from the client.
  const artifact = await getTodayDailyDecision(supabase, user.id);
  if (artifact) {
    const artifactSymbol =
      artifact.symbol.status === "known"
        ? artifact.symbol.value.trim().toUpperCase()
        : null;
    const watchSymbol = body.watchSymbol?.trim().toUpperCase();

    if (artifactSymbol && watchSymbol && watchSymbol !== artifactSymbol) {
      return apiError(
        `Today's decision is ${artifactSymbol} — refused watchSymbol ${watchSymbol}.`,
        409,
      );
    }

    if (artifact.tradingLocked && watchSymbol) {
      return apiError(
        "Today's decision is locked — cannot assign a watch symbol.",
        409,
      );
    }
  }

  const saved = await writeServerContract(createAdminClient(), user.id, body);
  if (!saved) {
    return apiError("Could not save contract", 500);
  }

  return apiOk({ contract: saved });
}
