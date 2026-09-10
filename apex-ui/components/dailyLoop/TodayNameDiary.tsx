type Props = {
  symbol: string;
  dateKey?: string | null;
  line?: string | null;
};

export default function TodayNameDiary({ symbol, dateKey, line }: Props) {
  if (!line?.trim()) {
    return null;
  }

  return (
    <p className="mt-2 text-xs leading-relaxed text-apex-muted/75">
      You wrote{dateKey ? ` · ${dateKey}` : ""} on {symbol}: {line}
    </p>
  );
}
