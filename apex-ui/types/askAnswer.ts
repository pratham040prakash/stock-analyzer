export type AskAnswerWord = "Wait" | "Buy" | "Sell" | "Reduce" | "Pass";

export type AskAnswerViewModel = {
  question: string;
  answer_word: AskAnswerWord;
  headline: string;
  reason: string;
  uncertainty: string;
  symbol: string | null;
  built_at: string;
};
