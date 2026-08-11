import { WAIT_DAY_BRAND } from "@/lib/gtm/waitDayBrandCopy";
import LandingSection from "./LandingSection";

const STEPS = [
  {
    step: "1",
    title: "APEX analyzes the market",
    body: "Quietly. No noise. No hype.",
  },
  {
    step: "2",
    title: WAIT_DAY_BRAND.howItWorksStep2Title,
    body: WAIT_DAY_BRAND.howItWorksStep2Body,
  },
  {
    step: "3",
    title: "Guides your execution",
    body: "Clear steps when you are ready to act — never pressure to chase.",
  },
] as const;

export default function LandingHowItWorks() {
  return (
    <LandingSection className="py-16 sm:py-20">
      <div className="max-w-[640px]">
        <h2 className="text-[24px] font-bold tracking-tight text-apex-text sm:text-[28px]">
          How it works
        </h2>
      </div>

      <ol className="mt-10 grid gap-4 sm:grid-cols-3">
        {STEPS.map((item) => (
          <li
            key={item.step}
            className="rounded-2xl border border-apex-border bg-apex-card p-5 sm:p-6"
          >
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-blue-500/30 bg-blue-500/10 text-[13px] font-semibold text-blue-200">
              {item.step}
            </span>
            <h3 className="mt-4 text-[16px] font-semibold text-apex-text">
              {item.title}
            </h3>
            <p className="mt-2 text-[14px] leading-relaxed text-apex-muted">
              {item.body}
            </p>
          </li>
        ))}
      </ol>
    </LandingSection>
  );
}
