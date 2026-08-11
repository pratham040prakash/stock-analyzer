import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from "react";

type ClassName = string | undefined | false;

function cn(...parts: ClassName[]): string {
  return parts.filter(Boolean).join(" ");
}

export function ApexShell({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <main
      className={cn(
        "relative min-h-screen bg-apex-bg px-4 py-6 text-apex-text sm:px-6 sm:py-10",
        "pb-[max(1.5rem,env(safe-area-inset-bottom))] pt-[max(1.5rem,env(safe-area-inset-top))]",
        className,
      )}
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(59,130,246,0.04),transparent_55%)]" />
      <div className="relative mx-auto w-full max-w-[600px] space-y-6">
        {children}
      </div>
    </main>
  );
}

export function ApexCard({
  children,
  className,
  hover = true,
  padding = "default",
}: {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  padding?: "default" | "compact" | "none";
}) {
  const paddingClass =
    padding === "none"
      ? ""
      : padding === "compact"
        ? "p-5"
        : "p-5 sm:p-6";

  return (
    <div
      className={cn(
        "rounded-2xl border border-apex-border bg-apex-card",
        "shadow-[0_24px_80px_rgba(0,0,0,0.32)]",
        hover &&
          "transition-all duration-200 ease-out hover:-translate-y-0.5 hover:shadow-[0_28px_90px_rgba(0,0,0,0.42)]",
        paddingClass,
        className,
      )}
    >
      {children}
    </div>
  );
}

export function ApexEyebrow({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <p
      className={cn(
        "text-[13px] font-medium text-apex-muted",
        className,
      )}
    >
      {children}
    </p>
  );
}

export function ApexTitle({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <h1
      className={cn(
        "text-[24px] font-bold leading-tight tracking-tight text-apex-text sm:text-[26px]",
        className,
      )}
    >
      {children}
    </h1>
  );
}

export function ApexBody({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <p className={cn("text-[14px] leading-relaxed text-apex-muted", className)}>
      {children}
    </p>
  );
}

type BadgeTone = "success" | "waiting" | "neutral" | "risk" | "insight";

const badgeToneClass: Record<BadgeTone, string> = {
  success: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
  waiting: "border-amber-500/30 bg-amber-500/10 text-amber-200",
  neutral: "border-apex-border bg-apex-bg/80 text-apex-muted",
  risk: "border-red-500/25 bg-red-500/10 text-red-300",
  insight: "border-blue-500/25 bg-blue-500/10 text-blue-200",
};

export function ApexBadge({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: BadgeTone;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider",
        badgeToneClass[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

type ButtonVariant = "primary" | "secondary" | "ghost";

export function ApexButton({
  children,
  className,
  variant = "primary",
  fullWidth = true,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  fullWidth?: boolean;
}) {
  const variantClass: Record<ButtonVariant, string> = {
    primary:
      "bg-emerald-500 text-slate-950 hover:bg-emerald-400 hover:scale-[1.02] active:scale-[0.98]",
    secondary:
      "border border-apex-border bg-apex-bg text-apex-text hover:bg-white/[0.03] hover:scale-[1.02] active:scale-[0.98]",
    ghost:
      "text-apex-muted hover:text-apex-text hover:bg-white/[0.03]",
  };

  return (
    <button
      type="button"
      className={cn(
        "rounded-xl px-4 py-3.5 text-[14px] font-semibold transition-all duration-200 ease-out disabled:cursor-default disabled:opacity-60 disabled:hover:scale-100 min-h-[48px]",
        fullWidth && "w-full",
        variantClass[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}

export function ApexInsight({
  title,
  children,
  className,
}: {
  title: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-xl border border-blue-500/20 bg-blue-500/[0.06] px-4 py-3.5",
        className,
      )}
    >
      <p className="text-[13px] font-semibold text-blue-200">{title}</p>
      <div className="mt-2.5">{children}</div>
    </div>
  );
}

export function ApexDivider({ className }: { className?: string }) {
  return <div className={cn("h-px bg-apex-border", className)} />;
}

export function ApexRow({
  label,
  value,
  className,
  valueClassName,
}: {
  label: string;
  value: string;
  className?: string;
  valueClassName?: string;
}) {
  return (
    <div
      className={cn(
        "flex items-start justify-between gap-4 py-2.5",
        className,
      )}
    >
      <span className="text-[13px] text-apex-muted">{label}</span>
      <span
        className={cn(
          "text-right text-[13px] font-medium text-apex-text",
          valueClassName,
        )}
      >
        {value}
      </span>
    </div>
  );
}

export function ApexSection({
  children,
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <section className={cn("space-y-3", className)} {...props}>
      {children}
    </section>
  );
}
