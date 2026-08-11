import type { AskAnswerViewModel } from "@/types/askAnswer";

const MACRO_PATTERNS = [
  /nifty/i,
  /sensex/i,
  /market (fall|drop|crash|correction)/i,
  /index (fall|drop|crash)/i,
  /macro/i,
  /what if.*\d+%/i,
  /fall.*\d+%/i,
  /drop.*\d+%/i,
];

export function isMacroQuestion(question: string): boolean {
  return MACRO_PATTERNS.some((pattern) => pattern.test(question));
}

function extractPercentMove(question: string): number | null {
  const match = question.match(/(\d+(?:\.\d+)?)\s*%/);

  if (!match?.[1]) {
    return null;
  }

  const value = Number(match[1]);

  return Number.isFinite(value) ? value : null;
}

export function assembleMacroAskAnswer(question: string): AskAnswerViewModel {
  const builtAt = new Date().toISOString();
  const move = extractPercentMove(question);
  const sharpMove = move !== null && move >= 2;

  if (/crash|correction|fall|drop/i.test(question) || sharpMove) {
    return {
      question,
      answer_word: "Wait",
      headline: "Wait · protect process first",
      reason: sharpMove
        ? `A ~${move}% index move raises volatility — honor existing WAIT receipts before adding risk.`
        : "Macro stress favors patience — review allocation drift before new buys.",
      uncertainty: "Medium",
      symbol: null,
      built_at: builtAt,
    };
  }

  return {
    question,
    answer_word: "Wait",
    headline: "Wait · macro context",
    reason: "Macro questions need a calm plan — check core bucket drift and cash buffer first.",
    uncertainty: "Medium",
    symbol: null,
    built_at: builtAt,
  };
}

export function runMacroAskSelfCheck(): void {
  if (!isMacroQuestion("What if Nifty falls 2%?")) {
    throw new Error("Macro ask self-check failed");
  }

  const answer = assembleMacroAskAnswer("What if Nifty falls 2%?");

  if (answer.answer_word !== "Wait") {
    throw new Error("Macro ask self-check failed: answer word");
  }
}
