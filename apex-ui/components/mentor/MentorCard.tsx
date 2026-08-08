import { ApexBody, ApexButton, ApexCard, ApexEyebrow, ApexTitle } from "@/components/ui/apex";

type InsightSeverity = "low" | "medium" | "high";

export type MentorPoint = {
  text: string;
  severity?: InsightSeverity;
};

type Props = {
  label?: string;
  message: string;
  points?: MentorPoint[];
  hint?: string;
  action?: string;
  onActionClick?: () => void;
};

function severityClass(severity?: InsightSeverity): string {
  if (severity === "low") return "text-emerald-300";
  if (severity === "medium") return "text-amber-200";
  if (severity === "high") return "text-red-300";
  return "text-apex-muted";
}

export default function MentorCard({
  label,
  message,
  points,
  hint,
  action,
  onActionClick,
}: Props) {
  return (
    <ApexCard>
      {label ? <ApexEyebrow className="mb-2">{label}</ApexEyebrow> : null}

      <ApexTitle className="text-[18px] font-semibold">{message}</ApexTitle>

      {points && points.length > 0 ? (
        <ul className="mt-4 space-y-2">
          {points.map((point) => (
            <li
              key={point.text}
              className={`text-[13px] ${severityClass(point.severity)}`}
            >
              • {point.text}
            </li>
          ))}
        </ul>
      ) : null}

      {hint ? <ApexBody className="mt-3 italic">{hint}</ApexBody> : null}

      {action ? (
        <ApexButton
          className="mt-4"
          variant="secondary"
          onClick={onActionClick}
        >
          {action}
        </ApexButton>
      ) : null}
    </ApexCard>
  );
}
