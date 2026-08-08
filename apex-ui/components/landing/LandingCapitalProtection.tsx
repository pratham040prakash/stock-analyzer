import type { ReactNode } from "react";
import LandingSection from "./LandingSection";

type TrustBlock = {
  title: string;
  body: string;
  icon: ReactNode;
  accent: string;
};

function ShieldIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      className="h-6 w-6"
      aria-hidden
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 3 4 6v6c0 5 3.5 8.5 8 9 4.5-.5 8-4 8-9V6l-8-3Z"
      />
      <path strokeLinecap="round" d="M9.5 12.5 11 14l3.5-3.5" />
    </svg>
  );
}

function PauseIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      className="h-6 w-6"
      aria-hidden
    >
      <circle cx="12" cy="12" r="9" />
      <path strokeLinecap="round" d="M10 9v6M14 9v6" />
    </svg>
  );
}

function DisciplineIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      className="h-6 w-6"
      aria-hidden
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 3v3M12 18v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M3 12h3M18 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"
      />
      <circle cx="12" cy="12" r="3.5" />
    </svg>
  );
}

function FrameworkIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      className="h-6 w-6"
      aria-hidden
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M4 7h16M4 12h10M4 17h16"
      />
      <rect x="15" y="10" width="5" height="5" rx="1" />
    </svg>
  );
}

const BLOCKS: TrustBlock[] = [
  {
    title: "Risk-first system",
    body: "Every decision is protected with strict risk controls",
    icon: <ShieldIcon />,
    accent: "border-emerald-500/25 bg-emerald-500/10 text-emerald-300",
  },
  {
    title: "No overtrading",
    body: "Most days, the right move is to do nothing",
    icon: <PauseIcon />,
    accent: "border-amber-500/25 bg-amber-500/10 text-amber-200",
  },
  {
    title: "Discipline over emotion",
    body: "No chasing, no panic, no guesswork",
    icon: <DisciplineIcon />,
    accent: "border-blue-500/25 bg-blue-500/10 text-blue-200",
  },
  {
    title: "Proven decision framework",
    body: "Every action is based on structured analysis, not opinions",
    icon: <FrameworkIcon />,
    accent: "border-apex-border bg-apex-bg/80 text-apex-muted",
  },
];

export default function LandingCapitalProtection() {
  return (
    <LandingSection className="py-16 sm:py-20">
      <div className="max-w-[640px]">
        <h2 className="text-[24px] font-bold tracking-tight text-apex-text sm:text-[28px]">
          Built to protect and grow your capital
        </h2>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-5">
        {BLOCKS.map((block) => (
          <article
            key={block.title}
            className="flex h-full flex-col rounded-2xl border border-apex-border bg-apex-card p-5 shadow-[0_24px_80px_rgba(0,0,0,0.32)] transition-all duration-200 ease-out hover:-translate-y-0.5 hover:shadow-[0_28px_90px_rgba(0,0,0,0.42)] sm:p-6"
          >
            <div
              className={`inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border ${block.accent}`}
            >
              {block.icon}
            </div>

            <h3 className="mt-4 text-[16px] font-semibold text-apex-text">
              {block.title}
            </h3>
            <p className="mt-2 flex-1 text-[14px] leading-relaxed text-apex-muted">
              {block.body}
            </p>
          </article>
        ))}
      </div>
    </LandingSection>
  );
}
