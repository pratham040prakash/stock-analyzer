import { assembleResearchSummary } from "@/services/research/assembleResearchSummary";
import type { AskAnswerViewModel, AskAnswerWord } from "@/types/askAnswer";
import type { DailyDecisionArtifact } from "@/types/decision";

const SYMBOL_PATTERN = /\b([A-Z]{2,15})\b/;

const SELL_PATTERN = /\b(sell|exit|trim|reduce|cut)\b/i;

function extractSymbol(question: string): string | null {
  const upper = question.toUpperCase();
  const match = upper.match(SYMBOL_PATTERN);

  if (!match?.[1]) {
    return null;
  }

  const blocked = new Set(["SHOULD", "WHAT", "WHEN", "WAIT", "BUY", "SELL", "IF", "CAN"]);

  if (blocked.has(match[1])) {
    return null;
  }

  return match[1];
}

function mapVerdict(verdict: string, question: string): AskAnswerWord {
  if (SELL_PATTERN.test(question)) {
    return verdict === "YES" ? "Reduce" : verdict === "NO" ? "Wait" : "Wait";
  }

  switch (verdict) {
    case "YES":
      return "Buy";
    case "NO":
      return "Pass";
    default:
      return "Wait";
  }
}

/**
 * Wave 2 non-contradiction guard.
 *
 * Ask may explain research and even recommend WAIT/PASS/REDUCE freely,
 * but it may only emit a BUY/SELL/REDUCE call that matches today's
 * frozen artifact. When there is no artifact, when trading is locked,
 * when today authorises a different action, or when today authorises a
 * different symbol, the requested action word is downgraded to WAIT
 * with a deterministic reason.
 */
export function enforceAskArtifactAlignment(params: {
  answerWord: AskAnswerWord;
  symbol: string | null;
  artifact: DailyDecisionArtifact | null;
}): { answerWord: AskAnswerWord; overrideReason: string | null } {
  const { answerWord, symbol, artifact } = params;

  if (answerWord === "Wait" || answerWord === "Pass") {
    return { answerWord, overrideReason: null };
  }

  const symbolUpper = symbol ? symbol.trim().toUpperCase() : null;

  if (!artifact) {
    return {
      answerWord: "Wait",
      overrideReason: "No frozen decision for today — Ask cannot authorise a trade.",
    };
  }

  if (artifact.tradingLocked || artifact.daily_verdict !== "trade") {
    return {
      answerWord: "Wait",
      overrideReason: "Today's decision is locked — Ask cannot override.",
    };
  }

  const artifactSymbol =
    artifact.symbol.status === "known"
      ? artifact.symbol.value.trim().toUpperCase()
      : null;

  if (!artifactSymbol) {
    return {
      answerWord: "Wait",
      overrideReason: "Today's decision has no confirmed symbol.",
    };
  }

  if (symbolUpper && symbolUpper !== artifactSymbol) {
    return {
      answerWord: "Wait",
      overrideReason: `Today authorises ${artifactSymbol} only — Ask cannot recommend ${symbolUpper}.`,
    };
  }

  if (
    (answerWord === "Buy" && artifact.action !== "buy") ||
    ((answerWord === "Sell" || answerWord === "Reduce") &&
      artifact.action !== "sell" &&
      artifact.action !== "reduce")
  ) {
    return {
      answerWord: "Wait",
      overrideReason: `Today's decision is ${artifact.action} — Ask cannot flip it.`,
    };
  }

  return { answerWord, overrideReason: null };
}

export async function assembleAskAnswer(
  question: string,
  artifact: DailyDecisionArtifact | null = null,
): Promise<AskAnswerViewModel> {
  const trimmed = question.trim();

  if (!trimmed) {
    return {
      question: trimmed,
      answer_word: "Wait",
      headline: "Ask one clear question.",
      reason: "Example: Should I buy RELIANCE?",
      uncertainty: "Mixed",
      symbol: null,
      proof_href: null,
      built_at: new Date().toISOString(),
    };
  }

  const symbol = extractSymbol(trimmed);

  if (!symbol) {
    return {
      question: trimmed,
      answer_word: "Wait",
      headline: "Need a symbol for a stock-specific answer.",
      reason: "Include a ticker — e.g. Should I buy INFY?",
      uncertainty: "High",
      symbol: null,
      proof_href: null,
      built_at: new Date().toISOString(),
    };
  }

  const research = await assembleResearchSummary(symbol);
  const proposed = mapVerdict(research.verdict, trimmed);
  const guarded = enforceAskArtifactAlignment({
    answerWord: proposed,
    symbol,
    artifact,
  });
  const answerWord = guarded.answerWord;
  const reason = guarded.overrideReason ?? research.summary;

  return {
    question: trimmed,
    answer_word: answerWord,
    headline: `${answerWord} · ${symbol}`,
    reason,
    uncertainty:
      guarded.overrideReason !== null
        ? "Low"
        : research.source === "alpha_ai"
          ? "Medium"
          : research.source === "market_data"
            ? "Medium"
            : "High",
    symbol,
    proof_href: `/app/research?symbol=${encodeURIComponent(symbol)}&proof=1`,
    built_at: new Date().toISOString(),
  };
}

export function runAskAnswerSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Ask answer self-check failed: ${message}`);
    }
  };

  const buy = mapVerdict("YES", "Should I buy INFY?");
  const reduce = mapVerdict("YES", "Should I sell INFY?");
  assert(buy === "Buy" && reduce === "Reduce", "verdict mapping");

  const missing = enforceAskArtifactAlignment({
    answerWord: "Buy",
    symbol: "INFY",
    artifact: null,
  });
  assert(
    missing.answerWord === "Wait" && missing.overrideReason !== null,
    "No artifact must force Wait",
  );

  const now = "2026-09-11T09:00:00.000Z";
  const tradingArtifact: DailyDecisionArtifact = {
    schema_version: "1",
    decision_id: "2026-09-11:test",
    decision_date: "2026-09-11",
    frozen_at: now,
    intent: "grow",
    action: "buy",
    symbol: { status: "known", value: "HDFCBANK", observed_at: now },
    approved_size: { kind: "buy_amount", amount_inr: 5000 },
    daily_verdict: "trade",
    tradingLocked: false,
    entryConfirmed: true,
    capital_state: {
      status: "known",
      value: { available_cash_inr: 1, portfolio_value_inr: 1 },
      observed_at: now,
    },
    broker_state: {
      status: "known",
      value: { broker: "zerodha", connection: "connected" },
      observed_at: now,
    },
    market_state: {
      status: "known",
      value: { trend: "sideways", session: "market_open" },
      observed_at: now,
    },
    source_timestamps: {
      portfolio: { status: "known", value: now, observed_at: now },
      capital: { status: "known", value: now, observed_at: now },
      broker: { status: "known", value: now, observed_at: now },
      market: { status: "known", value: now, observed_at: now },
      entry: { status: "known", value: now, observed_at: now },
    },
    evidence_ids: [],
    evidence: [],
    blockers: [],
    decision_metadata: {
      producer: "getDecision/evaluateDailyDecision",
      confidence: 80,
      reason: "Buy",
      confidence_factors: [],
    },
    frozen_portfolio: { positions: [], total_value_inr: 0, pnl_inr: 0 },
    projection: {
      decision: "BUY_MORE",
      action: "buy",
      confidence: 80,
      reason: "Buy",
      confidence_factors: [],
      actions: [],
      stock: "HDFCBANK",
      amount: 5000,
    },
  };

  const matched = enforceAskArtifactAlignment({
    answerWord: "Buy",
    symbol: "hdfcbank",
    artifact: tradingArtifact,
  });
  assert(
    matched.answerWord === "Buy" && matched.overrideReason === null,
    "Matching symbol/side must pass through",
  );

  const wrongSymbol = enforceAskArtifactAlignment({
    answerWord: "Buy",
    symbol: "INFY",
    artifact: tradingArtifact,
  });
  assert(
    wrongSymbol.answerWord === "Wait" && wrongSymbol.overrideReason !== null,
    "Different symbol must force Wait",
  );

  const lockedArtifact: DailyDecisionArtifact = {
    ...tradingArtifact,
    tradingLocked: true,
    daily_verdict: "wait",
    blockers: ["Capital unknown"],
  };
  const locked = enforceAskArtifactAlignment({
    answerWord: "Buy",
    symbol: "HDFCBANK",
    artifact: lockedArtifact,
  });
  assert(
    locked.answerWord === "Wait" && locked.overrideReason !== null,
    "Locked artifact must force Wait",
  );

  const sellFlip = enforceAskArtifactAlignment({
    answerWord: "Reduce",
    symbol: "HDFCBANK",
    artifact: tradingArtifact,
  });
  assert(
    sellFlip.answerWord === "Wait" && sellFlip.overrideReason !== null,
    "Reduce Ask against buy artifact must be refused",
  );
}
