type Props = {
  headline: string;
  bookLine: string;
  leftoverLine: string;
};

export default function TodayPrefillCard({ headline, bookLine, leftoverLine }: Props) {
  return (
    <section className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3">
      <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-apex-muted/70">
        If you place
      </p>
      <p className="mt-1 text-sm font-medium text-apex-text">{headline}</p>
      <p className="mt-1 text-sm text-apex-text/90">{bookLine}</p>
      <p className="mt-1 text-xs text-apex-muted/80">{leftoverLine}</p>
    </section>
  );
}
