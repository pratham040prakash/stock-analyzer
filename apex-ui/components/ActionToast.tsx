"use client";

type Props = {
  message: string | null;
};

export default function ActionToast({ message }: Props) {
  if (!message) {
    return null;
  }

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[60] px-5 py-3 rounded-xl bg-emerald-950/95 border border-emerald-500/30 text-sm text-emerald-100 shadow-lg backdrop-blur-sm">
      {message}
    </div>
  );
}
