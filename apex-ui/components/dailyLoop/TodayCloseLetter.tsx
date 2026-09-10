type Props = {
  letter: string;
};

export default function TodayCloseLetter({ letter }: Props) {
  return (
    <section className="rounded-2xl border border-sky-300/15 bg-sky-400/[0.07] px-4 py-3">
      <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-sky-100/70">
        Close letter
      </p>
      <p className="mt-1 text-sm leading-relaxed text-apex-text/90">{letter}</p>
    </section>
  );
}
