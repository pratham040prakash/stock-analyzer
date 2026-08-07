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
  if (severity === "low") return "text-green-400";
  if (severity === "medium") return "text-yellow-400";
  if (severity === "high") return "text-red-400";
  return "text-gray-400";
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
    <div className="bg-slate-900 border border-white/10 rounded-2xl p-6 hover:border-white/20 hover:-translate-y-1 hover:shadow-lg hover:shadow-black/20 transition-all duration-300">
      {label && (
        <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">
          {label}
        </div>
      )}

      <div className="text-lg leading-relaxed text-white mb-4">{message}</div>

      {points && points.length > 0 && (
        <ul className="space-y-1 text-sm">
          {points.map((point) => (
            <li key={point.text} className={severityClass(point.severity)}>
              • {point.text}
            </li>
          ))}
        </ul>
      )}

      {hint && (
        <div className="text-xs text-gray-500 mt-3 italic">{hint}</div>
      )}

      {action && (
        <button
          type="button"
          onClick={onActionClick}
          className="mt-4 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition-all duration-200 active:scale-95 text-sm"
        >
          {action}
        </button>
      )}
    </div>
  );
}
