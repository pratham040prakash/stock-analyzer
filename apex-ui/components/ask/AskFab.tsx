"use client";

import { useAskOverlay } from "@/components/ask/AskProvider";

export default function AskFab() {
  const { openAsk } = useAskOverlay();

  return (
    <button
      type="button"
      onClick={openAsk}
      aria-label="Ask APEX"
      className="fixed bottom-5 right-5 z-40 rounded-full border border-apex-border/30 bg-[#F5F5F7] px-4 py-3 text-sm font-semibold text-[#0A0A0B] shadow-lg transition-transform hover:scale-[1.02]"
    >
      Ask
    </button>
  );
}
