"use client";

const SURFACES = [
  { id: "today", label: "Today", available: true },
  { id: "trades", label: "Trades", available: false },
  { id: "proof", label: "Proof", available: false },
  { id: "trust", label: "Trust", available: false },
  { id: "ask", label: "Ask", available: false },
  { id: "you", label: "You", available: false },
] as const;

export default function ApexSurfaceNav() {
  return (
    <nav
      aria-label="APEX surfaces"
      className="-mx-1 flex gap-1 overflow-x-auto pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
    >
      {SURFACES.map((surface) => {
        if (surface.available) {
          return (
            <span
              key={surface.id}
              aria-current="page"
              className="shrink-0 rounded-lg border border-blue-500/25 bg-blue-500/10 px-3 py-1.5 text-[12px] font-medium text-blue-100"
            >
              {surface.label}
            </span>
          );
        }

        return (
          <span
            key={surface.id}
            aria-disabled="true"
            title="Coming soon"
            className="shrink-0 rounded-lg px-3 py-1.5 text-[12px] text-apex-muted/45"
          >
            {surface.label}
          </span>
        );
      })}
    </nav>
  );
}
