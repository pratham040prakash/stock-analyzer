"use client";

import { useCallback, useEffect, useRef, useState, startTransition } from "react";
import { useSearchParams } from "next/navigation";
import DemoDecisionCard from "@/components/DemoDecisionCard";
import { useAuth } from "@/components/AuthProvider";
import {
  getAuthCallbackUrl,
  SYSTEM_CONFIG_INCOMPLETE_MESSAGE,
} from "@/lib/env/config";
import {
  isNetworkErrorMessage,
  isRateLimitError,
  mapAuthErrorMessage,
} from "@/lib/auth/errors";
import { authError, authLog } from "@/lib/auth/log";
import {
  getOtpCooldownRemaining,
  markOtpSent,
  OTP_COOLDOWN_SECONDS,
} from "@/lib/auth/otpCooldown";

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
}

function ButtonSpinner() {
  return (
    <span
      className="inline-block h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin"
      aria-hidden
    />
  );
}

function TrustIndicators() {
  return (
    <ul className="space-y-2 text-sm text-gray-400 pt-2">
      <li className="flex items-center gap-2">
        <span className="text-green-400">✓</span>
        Secure connection
      </li>
      <li className="flex items-center gap-2">
        <span className="text-green-400">✓</span>
        Read-only access
      </li>
      <li className="flex items-center gap-2">
        <span className="text-green-400">✓</span>
        No passwords stored
      </li>
    </ul>
  );
}

const RATE_LIMIT_MESSAGE =
  "You're already set — your login link is on the way. Give it a moment.";
const OTP_SUCCESS_MESSAGE =
  "Check your email — your login link is on the way.";
const EMAIL_FALLBACK_MESSAGE =
  "Didn't receive the email? Check spam or try Google login.";

export default function LoginForm() {
  const searchParams = useSearchParams();
  const { supabase, configured } = useAuth();
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const [otpSent, setOtpSent] = useState(false);
  const [showEmailFallback, setShowEmailFallback] = useState(false);
  const emailRequestInFlight = useRef(false);
  const googleRequestInFlight = useRef(false);
  const fallbackTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const callbackError = searchParams.get("error");
  const urlError = callbackError ? decodeURIComponent(callbackError) : null;
  const displayError = error ?? urlError;
  const emailActionDisabled = loading || cooldown > 0;
  const googleActionDisabled = isGoogleLoading || loading;

  const beginOtpCooldown = useCallback(() => {
    markOtpSent();
    setCooldown(OTP_COOLDOWN_SECONDS);
    setOtpSent(true);
    if (fallbackTimerRef.current) clearTimeout(fallbackTimerRef.current);
    fallbackTimerRef.current = setTimeout(() => {
      setShowEmailFallback(true);
    }, 15000);
  }, []);

  const resetEmailStatus = useCallback(() => {
    if (fallbackTimerRef.current) {
      clearTimeout(fallbackTimerRef.current);
      fallbackTimerRef.current = null;
    }
    setShowEmailFallback(false);
    setMessage(null);
    setError(null);
  }, []);

  useEffect(() => {
    if (callbackError) {
      authError("Login page received callback error", { callbackError });
    }
  }, [callbackError]);

  useEffect(() => {
    const remaining = getOtpCooldownRemaining();
    if (remaining <= 0) return;

    const elapsedMs = OTP_COOLDOWN_SECONDS * 1000 - remaining * 1000;
    const fallbackDelayMs = Math.max(15000 - elapsedMs, 0);

    startTransition(() => {
      setCooldown(remaining);
      setOtpSent(true);
      setMessage(OTP_SUCCESS_MESSAGE);
    });

    fallbackTimerRef.current = setTimeout(() => {
      setShowEmailFallback(true);
    }, fallbackDelayMs);
  }, []);

  useEffect(() => {
    if (cooldown <= 0) return;

    const timer = setInterval(() => {
      setCooldown((current) => current - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [cooldown]);

  useEffect(() => {
    return () => {
      if (fallbackTimerRef.current) clearTimeout(fallbackTimerRef.current);
    };
  }, []);

  if (!configured) {
    return (
      <div className="w-full max-w-md space-y-6">
        <div>
          <h1 className="text-3xl font-semibold text-white mb-2">Welcome to APEX</h1>
          <p className="text-sm text-gray-400">
            Get one clear investment decision every day.
          </p>
        </div>
        <div className="p-4 rounded-xl border border-amber-500/20 bg-amber-500/5">
          <p className="text-sm text-amber-200/90">
            {SYSTEM_CONFIG_INCOMPLETE_MESSAGE}
          </p>
        </div>
      </div>
    );
  }

  function getEmailButtonLabel(): string {
    if (cooldown > 0) return `Link sent · retry in ${cooldown}s`;
    if (loading) return "Sending link...";
    if (otpSent) return "Resend link";
    return "Get my daily decision";
  }

  async function handleEmailLogin(event: React.FormEvent) {
    event.preventDefault();

    if (emailRequestInFlight.current || loading || cooldown > 0) return;

    emailRequestInFlight.current = true;
    setLoading(true);
    resetEmailStatus();

    const trimmedEmail = email.trim();
    if (!trimmedEmail || !isValidEmail(trimmedEmail)) {
      setError("Enter a valid email");
      emailRequestInFlight.current = false;
      setLoading(false);
      return;
    }

    if (!supabase) {
      setError(SYSTEM_CONFIG_INCOMPLETE_MESSAGE);
      emailRequestInFlight.current = false;
      setLoading(false);
      return;
    }

    authLog("Email login click", { email: trimmedEmail });

    try {
      const redirectTo = getAuthCallbackUrl();
      authLog("Email OTP request", { redirectTo });

      const { error: signInError } = await supabase.auth.signInWithOtp({
        email: trimmedEmail,
        options: {
          emailRedirectTo: redirectTo,
          shouldCreateUser: true,
        },
      });

      if (signInError) {
        authError("Email login error", { message: signInError.message });

        if (isRateLimitError(signInError.message)) {
          setMessage(RATE_LIMIT_MESSAGE);
          beginOtpCooldown();
          return;
        }

        if (isNetworkErrorMessage(signInError.message)) {
          setError(mapAuthErrorMessage(signInError));
          return;
        }

        setError(mapAuthErrorMessage(signInError));
        return;
      }

      authLog("Email OTP sent", { email: trimmedEmail });
      setMessage(OTP_SUCCESS_MESSAGE);
      beginOtpCooldown();
    } catch (err) {
      const errMessage =
        err instanceof Error ? err.message : "Unable to sign in. Try again.";
      authError("Email login exception", { message: errMessage });

      if (isRateLimitError(errMessage)) {
        setMessage(RATE_LIMIT_MESSAGE);
        beginOtpCooldown();
        return;
      }

      if (isNetworkErrorMessage(errMessage)) {
        setError(mapAuthErrorMessage({ message: errMessage }));
        return;
      }

      setError(mapAuthErrorMessage({ message: errMessage }));
    } finally {
      emailRequestInFlight.current = false;
      setLoading(false);
    }
  }

  async function handleGoogleLogin() {
    if (googleRequestInFlight.current || isGoogleLoading) return;

    if (!supabase) {
      setError(SYSTEM_CONFIG_INCOMPLETE_MESSAGE);
      return;
    }

    googleRequestInFlight.current = true;
    setIsGoogleLoading(true);
    setError(null);
    authLog("Google login click");

    try {
      const redirectTo = getAuthCallbackUrl();
      authLog("Google OAuth redirect", { redirectTo });

      const { data, error: signInError } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo,
          queryParams: {
            access_type: "offline",
            prompt: "consent",
          },
        },
      });

      if (signInError) {
        authError("Google OAuth error", { message: signInError.message });
        setError(mapAuthErrorMessage(signInError));
        googleRequestInFlight.current = false;
        setIsGoogleLoading(false);
        return;
      }

      authLog("Google OAuth initiated", { url: data.url });
    } catch (err) {
      const errMessage =
        err instanceof Error ? err.message : "Unable to sign in. Try again.";
      authError("Google OAuth exception", { message: errMessage });
      setError(mapAuthErrorMessage({ message: errMessage }));
      googleRequestInFlight.current = false;
      setIsGoogleLoading(false);
    }
  }

  return (
    <div className="w-full max-w-md space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-white mb-2">Welcome to APEX</h1>
        <p className="text-sm text-gray-400">
          Get one clear investment decision every day.
        </p>
      </div>

      <DemoDecisionCard />

      <form onSubmit={handleEmailLogin} className="space-y-4">
        <div>
          <label
            htmlFor="email"
            className="block text-xs text-gray-400 uppercase tracking-wider mb-2"
          >
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(event) => {
              setEmail(event.target.value);
              if (error) setError(null);
            }}
            placeholder="you@example.com"
            disabled={emailActionDisabled}
            className="w-full px-4 py-3 rounded-lg bg-slate-900 border border-white/10 text-white placeholder:text-gray-500 focus:outline-none focus:border-teal-500/40 disabled:opacity-60"
          />
          <p className="mt-2 text-xs text-gray-500">
            We&apos;ll create an account if you&apos;re new.
          </p>
        </div>

        <button
          type="submit"
          disabled={emailActionDisabled}
          className="w-full px-4 py-3 rounded-lg bg-teal-600/90 hover:bg-teal-600 disabled:opacity-60 disabled:cursor-not-allowed text-white text-sm font-medium transition-all inline-flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <ButtonSpinner />
              <span>{getEmailButtonLabel()}</span>
            </>
          ) : (
            getEmailButtonLabel()
          )}
        </button>
      </form>

      {message && (
        <div className="space-y-2">
          <p className="text-sm text-teal-300/90">{message}</p>
          {showEmailFallback && (
            <p className="text-sm text-gray-400">{EMAIL_FALLBACK_MESSAGE}</p>
          )}
        </div>
      )}
      {displayError && <p className="text-sm text-red-300/90">{displayError}</p>}

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-white/10" />
        </div>
        <div className="relative flex justify-center text-xs">
          <span className="bg-slate-950 px-3 text-gray-500">or</span>
        </div>
      </div>

      <div className="space-y-2">
        <button
          type="button"
          onClick={() => void handleGoogleLogin()}
          disabled={googleActionDisabled}
          className="w-full px-4 py-3 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 disabled:opacity-60 disabled:cursor-not-allowed text-white text-sm font-medium transition-all inline-flex items-center justify-center gap-2"
        >
          {isGoogleLoading ? (
            <>
              <ButtonSpinner />
              <span>Continuing with Google...</span>
            </>
          ) : (
            "Continue with Google"
          )}
        </button>
        <p className="text-xs text-gray-500 text-center">
          No account? We&apos;ll create one instantly.
        </p>
      </div>

      <TrustIndicators />
    </div>
  );
}
