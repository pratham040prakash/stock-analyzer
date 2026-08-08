import LandingSection from "./LandingSection";

const SOLUTIONS = [
  {
    title: "Finds real opportunities",
    body: "One clear action — only when conditions align.",
  },
  {
    title: "Cuts through the noise",
    body: "Markets are loud. APEX filters what actually matters.",
  },
  {
    title: "Guides your next step",
    body: "When to act, how much, and what to skip — spelled out.",
  },
] as const;

export default function LandingSolution() {
  return (
    <LandingSection narrow className="py-16 sm:py-20">
      <h2 className="text-[24px] font-bold tracking-tight text-apex-text sm:text-[28px]">
        APEX removes randomness
      </h2>

      <div className="mt-8 space-y-4">
        {SOLUTIONS.map((item) => (
          <div
            key={item.title}
            className="rounded-2xl border border-apex-border bg-apex-card px-5 py-5 sm:px-6"
          >
            <h3 className="text-[16px] font-semibold text-apex-text">
              {item.title}
            </h3>
            <p className="mt-2 text-[14px] leading-relaxed text-apex-muted">
              {item.body}
            </p>
          </div>
        ))}
      </div>
    </LandingSection>
  );
}
