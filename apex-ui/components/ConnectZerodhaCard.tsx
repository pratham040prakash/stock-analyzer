import { ApexBody, ApexButton, ApexCard, ApexTitle } from "@/components/ui/apex";

type Props = {
  title?: string;
  description?: string;
  buttonLabel?: string;
  subtext?: string;
};

export default function ConnectZerodhaCard({
  title = "Connect your portfolio",
  description = "A secure link to Zerodha — read-only, nothing manual.",
  buttonLabel = "Connect Zerodha",
  subtext = "Takes less than 10 seconds",
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
        <li>Read-only — APEX never places trades without you.</li>
        <li>Your login stays with Zerodha; we only sync holdings and cash.</li>
      </ul>
    </ApexCard>
  );
}
