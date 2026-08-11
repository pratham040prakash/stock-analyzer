"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const SURFACES = [
  { href: "/app", label: "Today" },
  { href: "/app/portfolio", label: "Portfolio" },
  { href: "/app/research", label: "Research" },
  { href: "/app/review", label: "Review" },
  { href: "/app/you", label: "You" },
] as const;

export default function ApexSurfaceNav() {
  const pathname = usePathname();

  return (
    <nav aria-label="APEX surfaces" className="flex flex-wrap gap-2">
      {SURFACES.map((surface) => {
        const active =
          surface.href === "/app"
            ? pathname === "/app"
            : pathname.startsWith(surface.href);

        return (
          <Link
            key={surface.href}
            href={surface.href}
            aria-current={active ? "page" : undefined}
            className={
              active
                ? "inline-flex rounded-lg border border-blue-500/25 bg-blue-500/10 px-3 py-1.5 text-[12px] font-medium text-blue-100"
                : "inline-flex rounded-lg border border-apex-border/20 px-3 py-1.5 text-[12px] font-medium text-apex-muted transition-colors hover:text-apex-text"
            }
          >
            {surface.label}
          </Link>
        );
      })}
    </nav>
  );
}
