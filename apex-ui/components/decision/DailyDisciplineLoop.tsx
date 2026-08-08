type Props = {
  updatedAt?: string | null;
  className?: string;
};

function formatTime(date: Date): string {
  return date.toLocaleTimeString("en-IN", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

function formatUpdatedLabel(updatedAt?: string | null): string {
  const date = updatedAt ? new Date(updatedAt) : new Date();

  if (Number.isNaN(date.getTime())) {
    return `Updated today at ${formatTime(new Date())}`;
  }

  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();

  if (isToday) {
    return `Updated today at ${formatTime(date)}`;
  }

  const dayLabel = date.toLocaleDateString("en-IN", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });

  return `Updated ${dayLabel} at ${formatTime(date)}`;
}

export default function DailyDisciplineLoop({
  updatedAt,
  className = "",
}: Props) {
  return (
    <div
      className={[
        "rounded-2xl border border-apex-border/40 bg-apex-bg/30 px-5 py-4",
        className,
      ].join(" ")}
    >
      <ul className="space-y-2.5 text-[13px] leading-relaxed text-apex-muted">
        <li>{formatUpdatedLabel(updatedAt)}</li>
        <li>This decision is valid for today only</li>
        <li className="italic">
          Check again tomorrow for the next opportunity
        </li>
      </ul>
    </div>
  );
}
