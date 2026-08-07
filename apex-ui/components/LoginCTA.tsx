"use client";

import Link from "next/link";

export default function LoginCTA() {
  return (
    <div className="p-6 rounded-2xl border border-white/10 bg-gradient-to-b from-slate-900 to-slate-900/80 space-y-4">
      <p className="text-sm text-gray-400">
        Sign in to connect your portfolio and get one clear action for today.
      </p>
      <Link
        href="/login"
        className="inline-flex px-5 py-2.5 rounded-lg bg-teal-600/90 hover:bg-teal-600 border border-teal-500/30 text-white text-sm font-medium transition-all active:scale-95"
      >
        Sign in to get started
      </Link>
    </div>
  );
}
