type Props = {
  line: string;
};

export default function TodayDeskStatus({ line }: Props) {
  if (!line.trim()) {
    return null;
  }

  return (
    <p className="text-center text-sm leading-relaxed text-apex-muted/75">{line}</p>
  );
}
