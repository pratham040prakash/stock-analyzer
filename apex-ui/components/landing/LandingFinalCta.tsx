import Link from "next/link";
import LandingSection from "./LandingSection";

export default function LandingFinalCta() {
  return (
    <LandingSection narrow className="pb-20 pt-8 sm:pb-28">
      <div className="rounded-2xl border border-apex-border bg-apex-card px-6 py-10 text-center sm:px-10 sm:py-12">
        <h2 className="text-[24px] font-bold tracking-tight text-apex-text sm:text-[28px]">
          Start making better decisions today
        </h2>

        <Link
          href="/login?next=/app"
          className="mt-8 inline-flex w-full items-center justify-center rounded-xl bg-emerald-500 px-6 py-4 text-[15px] font-semibold text-slate-950 transition-all duration-200 ease-out hover:scale-[1.02] hover:bg-emerald-400 active:scale-[0.99] sm:w-auto sm:min-w-[240px]"
        >
          Get Started
        </Link>

        <p className="mt-4 text-[13px] text-apex-muted">
          Guidance, not commands. You stay in control.
        </p>
      </div>
    </LandingSection>
  );
}
