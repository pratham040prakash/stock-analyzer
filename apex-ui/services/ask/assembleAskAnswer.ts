import { assembleResearchSummary } from "@/services/research/assembleResearchSummary";
import type { AskAnswerViewModel, AskAnswerWord } from "@/types/askAnswer";

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

export async function assembleAskAnswer(question: string): Promise<AskAnswerViewModel> {
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
  const answerWord = mapVerdict(research.verdict, trimmed);

  return {
    question: trimmed,
    answer_word: answerWord,
    headline: `${answerWord} · ${symbol}`,
    reason: research.summary,
    uncertainty:
      research.source === "alpha_ai"
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
  const buy = mapVerdict("YES", "Should I buy INFY?");
  const reduce = mapVerdict("YES", "Should I sell INFY?");

  if (buy !== "Buy" || reduce !== "Reduce") {
    throw new Error("Ask answer self-check failed: verdict mapping");
  }
}
