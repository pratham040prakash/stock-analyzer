type Props = {
  heartbeat: string;
  interrupt: string;
};

export default function TodayDeskStatus({ heartbeat, interrupt }: Props) {
  return (
    <p className="text-center text-[11px] font-medium uppercase tracking-[0.16em] text-apex-muted/65">
      {heartbeat} · {interrupt}
    </p>
  );
}
