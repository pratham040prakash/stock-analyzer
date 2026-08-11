"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type Options = {
  enabled: boolean;
  onRefresh: () => void | Promise<void>;
  thresholdPx?: number;
};

export function usePullToRefresh({
  enabled,
  onRefresh,
  thresholdPx = 72,
}: Options) {
  const [pullDistance, setPullDistance] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const startYRef = useRef<number | null>(null);
  const pullingRef = useRef(false);
  const pullDistanceRef = useRef(0);
  const onRefreshRef = useRef(onRefresh);

  useEffect(() => {
    onRefreshRef.current = onRefresh;
  }, [onRefresh]);

  const triggerRefresh = useCallback(async () => {
    if (isRefreshing) {
      return;
    }

    setIsRefreshing(true);
    setPullDistance(0);

    try {
      await onRefreshRef.current();
    } finally {
      setIsRefreshing(false);
    }
  }, [isRefreshing]);

  useEffect(() => {
    if (!enabled || typeof window === "undefined") {
      return;
    }

    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;

    const onTouchStart = (event: TouchEvent) => {
      if (window.scrollY > 0 || isRefreshing) {
        startYRef.current = null;
        pullingRef.current = false;
        return;
      }

      startYRef.current = event.touches[0]?.clientY ?? null;
      pullingRef.current = true;
    };

    const onTouchMove = (event: TouchEvent) => {
      if (!pullingRef.current || startYRef.current === null) {
        return;
      }

      const currentY = event.touches[0]?.clientY ?? startYRef.current;
      const delta = Math.max(0, currentY - startYRef.current);

      if (delta <= 0) {
        setPullDistance(0);
        return;
      }

      if (prefersReducedMotion) {
        return;
      }

      setPullDistance(Math.min(delta, thresholdPx * 1.5));
      pullDistanceRef.current = Math.min(delta, thresholdPx * 1.5);
    };

    const onTouchEnd = () => {
      if (!pullingRef.current) {
        return;
      }

      const shouldRefresh = pullDistanceRef.current >= thresholdPx;
      startYRef.current = null;
      pullingRef.current = false;
      pullDistanceRef.current = 0;

      if (shouldRefresh) {
        void triggerRefresh();
        return;
      }

      setPullDistance(0);
    };

    document.addEventListener("touchstart", onTouchStart, { passive: true });
    document.addEventListener("touchmove", onTouchMove, { passive: true });
    document.addEventListener("touchend", onTouchEnd);

    return () => {
      document.removeEventListener("touchstart", onTouchStart);
      document.removeEventListener("touchmove", onTouchMove);
      document.removeEventListener("touchend", onTouchEnd);
    };
  }, [enabled, isRefreshing, thresholdPx, triggerRefresh]);

  return {
    pullDistance,
    isRefreshing,
    triggerRefresh,
  };
}
