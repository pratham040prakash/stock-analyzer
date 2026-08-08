import LandingSection from "./LandingSection";

const PROBLEMS = [
  "They overtrade",
  "They chase noise",
  "They don't follow discipline",
] as const;

export default function LandingProblem() {
  return (
    <LandingSection narrow className="py-16 sm:py-20">
      <h2 className="text-[24px] font-bold tracking-tight text-apex-text sm:text-[28px]">
        Most investors lose money because…
      </h2>

      <ul className="mt-8 space-y-4">
        {PROBLEMS.map((item) => (
          <li
            key={item}
            className="flex items-start gap-3 rounded-2xl border border-apex-border bg-apex-card px-5 py-4"
          >
            <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-red-400/80" />
            <span className="text-[15px] leading-relaxed text-apex-text/90">
              {item}
            </span>
          </li>
        ))}
      </ul>
    </LandingSection>
  );
}
