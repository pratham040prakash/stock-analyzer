import { generateMentorDecision } from "@/lib/mentorBrain";
import type { FinancialProfile } from "@/lib/financialProfile";
import type { MentorTone } from "@/lib/mentorCopy";
import type { MentorDecision } from "@/types/mentorDecision";
import type { Portfolio } from "@/types/portfolio";
import type { SessionHistory } from "@/types/mentorDecision";

export type MentorEngineInput = {
  portfolio: Portfolio;
  financialProfile: FinancialProfile | null;
  sessionHistory?: SessionHistory;
  mentorTone?: MentorTone;
};

export type MentorEngineResult = {
  decision: MentorDecision;
  message: string;
  confidence: MentorDecision["confidence"];
};

export function evaluateMentor(input: MentorEngineInput): MentorEngineResult {
  const decision = generateMentorDecision({
    portfolio: input.portfolio,
    financialProfile: input.financialProfile,
    sessionHistory: input.sessionHistory ?? {
      pastDecisions: [],
      visitCount: 0,
    },
    mentorTone: input.mentorTone,
  });

  return {
    decision,
    message: decision.summary,
    confidence: decision.confidence,
  };
}
