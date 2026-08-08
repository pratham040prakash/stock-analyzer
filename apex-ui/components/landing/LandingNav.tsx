import Link from "next/link";

export default function LandingNav() {
  return (
    <header className="relative z-10 border-b border-apex-border/80 bg-apex-bg/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-5 py-4 sm:px-6">
        <div className="text-[13px] font-medium tracking-wide text-apex-muted">
          APEX · Your Investment Mentor
        </div>
        <Link
          href="/login?next=/app"
          className="text-[13px] font-medium text-apex-text transition-colors hover:text-white"
        >
          Sign in
        </Link>
      </div>
    </header>
  );
}
