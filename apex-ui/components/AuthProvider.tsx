"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { createClient, isSupabaseConfigured } from "@/lib/supabase/client";
import { authDebug, authLog } from "@/lib/auth/log";
import type { User, SupabaseClient } from "@supabase/supabase-js";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  supabase: SupabaseClient | null;
  configured: boolean;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const configured = isSupabaseConfigured();
  const supabase = useMemo(
    () => (configured ? createClient() : null),
    [configured],
  );

  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(configured);

  useEffect(() => {
    if (!supabase) {
      authDebug("Auth provider skipped — Supabase not configured");
      return;
    }

    supabase.auth.getSession().then(({ data: { session } }) => {
      authDebug("Initial session loaded", {
        hasSession: Boolean(session),
        userId: session?.user?.id,
      });
      setUser(session?.user ?? null);
      setLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      authLog("Auth event", { event, userId: session?.user?.id ?? null });
      setUser(session?.user ?? null);
      setLoading(false);

      if (session && event === "SIGNED_IN") {
        authLog("Session active — refreshing app state");
        window.location.reload();
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [supabase]);

  useEffect(() => {
    if (!supabase) return;

    const onVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        void supabase.auth.startAutoRefresh();
        window.location.reload();
      } else {
        supabase.auth.stopAutoRefresh();
      }
    };

    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => {
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [supabase]);

  async function signOut() {
    if (!supabase) return;
    authLog("Sign out clicked");
    await supabase.auth.signOut();
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, supabase, configured, signOut }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
