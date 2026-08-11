"use client";

import Link from "next/link";
import {
  describeInvestmentStyle,
  OPERATING_MANUAL,
} from "@/lib/dailyLoop/operatingManualCopy";
import { WAIT_DAY_BRAND } from "@/lib/gtm/waitDayBrandCopy";
import { INTENT_UI_LABELS } from "@/lib/onboarding/intentLabels";
import { ApexBody, ApexCard, ApexShell, ApexTitle } from "@/components/ui/apex";
import ApexSurfaceNav from "@/components/nav/ApexSurfaceNav";

const PLAYBOOKS = [
  {
    title: "Wait · Trade · Pause",
    body: WAIT_DAY_BRAND.playbookIntro,
  },
  {
    title: "Long-term core",
    body: OPERATING_MANUAL.coreLine,
  },
  {
    title: "Tactical pool",
    body: OPERATING_MANUAL.tacticalLine,
  },
  {
    title: "Not intraday",
    body: OPERATING_MANUAL.intradayLine,
  },
] as const;

export default function HowApexWorksClient() {
  return (
    <ApexShell>
      <header className="space-y-4">
        <ApexBody>APEX · Operating manual</ApexBody>
        <ApexTitle>How APEX works</ApexTitle>
        <ApexBody>
          Plain language for investors with zero stock jargon — preserve capital first,
          compound over years.
        </ApexBody>
        <ApexSurfaceNav />
      </header>

      <div className="mt-6 space-y-4">
        {PLAYBOOKS.map((section) => (
          <ApexCard key={section.title} hover={false}>
            <h2 className="text-lg font-semibold text-apex-text">{section.title}</h2>
            <p className="mt-2 text-sm leading-relaxed text-apex-muted/85">{section.body}</p>
          </ApexCard>
        ))}

        <ApexCard hover={false}>
          <h2 className="text-lg font-semibold text-apex-text">
            {WAIT_DAY_BRAND.brandCardTitle}
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-apex-muted/85">
            {WAIT_DAY_BRAND.brandCardBody}
          </p>
          <p className="mt-3 text-sm leading-relaxed text-apex-muted/70">
            {WAIT_DAY_BRAND.antiFomoRule}
          </p>
        </ApexCard>

        <ApexCard hover={false}>
          <h2 className="text-lg font-semibold text-apex-text">Investment styles</h2>
          <ul className="mt-3 space-y-2 text-sm text-apex-muted/85">
            <li>{describeInvestmentStyle("long_term_only")}</li>
            <li>{describeInvestmentStyle("core_plus_tactical")}</li>
            <li>{describeInvestmentStyle("tactical_only")}</li>
          </ul>
        </ApexCard>

        <ApexCard hover={false}>
          <h2 className="text-lg font-semibold text-apex-text">Today modes</h2>
          <ul className="mt-3 space-y-2 text-sm text-apex-muted/85">
            {(["grow", "protect", "explore"] as const).map((intent) => (
              <li key={intent}>
                <span className="font-medium text-apex-text/90">
                  {INTENT_UI_LABELS[intent].label}
                </span>
                {" · "}
                {INTENT_UI_LABELS[intent].hint}
              </li>
            ))}
          </ul>
        </ApexCard>
      </div>

      <p className="mt-8 text-sm text-apex-muted/70">
        <Link href="/app" className="text-blue-200/90 hover:underline">
          ← Back to Today
        </Link>
      </p>
    </ApexShell>
  );
}
