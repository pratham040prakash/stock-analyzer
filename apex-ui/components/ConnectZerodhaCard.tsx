import { KITE_CONNECT_DISCIPLINE } from "@/lib/gtm/kiteConnectDisciplineCopy";
import { ApexBody, ApexButton, ApexCard, ApexTitle } from "@/components/ui/apex";

type Props = {
  title?: string;
  description?: string;
  buttonLabel?: string;
  subtext?: string;
};

export default function ConnectZerodhaCard({
  title = KITE_CONNECT_DISCIPLINE.connectTitle,
  description = KITE_CONNECT_DISCIPLINE.connectDescription,
  buttonLabel = KITE_CONNECT_DISCIPLINE.connectButton,
  subtext = KITE_CONNECT_DISCIPLINE.connectSubtext,
}: Props) {
  return (
    <ApexCard>
      <ApexTitle className="text-[20px]">{title}</ApexTitle>
      <ApexBody className="mt-2 max-w-md">{description}</ApexBody>

      <a href="/api/zerodha/login" className="mt-5 block">
        <ApexButton>{buttonLabel}</ApexButton>
      </a>

      <ApexBody className="mt-3">{subtext}</ApexBody>
      <ul className="mt-4 space-y-1 text-xs text-apex-muted/70">
        {KITE_CONNECT_DISCIPLINE.connectBullets.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
    </ApexCard>
  );
}
