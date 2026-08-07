"use client";

import MentorCard from "./mentor/MentorCard";
import type { MentorDecision } from "@/types/mentorDecision";

type Props = {
  decision: MentorDecision;
  onNextStep?: () => void;
};

function urgencyClass(urgency: MentorDecision["urgency"]): string {
  if (urgency === "high") return "text-amber-300/90";
  if (urgency === "medium") return "text-teal-300/80";
  return "text-gray-400";
}

function suggestionLabel(suggestion: "add" | "reduce" | "hold"): string {
  if (suggestion === "add") return "Add carefully";
  if (suggestion === "reduce") return "Reduce exposure";
  return "Stay steady";
}

export default function MentorGuidance({ decision, onNextStep }: Props) {
  return (
    <div className="space-y-6">
      <div className="relative bg-gradient-to-r from-slate-900 to-slate-800 border border-white/10 rounded-2xl p-6 space-y-5 shadow-[0_0_40px_rgba(59,130,246,0.08)]">
        <div className="absolute top-4 right-6 text-xs text-gray-500">
          APEX is here with you
        </div>

        <div>
          <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">
            Your guidance
          </div>
          <p className="text-xl text-white leading-relaxed">{decision.summary}</p>
          <p className={`text-sm mt-2 italic ${urgencyClass(decision.urgency)}`}>
            {decision.primaryInsight}
          </p>
        </div>

        <div className="pt-3 border-t border-white/10 space-y-2">
          <div className="text-xs text-gray-400 mb-1">Why this matters</div>
          {decision.reasoning.map((line) => (
            <p key={line} className="text-sm text-gray-300">
              {line}
            </p>
          ))}
        </div>

        {decision.affectedStocks && decision.affectedStocks.length > 0 && (
          <div className="pt-3 border-t border-white/10 space-y-3">
            <div className="text-xs text-gray-400 uppercase tracking-wider">
              Where to look
            </div>
            <ul className="space-y-2">
              {decision.affectedStocks.map((stock) => (
                <li
                  key={stock.symbol}
                  className="text-sm border border-white/5 rounded-lg p-3 bg-white/[0.02]"
                >
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="text-white font-medium">{stock.symbol}</span>
                    <span className="text-xs text-gray-400">
                      {suggestionLabel(stock.suggestion)}
                    </span>
                  </div>
                  <p className="text-gray-400">{stock.reason}</p>
                </li>
              ))}
            </ul>
          </div>
        )}

        {decision.financialContext && (
          <div className="pt-3 border-t border-white/10">
            <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">
              Your capacity
            </div>
            <p className="text-sm text-gray-300 italic">
              {decision.financialContext.message}
            </p>
          </div>
        )}

        {decision.behavioralInsight && (
          <p className="text-sm text-teal-400/70 italic">
            {decision.behavioralInsight}
          </p>
        )}
      </div>

      <MentorCard
        label="Next step"
        message={decision.nextStep}
        hint="You don't need to rush — just continue when ready."
        action="Let's look at this together"
        onActionClick={onNextStep}
      />

      <p className="text-sm text-gray-400 italic text-center max-w-lg mx-auto">
        {decision.sessionClosing}
      </p>
    </div>
  );
}
