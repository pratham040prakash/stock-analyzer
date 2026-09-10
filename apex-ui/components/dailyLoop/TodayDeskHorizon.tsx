type Props = {
  lines: string[];
  onDeskSat?: () => void;
  deskSatLine?: string | null;
  satBusy?: boolean;
};

export default function TodayDeskHorizon({
  lines,
  onDeskSat,
  deskSatLine = null,
  satBusy = false,
}: Props) {
  if (lines.length === 0 && !onDeskSat) {
    return null;
  }

  return (
    <section className="space-y-2 rounded-xl border border-white/5 bg-white/[0.02] px-4 py-3">
      <p className="text-center text-[11px] font-medium uppercase tracking-[0.16em] text-apex-muted/65">
        Desk
      </p>
      {lines.slice(0, 8).map((line) => (
        <p key={line} className="text-center text-xs leading-relaxed text-apex-muted/80">
          {line}
        </p>
      ))}
      {deskSatLine ? (
        <p className="text-center text-xs text-emerald-200/80">{deskSatLine}</p>
      ) : null}
      {onDeskSat && !deskSatLine ? (
        <button
          type="button"
          disabled={satBusy}
          onClick={onDeskSat}
          className="mx-auto block text-[11px] font-medium uppercase tracking-[0.16em] text-sky-100/80 disabled:opacity-50"
        >
          I saw the interrupt
        </button>
      ) : null}
    </section>
  );
}
