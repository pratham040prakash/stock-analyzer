"use client";

type Props = {
  synced: boolean | null;
  message: string | null;
  loading?: boolean;
  onRetry?: () => void;
};

export default function BrokerReconcilePanel({
  synced,
  message,
  loading,
  onRetry,
}: Props) {
  const statusLabel =
    synced === null
      ? "Checking broker…"
      : synced
        ? "Broker reconciled"
        : "Reconcile incomplete";

  const tone =
    synced === null
      ? "border-apex-border/15 bg-white/[0.02]"
      : synced
        ? "border-emerald-500/20 bg-emerald-500/5"
        : "border-amber-500/20 bg-amber-500/5";

  return (
    <section
      aria-label="Broker reconcile"
      className={`rounded-xl border px-4 py-3 space-y-2 ${tone}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Planned vs actual
          </p>
          <p className="text-sm font-medium text-apex-text/90">{statusLabel}</p>
          {message ? (
            <p className="text-xs text-apex-muted/80 mt-1">{message}</p>
          ) : null}
        </div>
        {onRetry ? (
          <button
            type="button"
            disabled={loading}
            onClick={onRetry}
            className="rounded-lg border border-apex-border/25 px-3 py-1.5 text-xs text-apex-muted transition-colors hover:text-apex-text disabled:opacity-50"
          >
            {loading ? "Syncing…" : "Re-sync"}
          </button>
        ) : null}
      </div>
    </section>
  );
}
