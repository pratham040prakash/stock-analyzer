"use client";

type Props = {
  headline: string;
  detail: string;
  followedDays: number;
  trackableDays: number;
  className?: string;
};

export default function DisciplineDigestStrip({
  headline,
  detail,
  followedDays,
  trackableDays,
  className = "",
}: Props) {
  const tone =
    trackableDays > 0 && followedDays / trackableDays >= 0.7
      ? "border-emerald-500/20 bg-emerald-500/5"
      : "border-blue-500/20 bg-blue-500/[0.04]";

  return (
    <section
      className={`rounded-xl border px-4 py-4 ${tone} ${className}`.trim()}
      aria-label="Weekly discipline summary"
    >
      <p className="text-xs font-medium uppercase tracking-wide text-apex-muted/75">
        Weekly discipline
      </p>
      <p className="mt-1 text-xl font-semibold text-apex-text">{headline}</p>
      <p className="mt-1 text-sm text-apex-muted/85">{detail}</p>
    </section>
  );
}
