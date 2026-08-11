"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import type { ApexTier, TierFeatures } from "@/services/subscription/tier";
import { tierFeatures } from "@/services/subscription/tier";
import type { PremiumTrialView } from "@/services/subscription/conversionFunnel";

type TierResponse = {
  tier: ApexTier;
  features: TierFeatures;
  activationEnabled?: boolean;
  billingEnabled?: boolean;
  trial?: PremiumTrialView;
};

const EMPTY_TRIAL: PremiumTrialView = {
  status: "none",
  enabled: true,
  days: 7,
  headline: "",
  body: "",
  expiresAt: null,
  daysRemaining: null,
};

const FREE_FEATURES = tierFeatures("free");

export function usePremiumTier(enabled = true) {
  const [tier, setTier] = useState<ApexTier>("free");
  const [features, setFeatures] = useState<TierFeatures>(FREE_FEATURES);
  const [activationEnabled, setActivationEnabled] = useState(false);
  const [billingEnabled, setBillingEnabled] = useState(false);
  const [trial, setTrial] = useState<PremiumTrialView>(EMPTY_TRIAL);
  const [loading, setLoading] = useState(enabled);
  const requestRef = useRef(0);

  const refresh = useCallback(async () => {
    if (!enabled) {
      setTier("free");
      setFeatures(FREE_FEATURES);
      setActivationEnabled(false);
      setBillingEnabled(false);
      setTrial(EMPTY_TRIAL);
      setLoading(false);
      return;
    }

    const requestId = ++requestRef.current;
    setLoading(true);

    try {
      const res = await apiFetch("/api/subscription/tier", { method: "GET" });
      const data = await parseApiJson<TierResponse>(res, "Subscription tier");

      if (requestId !== requestRef.current) {
        return;
      }

      if (!res.ok || !data) {
        setTier("free");
        setFeatures(FREE_FEATURES);
        setActivationEnabled(false);
        setBillingEnabled(false);
        setTrial(EMPTY_TRIAL);
        return;
      }

      setTier(data.tier ?? "free");
      setFeatures(data.features ?? tierFeatures(data.tier ?? "free"));
      setActivationEnabled(Boolean(data.activationEnabled));
      setBillingEnabled(Boolean(data.billingEnabled));
      setTrial(data.trial ?? EMPTY_TRIAL);
    } catch {
      if (requestId !== requestRef.current) {
        return;
      }
      setTier("free");
      setFeatures(FREE_FEATURES);
      setActivationEnabled(false);
      setBillingEnabled(false);
      setTrial(EMPTY_TRIAL);
    } finally {
      if (requestId === requestRef.current) {
        setLoading(false);
      }
    }
  }, [enabled]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return {
    tier,
    features,
    isPremium: tier === "premium",
    activationEnabled,
    billingEnabled,
    trial,
    loading,
    refresh,
  };
}
