"use client";

import { useCallback, useState } from "react";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import type { AskAnswerViewModel } from "@/types/askAnswer";

type Props = {
  open: boolean;
  onClose: () => void;
};

type AnswerResponse = {
  status: string;
  answer: AskAnswerViewModel;
};

export default function AskOverlay({ open, onClose }: Props) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AskAnswerViewModel | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async () => {
    const trimmed = question.trim();

    if (!trimmed) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await apiFetch("/api/ask/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
      });
      const data = await parseApiJson<AnswerResponse>(response, "Ask answer");

      if (response.ok && data?.answer) {
        setAnswer(data.answer);
      } else {
        setError("Could not answer that question right now.");
      }
    } catch (submitError) {
      setError(
        submitError instanceof Error ? submitError.message : "Ask request failed.",
      );
    } finally {
      setLoading(false);
    }
  }, [question]);

  const handleClose = useCallback(() => {
    setAnswer(null);
    setQuestion("");
    setError(null);
    onClose();
  }, [onClose]);

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-4 sm:items-center">
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Ask overlay"
        className="w-full max-w-[430px] rounded-2xl border border-apex-border/20 bg-[#0A0A0B] p-5 space-y-4 shadow-2xl"
      >
        {!answer ? (
          <>
            <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
              What if…?
            </p>
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={3}
              aria-label="Ask a what-if question"
              placeholder="Should I buy RELIANCE? · Am I too concentrated? · What if Nifty falls 2%?"
              className="w-full rounded-xl border border-apex-border/20 bg-white/[0.03] px-3 py-2 text-sm text-apex-text outline-none focus:border-blue-400/40"
            />
            {error ? <p className="text-xs text-amber-200/85">{error}</p> : null}
            <div className="flex gap-2">
              <button
                type="button"
                disabled={loading || !question.trim()}
                onClick={() => void submit()}
                className="flex-1 rounded-xl bg-[#F5F5F7] px-4 py-3 text-sm font-semibold text-[#0A0A0B] disabled:opacity-50"
              >
                {loading ? "Thinking…" : "Answer"}
              </button>
              <button
                type="button"
                onClick={handleClose}
                className="rounded-xl border border-apex-border/25 px-4 py-3 text-sm text-apex-muted"
              >
                Cancel
              </button>
            </div>
          </>
        ) : (
          <>
            <p className="text-5xl font-semibold text-apex-text">{answer.answer_word}</p>
            <p className="text-lg text-apex-text/90">{answer.headline}</p>
            <p className="text-sm text-apex-muted/85">{answer.reason}</p>
            <p className="text-xs text-apex-muted/60">
              Uncertainty · {answer.uncertainty}
            </p>
            {answer.symbol ? (
              <a
                href={`/app/research?symbol=${encodeURIComponent(answer.symbol)}`}
                className="inline-flex text-sm text-blue-200/90 hover:text-blue-100"
              >
                Open research for {answer.symbol} →
              </a>
            ) : null}
            {answer.proof_href ? (
              <a
                href={answer.proof_href}
                className="inline-flex text-sm text-blue-200/90 hover:text-blue-100"
              >
                See the proof →
              </a>
            ) : null}
            <button
              type="button"
              onClick={handleClose}
              className="w-full rounded-xl bg-[#F5F5F7] px-4 py-3 text-sm font-semibold text-[#0A0A0B]"
            >
              Done
            </button>
          </>
        )}
      </div>
    </div>
  );
}
