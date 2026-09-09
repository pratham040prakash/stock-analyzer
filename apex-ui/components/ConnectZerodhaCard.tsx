"use client";

import { KITE_CONNECT_DISCIPLINE } from "@/lib/gtm/kiteConnectDisciplineCopy";
import {
  markKiteConnectAttempt,
  writeBrokerConnectSkipped,
} from "@/lib/onboarding/brokerConnectPreference";
import { ApexBody, ApexButton, ApexCard, ApexTitle } from "@/components/ui/apex";

type Props = {
  title?: string;
  description?: string;
  buttonLabel?: string;
  subtext?: string;
  onSkip?: () => void;
  skipHref?: string;
  skipLabel?: string;
};

export default function ConnectZerodhaCard({
  title = KITE_CONNECT_DISCIPLINE.connectTitle,
  description = KITE_CONNECT_DISCIPLINE.connectDescription,
  buttonLabel = KITE_CONNECT_DISCIPLINE.connectButton,
  subtext = KITE_CONNECT_DISCIPLINE.connectSubtext,
  onSkip,
  skipHref,
  skipLabel = KITE_CONNECT_DISCIPLINE.skipButton,
}: Props) {
  return (
    <ApexCard>
      <ApexTitle className="text-[20px]">{title}</ApexTitle>
      <ApexBody className="mt-2 max-w-md">{description}</ApexBody>

      <a
        href="/api/zerodha/login"
        className="mt-5 block"
        onClick={() => {
          markKiteConnectAttempt();
        }}
      >
        <ApexButton>{buttonLabel}</ApexButton>
      </a>

      {onSkip ? (
        <div className="mt-3">
          <ApexButton type="button" variant="secondary" onClick={onSkip}>
            {skipLabel}
          </ApexButton>
        </div>
      ) : skipHref ? (
        <a
          href={skipHref}
          className="mt-3 block"
          onClick={() => {
            writeBrokerConnectSkipped(true);
          }}
        >
          <ApexButton type="button" variant="secondary">
            {skipLabel}
          </ApexButton>
        </a>
      ) : null}

      <ApexBody className="mt-3">{subtext}</ApexBody>
      {onSkip ? (
        <ApexBody className="mt-2">{KITE_CONNECT_DISCIPLINE.skipDetail}</ApexBody>
      ) : null}
      <ul className="mt-4 space-y-1 text-xs text-apex-muted/70">
        {KITE_CONNECT_DISCIPLINE.connectBullets.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
    </ApexCard>
  );
}
