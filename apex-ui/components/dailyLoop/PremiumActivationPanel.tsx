"use client";

import { useState } from "react";

type Props = {
  compact?: boolean;
  onActivated?: () => void;
};

export default function PremiumActivationPanel({
  compact = false,
  onActivated,
}: Props) {
  const [code, setCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmed = code.trim();

    if (!trimmed || submitting) {
      return;
    }

    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch("/api/subscription/activate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: trimmed }),
        cache: "no-store",
      });

      const payload = (await response.json()) as {
        status?: string;
        message?: string;
      };

      if (!response.ok || payload.status !== "ok") {
        setError(
          typeof payload.message === "string"
            ? payload.message
            : "Invalid access code",
        );
        return;
      }

      setSuccess(
        typeof payload.message === "string"
          ? payload.message
          : "APEX Premium is now active.",
      );
      setCode("");
      onActivated?.();
    } catch {
      setError("Could not activate right now. Try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={
        compact
          ? "mt-3 space-y-2 border-t border-apex-border/10 pt-3"
          : "mt-4 space-y-3 border-t border-apex-border/10 pt-4"
      }
    >
      <div>
        <label
          htmlFor={compact ? "premium-access-code-compact" : "premium-access-code"}
          className="text-xs font-medium uppercase tracking-wide text-apex-muted"
        >
          Have an access code?
        </label>
        <p className="mt-1 text-xs leading-snug text-apex-muted/70">
          Enter your invite code to unlock Premium. No payment in this beta.
        </p>
      </div>

      <div className="flex flex-col gap-2 sm:flex-row">
        <input
          id={compact ? "premium-access-code-compact" : "premium-access-code"}
          name="code"
          type="text"
          autoComplete="off"
          spellCheck={false}
          value={code}
          onChange={(event) => setCode(event.target.value)}
          placeholder="Enter access code"
          className="min-w-0 flex-1 rounded-lg border border-apex-border/20 bg-black/20 px-3 py-2 text-sm text-apex-text outline-none ring-0 placeholder:text-apex-muted/50 focus:border-apex-border/40"
        />
        <button
          type="submit"
          disabled={submitting || code.trim().length === 0}
          className="rounded-lg border border-apex-border/25 bg-white/[0.04] px-4 py-2 text-sm font-medium text-apex-text transition hover:bg-white/[0.07] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? "Activating…" : "Activate Premium"}
        </button>
      </div>

      {error ? <p className="text-xs text-amber-200/90">{error}</p> : null}
      {success ? <p className="text-xs text-emerald-300/90">{success}</p> : null}
    </form>
  );
}
