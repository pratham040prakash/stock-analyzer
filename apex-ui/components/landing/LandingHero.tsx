import Link from "next/link";
import { WAIT_DAY_BRAND } from "@/lib/gtm/waitDayBrandCopy";
import LandingSection from "./LandingSection";

export default function LandingHero() {
  return (
    <LandingSection narrow className="pt-16 pb-20 sm:pt-24 sm:pb-28 text-center">
      <p className="text-[13px] font-medium text-apex-muted">
        APEX · {WAIT_DAY_BRAND.tagline}
      </p>

      <h1 className="mt-5 text-[36px] font-bold leading-[1.08] tracking-tight text-apex-text sm:text-[48px] sm:leading-[1.05]">
        {WAIT_DAY_BRAND.headline}
      </h1>

      <p className="mx-auto mt-6 max-w-xl text-[16px] leading-relaxed text-apex-muted sm:text-[18px]">
        {WAIT_DAY_BRAND.heroSubline}
      </p>

      <Link
        href="/login?next=/app"
        className="mt-10 inline-flex w-full max-w-sm items-center justify-center rounded-xl bg-emerald-500 px-6 py-4 text-[15px] font-semibold text-slate-950 transition-all duration-200 ease-out hover:scale-[1.02] hover:bg-emerald-400 active:scale-[0.99] sm:w-auto sm:min-w-[280px]"
      >
        {WAIT_DAY_BRAND.landingCta}
      </Link>

      <p className="mt-4 text-[13px] text-apex-muted">
        {WAIT_DAY_BRAND.footerNote}
      </p>
    </LandingSection>
  );
}
