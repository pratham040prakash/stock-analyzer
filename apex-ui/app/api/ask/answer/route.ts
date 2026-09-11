import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import { assembleAskAnswer } from "@/services/ask/assembleAskAnswer";
import { answerVoiceDesk } from "@/lib/dailyLoop/deskHorizon";
import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import { createAdminClient } from "@/lib/supabase/admin";
import { readServerContract } from "@/services/desk/contractStore";
import {
  assembleMacroAskAnswer,
  isMacroQuestion,
} from "@/services/ask/assembleMacroAskAnswer";
import {
  assemblePortfolioAskAnswer,
  isPortfolioQuestion,
} from "@/services/ask/assemblePortfolioAskAnswer";
import { createClient } from "@/lib/supabase/server";
import { getTodayDailyDecision } from "@/services/decision/repository";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  let body: { question?: string };

  try {
    body = (await request.json()) as { question?: string };
  } catch {
    return apiError("Invalid JSON body", 400);
  }

  const question = body.question?.trim();

  if (!question || question.length > 500) {
    return apiError("Question required (max 500 chars)", 400);
  }

  const contract = await readServerContract(
    createAdminClient(),
    user.id,
    tradingDateKey(),
  );
  const artifact = await getTodayDailyDecision(supabase, user.id);
  const voice = answerVoiceDesk({ question, contract });
  const answer = voice
    ? {
        question,
        answer_word: "Wait" as const,
        headline: voice.headline,
        reason: voice.reason,
        uncertainty: "Low",
        symbol: contract?.watchSymbol ?? null,
        proof_href: null,
        built_at: new Date().toISOString(),
      }
    : isPortfolioQuestion(question)
    ? await assemblePortfolioAskAnswer(supabase, user.id, question)
    : isMacroQuestion(question)
      ? assembleMacroAskAnswer(question)
      : await assembleAskAnswer(question, artifact);

  return NextResponse.json({ status: "ok", answer });
}
