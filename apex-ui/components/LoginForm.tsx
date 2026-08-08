"use client";

import { useCallback, useEffect, useRef, useState, startTransition } from "react";
import { useSearchParams } from "next/navigation";
import DemoDecisionCard from "@/components/DemoDecisionCard";
import { useAuth } from "@/components/AuthProvider";
import {
  ApexBody,
  ApexButton,
  ApexCard,
  ApexDivider,
  ApexTitle,
} from "@/components/ui/apex";
import {
  SYSTEM_CONFIG_INCOMPLETE_MESSAGE,
} from "@/lib/env/config";
import {
  isNetworkErrorMessage,
  isRateLimitError,
  mapAuthErrorMessage,
} from "@/lib/auth/errors";
import { authError, authLog } from "@/lib/auth/log";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
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
    <ul className="space-y-2 pt-2 text-[13px] text-apex-muted">
      <li>Secure connection</li>
      <li>Read-only access</li>
      <li>No passwords stored</li>
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
          <ApexTitle>Welcome to APEX</ApexTitle>
          <ApexBody className="mt-2">
            Get one clear investment decision every day.
          </ApexBody>
        </div>
        <ApexCard hover={false} padding="compact" className="border-amber-500/20">
          <ApexBody className="text-amber-200/90">
            {SYSTEM_CONFIG_INCOMPLETE_MESSAGE}
          </ApexBody>
        </ApexCard>
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
      const response = await apiFetch("/api/auth/otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: trimmedEmail }),
      });

      const payload = await parseApiJson<{
        status?: string;
        message?: string;
        redirectTo?: string;
      }>(response, "Auth OTP");

      if (!payload) {
        setError("Unable to sign in. Try again.");
        return;
      }

      if (!response.ok) {
        const errMessage = payload.message ?? "Unable to sign in. Try again.";
        authError("Email login error", { message: errMessage });

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
        return;
      }

      authLog("Email OTP sent", {
        email: trimmedEmail,
        redirectTo: payload.redirectTo,
      });
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
      const redirectTo = `${window.location.origin}/auth/callback`;
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

      if (data.url) {
        window.location.assign(data.url);
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
        <ApexTitle>Welcome to APEX</ApexTitle>
        <ApexBody className="mt-2">
          Get one clear investment decision every day.
        </ApexBody>
      </div>

      <DemoDecisionCard />

      <form onSubmit={handleEmailLogin} className="space-y-4">
        <div>
          <label
            htmlFor="email"
            className="mb-2 block text-[13px] text-apex-muted"
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
            className="w-full rounded-xl border border-apex-border bg-apex-card px-4 py-3 text-apex-text placeholder:text-apex-muted focus:border-blue-500/40 focus:outline-none disabled:opacity-60"
          />
        </div>

        <ApexButton type="submit" disabled={emailActionDisabled}>
          {loading ? (
            <span className="inline-flex items-center justify-center gap-2">
              <ButtonSpinner />
              {getEmailButtonLabel()}
            </span>
          ) : (
            getEmailButtonLabel()
          )}
        </ApexButton>
      </form>

      {message ? (
        <div className="space-y-2">
          <ApexBody className="text-emerald-200/90">{message}</ApexBody>
          {showEmailFallback ? (
            <ApexBody>{EMAIL_FALLBACK_MESSAGE}</ApexBody>
          ) : null}
        </div>
      ) : null}
      {displayError ? (
        <p className="text-[13px] text-red-300/90">{displayError}</p>
      ) : null}

      <ApexDivider />

      <ApexButton
        type="button"
        variant="secondary"
        disabled={googleActionDisabled}
        onClick={() => void handleGoogleLogin()}
      >
        {isGoogleLoading ? (
          <span className="inline-flex items-center justify-center gap-2">
            <ButtonSpinner />
            Continuing with Google…
          </span>
        ) : (
          "Continue with Google"
        )}
      </ApexButton>

      <TrustIndicators />
    </div>
  );
}
