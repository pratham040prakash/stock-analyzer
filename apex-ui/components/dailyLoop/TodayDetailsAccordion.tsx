"use client";

import type { ReactNode } from "react";

export type TodayDetailsAccordionProps = {
  children: ReactNode;
  className?: string;
};

export default function TodayDetailsAccordion({
  children,
  className = "",
}: TodayDetailsAccordionProps) {
  return (
    <details
      className={`group rounded-xl border border-apex-border/15 bg-white/[0.02] ${className}`.trim()}
    >
      <summary className="cursor-pointer list-none px-4 py-3 text-sm font-medium text-apex-text/85 marker:content-none [&::-webkit-details-marker]:hidden">
        <span className="inline-flex items-center gap-2">
          Details
          <span className="text-xs font-normal text-apex-muted/60 group-open:hidden">
            Progress · monitor · depth
          </span>
        </span>
      </summary>
      <div className="space-y-4 border-t border-apex-border/10 px-4 py-4">
        {children}
      </div>
    </details>
  );
}
