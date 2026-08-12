"use client";

import { KITE_CONNECT_DISCIPLINE } from "@/lib/gtm/kiteConnectDisciplineCopy";
import { ApexBody, ApexButton, ApexCard, ApexEyebrow, ApexTitle } from "@/components/ui/apex";

type Props = {
  syncMessage?: string | null;
  onDismiss?: () => void;
};

export default function KiteConnectDisciplineCard({
  syncMessage,
  onDismiss,
}: Props) {
  return (
    <ApexCard hover={false} padding="compact" className="border-emerald-500/20">
      <ApexEyebrow className="mb-1">{KITE_CONNECT_DISCIPLINE.successEyebrow}</ApexEyebrow>
      <ApexTitle className="text-[20px]">
        {KITE_CONNECT_DISCIPLINE.successHeadline}
      </ApexTitle>
      <ApexBody className="mt-2 max-w-md">{KITE_CONNECT_DISCIPLINE.successBody}</ApexBody>

      {syncMessage ? (
        <p className="mt-3 text-sm text-emerald-200/90">{syncMessage}</p>
      ) : null}

      <ul className="mt-4 space-y-2 text-xs leading-relaxed text-apex-muted/80">
        {KITE_CONNECT_DISCIPLINE.welcomeBullets.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>

      <p className="mt-4 text-xs text-apex-muted/70">
        {KITE_CONNECT_DISCIPLINE.successNext}
      </p>

      {onDismiss ? (
        <div className="mt-4">
          <ApexButton variant="secondary" className="w-full sm:w-auto" onClick={onDismiss}>
            Got it
          </ApexButton>
        </div>
      ) : null}
    </ApexCard>
  );
}
