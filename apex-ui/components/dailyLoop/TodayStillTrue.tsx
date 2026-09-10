type Props = {
  line: string;
  onConfirm: () => void;
  saving?: boolean;
};

export default function TodayStillTrue({ line, onConfirm, saving = false }: Props) {
  return (
    <section className="rounded-2xl border border-amber-300/20 bg-amber-400/[0.07] px-4 py-3">
      <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-amber-100/70">
        Still true?
      </p>
      <p className="mt-1 text-sm leading-relaxed text-apex-text/90">{line}</p>
      <button
        type="button"
        disabled={saving}
        onClick={onConfirm}
        className="mt-3 rounded-xl border border-white/15 bg-white px-3 py-2 text-xs font-semibold text-black disabled:opacity-50"
      >
        Still true
      </button>
    </section>
  );
}
