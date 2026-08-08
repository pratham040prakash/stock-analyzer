import LandingNav from "./LandingNav";
import LandingHero from "./LandingHero";
import LandingProblem from "./LandingProblem";
import LandingSolution from "./LandingSolution";
import LandingCapitalProtection from "./LandingCapitalProtection";
import LandingHowItWorks from "./LandingHowItWorks";
import LandingProductPreview from "./LandingProductPreview";
import LandingFinalCta from "./LandingFinalCta";
import LandingSection from "./LandingSection";

export default function LandingPage() {
  return (
    <div className="relative min-h-screen bg-apex-bg text-apex-text">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(59,130,246,0.05),transparent_55%)]" />

      <div className="relative">
        <LandingNav />
        <LandingHero />
        <LandingProblem />
        <LandingSolution />
        <LandingCapitalProtection />
        <LandingHowItWorks />
        <LandingProductPreview />
        <LandingFinalCta />

        <LandingSection narrow className="border-t border-apex-border pb-10 pt-8">
          <p className="text-center text-[12px] text-apex-muted">
            APEX supports your decisions — not financial advice.
          </p>
        </LandingSection>
      </div>
    </div>
  );
}
