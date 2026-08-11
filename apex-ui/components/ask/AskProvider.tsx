"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import AskOverlay from "@/components/ask/AskOverlay";

type AskContextValue = {
  open: boolean;
  openAsk: () => void;
  closeAsk: () => void;
};

const AskContext = createContext<AskContextValue | null>(null);

export function AskProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);

  const openAsk = useCallback(() => setOpen(true), []);
  const closeAsk = useCallback(() => setOpen(false), []);

  const value = useMemo(
    () => ({ open, openAsk, closeAsk }),
    [closeAsk, open, openAsk],
  );

  return (
    <AskContext.Provider value={value}>
      {children}
      <AskOverlay open={open} onClose={closeAsk} />
    </AskContext.Provider>
  );
}

export function useAskOverlay(): AskContextValue {
  const context = useContext(AskContext);

  if (!context) {
    throw new Error("useAskOverlay must be used within AskProvider");
  }

  return context;
}
