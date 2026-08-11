import { assembleResearchSummary } from "@/services/research/assembleResearchSummary";
import type { AskAnswerViewModel, AskAnswerWord } from "@/types/askAnswer";

const SYMBOL_PATTERN = /\b([A-Z]{2,15})\b/;

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

function mapVerdict(verdict: string): AskAnswerWord {
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
      built_at: new Date().toISOString(),
    };
  }

  const research = await assembleResearchSummary(symbol);
  const answerWord = mapVerdict(research.verdict);

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
    built_at: new Date().toISOString(),
  };
}

export function runAskAnswerSelfCheck(): void {
  const word = mapVerdict("YES");

  if (word !== "Buy") {
    throw new Error("Ask answer self-check failed: YES should map to Buy");
  }
}
