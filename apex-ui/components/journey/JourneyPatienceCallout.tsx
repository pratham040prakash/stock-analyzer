"use client";

export type JourneyPatienceCalloutProps = {
  patienceUntil: string;
  trustLine?: string | null;
  compact?: boolean;
  className?: string;
};

export default function JourneyPatienceCallout({
  patienceUntil,
  trustLine = null,
  compact = false,
  className = "",
}: JourneyPatienceCalloutProps) {
  return (
    <div
      className={[
        "rounded-lg border border-sky-500/25 bg-sky-500/[0.08]",
        compact ? "px-3 py-2" : "px-3 py-3",
        className,
      ].join(" ")}
    >
      <p
        className={[
          "font-semibold leading-snug text-sky-100",
          compact ? "text-sm" : "text-base",
        ].join(" ")}
      >
        {patienceUntil}
      </p>
      {trustLine ? (
        <p className="mt-1 text-[11px] leading-relaxed text-sky-50/80">{trustLine}</p>
      ) : null}
    </div>
  );
}
