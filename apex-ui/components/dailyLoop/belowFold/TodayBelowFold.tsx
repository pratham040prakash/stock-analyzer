"use client";

import type { MorningBriefViewModel } from "@/types/morningBrief";

function ZoneShell({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-3 space-y-2">
      <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
        {title}
      </p>
      {children}
    </section>
  );
}

export function PortfolioIntelligenceZone({
  portfolio,
}: {
  portfolio: MorningBriefViewModel["portfolio"];
}) {
  return (
    <ZoneShell title="Portfolio intelligence">
      <p className="text-sm text-apex-text/85">{portfolio.summary}</p>
      <div className="flex flex-wrap gap-3 text-xs text-apex-muted/80">
        <span>{portfolio.holdings_count} holdings</span>
        {portfolio.day_pnl !== null ? (
          <span>Day P&L ₹{Math.round(portfolio.day_pnl).toLocaleString("en-IN")}</span>
        ) : null}
        {portfolio.open_pnl !== null ? (
          <span>Open P&L ₹{Math.round(portfolio.open_pnl).toLocaleString("en-IN")}</span>
        ) : null}
      </div>
    </ZoneShell>
  );
}

export function OpportunityZone({
  opportunity,
}: {
  opportunity: MorningBriefViewModel["opportunity"];
}) {
  if (!opportunity.visible || !opportunity.symbol) {
    return null;
  }

  return (
    <ZoneShell title="Top opportunity">
      <p className="text-sm font-medium text-apex-text">{opportunity.symbol}</p>
      <p className="text-sm text-apex-muted/85">{opportunity.setup}</p>
      <p className="text-xs text-apex-muted/65">Lane · {opportunity.lane}</p>
    </ZoneShell>
  );
}

export function RiskMonitorZone({ risk }: { risk: MorningBriefViewModel["risk"] }) {
  return (
    <ZoneShell title="Risk monitor">
      <p className="text-sm text-apex-text/85">Risk level · {risk.level}</p>
      {risk.session_ribbon.length > 0 ? (
        <p className="text-xs text-apex-muted/75">{risk.session_ribbon.join(" · ")}</p>
      ) : null}
      {risk.warnings.length > 0 ? (
        <ul className="space-y-1 text-xs text-amber-100/80">
          {risk.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      ) : (
        <p className="text-xs text-apex-muted/70">No active risk warnings.</p>
      )}
    </ZoneShell>
  );
}

export function MarketContextZone({
  market,
}: {
  market: MorningBriefViewModel["market"];
}) {
  return (
    <ZoneShell title="Market context">
      <p className="text-sm text-apex-text/85">{market.market_label}</p>
      <p className="text-xs text-apex-muted/75">{market.guidance}</p>
      <p className="text-xs text-apex-muted/60">{market.pnl_line}</p>
    </ZoneShell>
  );
}

export function DisciplineZone({
  discipline,
}: {
  discipline: MorningBriefViewModel["discipline"];
}) {
  return (
    <ZoneShell title="Discipline score">
      <p className="text-sm text-apex-text/85">
        Process score {discipline.process_score}/100
      </p>
      <p className="text-xs text-apex-muted/75">{discipline.streak_message}</p>
      <p className="text-xs text-apex-muted/60">
        Followed {discipline.followed_days} · Wait days {discipline.wait_days}
      </p>
    </ZoneShell>
  );
}

export default function TodayBelowFold({
  brief,
}: {
  brief: MorningBriefViewModel;
}) {
  return (
    <div className="space-y-3 [content-visibility:auto]">
      <PortfolioIntelligenceZone portfolio={brief.portfolio} />
      <OpportunityZone opportunity={brief.opportunity} />
      <RiskMonitorZone risk={brief.risk} />
      <MarketContextZone market={brief.market} />
      <DisciplineZone discipline={brief.discipline} />
    </div>
  );
}
