"use client";

type Props = {
  message: string | null;
};

export default function MentorToast({ message }: Props) {
  if (!message) return null;

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 px-4 py-3 rounded-xl bg-slate-800/95 border border-white/10 text-sm text-gray-200 shadow-lg backdrop-blur-sm">
      {message}
    </div>
  );
}
