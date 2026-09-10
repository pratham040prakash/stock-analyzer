"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { buildCapitalDecision } from "@/lib/dailyLoop/capitalDecision";
import { resolveTodayHero, resolveTodayHeroDisplay, enrichTodayHeroWithSellTrim } from "@/lib/dailyLoop/todaySurface";
import { getBrokerStepLine,
} from "@/lib/dailyLoop/disciplineStreak";
import {
  markBrokerStepCompleted,
  markBrokerStepSkipped,
  readBrokerStepCompleted,
  readBrokerStepSkipped,
} from "@/lib/dailyLoop/brokerStepState";
import { getIntentExperience } from "@/lib/dailyLoop/intentExperience";
import { useDailyLoop } from "@/lib/useDailyLoop";
import { useDisciplineStreak } from "@/lib/useDisciplineStreak";
import { useIntentTransition } from "@/lib/useIntentTransition";
import type { EntryTimingState } from "@/components/decision/ExecutionPlanCard";
import {
  CapitalActionsBlock,
  ExecutionStatusBlock,
} from "@/components/dailyLoop/DecisionDepthSections";
import TodayExecutionPanel from "@/components/dailyLoop/TodayExecutionPanel";
import TodayMonitorStrip from "@/components/dailyLoop/TodayMonitorStrip";
import TodayPortfolioSummary from "@/components/dailyLoop/TodayPortfolioSummary";
import ResearchTodayHandoff from "@/components/research/ResearchTodayHandoff";
import VerdictCanvas from "@/components/dailyLoop/VerdictCanvas";
import TodayBelowFold from "@/components/dailyLoop/belowFold/TodayBelowFold";
import TodayDisciplineChip from "@/components/dailyLoop/TodayDisciplineChip";
import DecisionReceipt from "@/components/dailyLoop/DecisionReceipt";
import { buildDailyVerdictPresentation,
  countConsecutiveLossDays,
} from "@/lib/dailyLoop/dailyVerdict";
import OperatingManualStrip from "@/components/dailyLoop/OperatingManualStrip";
import CapitalDamsStrip from "@/components/dailyLoop/CapitalDamsStrip";
import SectorCapStrip from "@/components/portfolio/SectorCapStrip";
import TodayDetailsAccordion from "@/components/dailyLoop/TodayDetailsAccordion";
import TodayWaitInsightCard from "@/components/dailyLoop/TodayWaitInsightCard";
import TodayBookLine from "@/components/dailyLoop/TodayBookLine";
import TodayStarterHoldCard from "@/components/dailyLoop/TodayStarterHoldCard";
import TodaySecondNameCard from "@/components/dailyLoop/TodaySecondNameCard";
import TodayKiteContract from "@/components/dailyLoop/TodayKiteContract";
import TodayPrefillCard from "@/components/dailyLoop/TodayPrefillCard";
import TodayCloseLetter from "@/components/dailyLoop/TodayCloseLetter";
import TodayStillTrue from "@/components/dailyLoop/TodayStillTrue";
import {
  buildSecondNameWatch,
  pickSecondName,
  rankSecondNames,
} from "@/lib/dailyLoop/secondNameToday";
import {
  buildTodayContract,
  persistTodayContract,
  readTodayContract,
  rememberDeskFields,
} from "@/lib/dailyLoop/todayContract";
import { syncTodayContractToServer } from "@/lib/dailyLoop/syncTodayContract";
import {
  buildCampaignLine,
  buildPrefillPreview,
  buildStillTrueLine,
  mergeSessionExtrema,
  normalizeGttStatus,
  thesisNeedsCheckIn,
  watchBandPct,
} from "@/lib/dailyLoop/deskNight";
import {
  appendNameDiary,
  deskHeartbeatLine,
  interruptHealthLine,
  latestDiaryLine,
} from "@/lib/dailyLoop/deskOs";
import { isNseCashSessionOpen } from "@/lib/broker/marketSession";
import TodayDeskStatus from "@/components/dailyLoop/TodayDeskStatus";
import TodayNameDiary from "@/components/dailyLoop/TodayNameDiary";
import { buildDeskFlip, normalizeSymbols, resolveTodayLoop } from "@/lib/dailyLoop/todayLoop";
import { shiftIstDateKey, tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import {
  buildHoldInterruptCopy,
  buildHumanThesis,
  buildLoopReceiptBody,
  buildWatchInterruptCopy,
  cutInrFromInvalidation,
  fireWatchInterrupt,
  holdNotifyKey,
  persistHoldNotifyKey,
  persistWatchNotifyKey,
  pickYesterdayLoopLine,
  readHoldNotifyKeys,
  readWatchNotifyKey,
  readYesterdayLoopLine,
  resolveWatchCarry,
  shouldNotifyHold,
  shouldNotifyWatch,
  watchNotifyKey,
} from "@/lib/dailyLoop/todayMemory";
import TodayWatchlistPanel from "@/components/dailyLoop/TodayWatchlistPanel";
import TodaySyncStatusBanner from "@/components/dailyLoop/TodaySyncStatusBanner";
import InvestmentJourneyPanel from "@/components/journey/InvestmentJourneyPanel";
import {
  buildAlignedWaitInsight,
  resolvePrimaryTradeSymbol,
} from "@/lib/dailyLoop/todayPrimaryFocus";
import { resolveTodayDataFreshness } from "@/lib/dailyLoop/todayDataFreshness";
import {
  FIRST_BUY_HOLD_LABEL,
  applyEmptyBookPresentation,
  applyFirstBuyPresentation,
  applyStarterBookPresentation,
  buildEmptyBookWaitCopy,
  buildFirstBuySize,
  buildFirstBuyWhy,
  buildStarterBookHoldLines,
  buildStarterBookWaitCopy,
  hasCompleteFirstBuyPlan,
  isEmptyBook,
  isFirstBuyCandidate,
  isStarterBook,
  isYoungBook,
  buildBookHoldRule,
  buildYoungBookHoldLines,
  buildYoungBookWaitCopy,
  buildYoungBookCashCopy,
  orderYoungBookHoldings,
  resolveEmptyBookCommitLabel,
} from "@/lib/dailyLoop/firstBuyToday";
import { useMarketSession } from "@/lib/broker/useMarketSession";
import {
  formatExplorePipelineSummaryPlain,
  formatExploreSetupSummary,
} from "@/lib/dailyLoop/exploreSetupPresentation";
import { isSacredCoreSymbol } from "@/services/portfolio/allocationPolicy";
import { buildSectorCapSummary } from "@/services/portfolio/sectorCapPolicy";
import { useMorningBrief } from "@/lib/useMorningBrief";
import TodayProgressStrip from "@/components/dailyLoop/TodayProgressStrip";
import WeeklyReviewStrip from "@/components/dailyLoop/WeeklyReviewStrip";
import LastClosedTrustBlock from "@/components/dailyLoop/LastClosedTrustBlock";
import CapitalModeToggle from "@/components/dailyLoop/CapitalModeToggle";
import { ApexCard } from "@/components/ui/apex";
import type { ConnectionStatus } from "@/lib/broker/zerodha";
import type { StockPick } from "@/types/decision";
import type { UserIntent } from "@/types/intent";
import type { CapitalFundingMode } from "@/lib/dailyLoop/capitalMargin";
import type { BrokerFillSummary } from "@/services/trade/logTradeFill";
import type { TierFeatures } from "@/services/subscription/tier";
import type {
  DisciplineHistoryEntry,
  DisciplineHistorySummary,
} from "@/types/decisionHistory";
import type { PortfolioHoldingRow } from "@/types/portfolioApi";
import type { ResearchVerdict } from "@/types/researchSummary";
import PremiumFeatureGate from "@/components/dailyLoop/PremiumFeatureGate";
import { useExploreTriggers } from "@/lib/useExploreTriggers";
import { useDayPnlPoll } from "@/lib/useDayPnlPoll";
import { useOpenMonitor } from "@/lib/useOpenMonitor";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";

export type HomeDecision = {
  action: string;
  stock?: string;
  amount?: number;
  confidence?: number;
  structureScore?: number;
  allocation?: number;
  suggested_sell_percent?: number;
  allocationPercent?: number;
  allocationReason?: string;
  reason?: string;
  message?: string;
  confidence_factors?: string[];
  confidenceMetrics?: {
    expectedReturn?: number;
    probability?: number;
    edgeScore?: number;
    expectedDrawdown?: number;
  };
  validation?: {
    signal_strength?: number;
    signal_agreement?: boolean;
    market_alignment?: boolean;
    risk_ok?: boolean;
  };
  picks?: StockPick[];
};

export type HomeDecisionScreenProps = {
  decision: HomeDecision;
  entryTiming: EntryTimingState;
  intent: UserIntent;
  topSymbol?: string;
  topAllocationPct?: number;
  availableCash?: number;
  ledgerCash?: number;
  portfolioValue?: number;
  totalCapital?: number;
  collateral?: number;
  capitalMode?: CapitalFundingMode;
  onCapitalModeChange?: (mode: CapitalFundingMode) => void;
  openPnlFromPortfolio?: number | null;
  holdings?: { symbol: string; weight: number; quantity?: number }[];
  portfolioHoldings?: PortfolioHoldingRow[];
  portfolioTotalPnl?: number | null;
  portfolioLoading?: boolean;
  portfolioStale?: boolean;
  connectionStatus?: ConnectionStatus;
  decisionUpdatedAt?: string | null;
  fundsLoading?: boolean;
  fundsSynced?: boolean;
  fundsSyncError?: string | null;
  isRefreshing?: boolean;
  onCapitalRefresh?: () => void;
  onBrokerDataRefresh?: () => void;
  brokerDataRefreshing?: boolean;
  autoSyncRetrying?: boolean;
  autoSyncRetryDetail?: string;
  onDisciplineCommitted?: () => void;
  disciplineHistory?: DisciplineHistoryEntry[];
  disciplineSummary?: DisciplineHistorySummary;
  disciplineDays?: string[];
  premiumFeatures?: TierFeatures;
  premiumActivationEnabled?: boolean;
  onPremiumActivated?: () => void;
  proofHref?: string | null;
  researchHandoff?: {
    symbol: string;
    verdict: ResearchVerdict;
    headline?: string;
    onDismiss: () => void;
  };
  tapeHardWait?: boolean;
  onIntentChange?: (intent: UserIntent) => void;
  className?: string;
};

export default function HomeDecisionScreen({
  decision,
  entryTiming,
  intent,
  topSymbol,
  topAllocationPct,
  availableCash,
  ledgerCash,
  portfolioValue,
  totalCapital,
  collateral,
  capitalMode,
  onCapitalModeChange,
  openPnlFromPortfolio,
  holdings,
  portfolioHoldings = [],
  portfolioTotalPnl,
  portfolioLoading = false,
  portfolioStale = false,
  connectionStatus = "NOT_CONNECTED",
  decisionUpdatedAt,
  fundsLoading = false,
  fundsSynced = false,
  fundsSyncError = null,
  isRefreshing = false,
  onCapitalRefresh,
  onBrokerDataRefresh,
  brokerDataRefreshing = false,
  autoSyncRetrying = false,
  autoSyncRetryDetail,
  onDisciplineCommitted,
  disciplineHistory = [],
  disciplineSummary,
  disciplineDays = [],
  premiumFeatures,
  premiumActivationEnabled = false,
  onPremiumActivated,
  proofHref = null,
  researchHandoff,
  tapeHardWait: tapeHardWaitProp = false,
  onIntentChange,
  className = "",
}: HomeDecisionScreenProps) {
  const features = premiumFeatures ?? {
    marginMode: false,
    decisionDepth: false,
    decisionHistory: false,
  };
  const { renderIntent, contentClassName } = useIntentTransition(intent);
  const experience = getIntentExperience(renderIntent);
  const {
    trustScore,
    trustDelta,
    trustMessage,
    lastOutcome,
    lastOutcomeStock,
    refreshTrust,
    plan,
    planLoading,
  } = useDailyLoop(decision, entryTiming, intent);

  const capitalDecisionInput = useMemo(
    () => ({
      action: decision.action,
      stock: decision.stock ?? topSymbol,
      picks: decision.picks,
      allocationPercent: decision.allocationPercent,
      suggested_sell_percent: decision.suggested_sell_percent,
      topAllocationPct,
      availableCash,
      ledgerCash,
      portfolioValue,
      collateral,
      capitalMode,
      holdings,
      entryTiming,
      confidence: decision.confidence,
    }),
    [
      availableCash,
      capitalMode,
      collateral,
      decision.action,
      decision.allocationPercent,
      decision.confidence,
      decision.picks,
      decision.stock,
      decision.suggested_sell_percent,
      entryTiming,
      holdings,
      ledgerCash,
      portfolioValue,
      topAllocationPct,
      topSymbol,
    ],
  );

  const capitalDecision = useMemo(
    () =>
      buildCapitalDecision({
        intent: renderIntent,
        ...capitalDecisionInput,
      }),
    [capitalDecisionInput, renderIntent],
  );

  const growDecision = useMemo(
    () =>
      buildCapitalDecision({
        intent: "grow",
        ...capitalDecisionInput,
      }),
    [capitalDecisionInput],
  );

  const protectDecision = useMemo(
    () =>
      buildCapitalDecision({
        intent: "protect",
        ...capitalDecisionInput,
      }),
    [capitalDecisionInput],
  );

  const retention = useDisciplineStreak({
    intent: renderIntent,
    action: decision.action,
    stock: decision.stock,
    deploymentPercentage: capitalDecision.deploymentPercentage,
    onCommitted: onDisciplineCommitted,
  });

  const todayHero = useMemo(
    () =>
      resolveTodayHero(capitalDecision, {
        suggestedSellPercent: decision.suggested_sell_percent,
      }),
    [capitalDecision, decision.suggested_sell_percent],
  );
  const [ticketOverride, setTicketOverride] = useState<number | null>(null);

  useEffect(() => {
    setTicketOverride(null);
  }, [todayHero.deployAmount, todayHero.symbol]);
  const { canPlaceMarketOrder } = useMarketSession();

  const [brokerStepCompleted, setBrokerStepCompleted] = useState(() => {
    const symbol = todayHero.symbol?.trim().toUpperCase();
    if (!symbol || typeof window === "undefined") {
      return false;
    }

    return readBrokerStepCompleted(symbol);
  });
  const [brokerStepSkipped, setBrokerStepSkipped] = useState(() => {
    const symbol = todayHero.symbol?.trim().toUpperCase();
    if (!symbol || typeof window === "undefined") {
      return false;
    }

    return readBrokerStepSkipped(symbol);
  });
  const [brokerFillSummary, setBrokerFillSummary] =
    useState<BrokerFillSummary | null>(null);
  const [receiptDismissed, setReceiptDismissed] = useState(false);
  const [processingHoldTrim, setProcessingHoldTrim] = useState(false);
  const [liveTapeHardWait, setLiveTapeHardWait] = useState(tapeHardWaitProp);
  const [watchFilledToday, setWatchFilledToday] = useState(false);
  const [yesterdayLine, setYesterdayLine] = useState<string | null>(null);
  const [humanThesis, setHumanThesis] = useState<string | null>(null);
  const [holdCuts, setHoldCuts] = useState<Record<string, number>>({});
  const [holdTheses, setHoldTheses] = useState<Record<string, string>>({});
  const [cutSaving, setCutSaving] = useState<string | null>(null);
  const [campaignDay, setCampaignDay] = useState(0);
  const [closeLetter, setCloseLetter] = useState<string | null>(null);
  const [gttStatus, setGttStatus] = useState<string | null>(null);
  const [gttBusy, setGttBusy] = useState(false);
  const [bannedSymbols, setBannedSymbols] = useState<string[]>([]);
  const [interruptReady, setInterruptReady] = useState(false);
  const [lastWatchAt, setLastWatchAt] = useState<string | null>(null);
  const [nameDiary, setNameDiary] = useState<
    Array<{ dateKey: string; symbol: string; line: string }>
  >([]);
  const [stillTrue, setStillTrue] = useState<{
    symbol: string;
    thesis: string;
    invalidation: string | null;
    line: string;
  } | null>(null);
  const [stillTrueSaving, setStillTrueSaving] = useState(false);
  const [brokerFillStatusLoading, setBrokerFillStatusLoading] = useState(() => {
    const symbol = todayHero.symbol?.trim().toUpperCase();
    if (!symbol || typeof window === "undefined") {
      return false;
    }

    return !readBrokerStepCompleted(symbol);
  });

  useEffect(() => {
    if (tapeHardWaitProp) {
      setLiveTapeHardWait(true);
    }
  }, [tapeHardWaitProp]);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        const response = await apiFetch("/api/market/tape", {
          cache: "no-store",
        });
        const payload = await parseApiJson<{
          tape?: { hardWait?: boolean };
        }>(response, "Market tape");

        if (cancelled || !response.ok) {
          return;
        }

        setLiveTapeHardWait(payload?.tape?.hardWait === true);
      } catch {
        // Yahoo tape is optional — fail open so a missing index does not lock Today.
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const actualSymbolWeight = useMemo(() => {
    if (!brokerStepCompleted || !todayHero.symbol || !holdings?.length) {
      return undefined;
    }

    const match = holdings.find(
      (holding) =>
        holding.symbol.trim().toUpperCase() ===
        todayHero.symbol?.trim().toUpperCase(),
    );

    return match?.weight;
  }, [brokerStepCompleted, holdings, todayHero.symbol]);

  useEffect(() => {
    if (!todayHero.symbol) {
      setBrokerStepCompleted(false);
      setBrokerStepSkipped(false);
      setBrokerFillSummary(null);
      setBrokerFillStatusLoading(false);
      return;
    }

    const sessionComplete = readBrokerStepCompleted(todayHero.symbol);
    const sessionSkipped = readBrokerStepSkipped(todayHero.symbol);
    if (sessionComplete || sessionSkipped) {
      setBrokerStepCompleted(sessionComplete);
      setBrokerStepSkipped(sessionSkipped);
      setBrokerFillStatusLoading(false);
    } else {
      setBrokerFillStatusLoading(true);
    }

    let cancelled = false;

    void (async () => {
      try {
        const response = await apiFetch(
          `/api/trade/status?stock=${encodeURIComponent(todayHero.symbol ?? "")}`,
          { cache: "no-store" },
        );
        const payload = await parseApiJson<{
          filledToday?: boolean;
          orderId?: string;
          quantity?: number;
          side?: "buy" | "sell";
          price?: number;
        }>(response, "Trade status");

        if (cancelled) {
          return;
        }

        if (!response.ok) {
          return;
        }

        if (!payload?.filledToday) {
          if (!sessionComplete && !sessionSkipped) {
            setBrokerStepCompleted(false);
            setBrokerFillSummary(null);
          }
          return;
        }

        if (
          payload.orderId &&
          typeof payload.quantity === "number" &&
          (payload.side === "buy" || payload.side === "sell")
        ) {
          setBrokerFillSummary({
            orderId: payload.orderId,
            quantity: payload.quantity,
            side: payload.side,
            price: payload.price,
          });
        }

        markBrokerStepCompleted(todayHero.symbol ?? "");
        setBrokerStepCompleted(true);

        if (!sessionComplete) {
          onCapitalRefresh?.();
        }
      } catch {
        // Session cache remains the fallback when the status API is unavailable.
      } finally {
        if (!cancelled) {
          setBrokerFillStatusLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [onCapitalRefresh, todayHero.symbol]);

  const holdingAllocationPct =
    todayHero.currentWeight ??
    topAllocationPct ??
    capitalDecision.actions.find((action) => action.symbol === todayHero.symbol)
      ?.portfolioWeight;

  const seedYoungBook = isYoungBook({
    openHoldingsCount: portfolioHoldings.filter((row) => row.quantity > 0).length,
    portfolioValue: portfolioValue ?? null,
  });
  const isExplore = renderIntent === "explore" && !seedYoungBook;
  const isCapitalDeployment =
    seedYoungBook || renderIntent === "grow" || renderIntent === "protect";
  const morningBriefEnabled = isCapitalDeployment && connectionStatus === "CONNECTED";
  const {
    brief: morningBrief,
    loading: morningBriefLoading,
    error: morningBriefError,
    refresh: refreshMorningBrief,
  } = useMorningBrief({
    enabled: morningBriefEnabled,
    intent: seedYoungBook ? "grow" : renderIntent,
    refreshKey: decisionUpdatedAt,
  });
  const monitorEnabled =
    connectionStatus === "CONNECTED" && isCapitalDeployment;
  const dayPnlPollEnabled = connectionStatus === "CONNECTED";
  const {
    positions: monitorPositions,
    loading: monitorLoading,
    refresh: refreshMonitor,
  } = useOpenMonitor({ enabled: monitorEnabled });
  const {
    positionsPnl: livePositionsPnl,
    positionsBreakdown: livePositionsBreakdown,
    portfolioDayPnl: liveDayPnl,
    positionTicks,
    liveHoldings,
    liveHoldingsTotalValue,
    liveHoldingsTotalPnl,
    lastSyncedAt: liveLastSyncedAt,
    pollError: livePollError,
    isPolling: livePnlPolling,
    refresh: refreshLiveDayPnl,
  } = useDayPnlPoll({
    enabled: dayPnlPollEnabled,
  });
  const displayPortfolioHoldings =
    liveHoldings.length > 0 ? liveHoldings : portfolioHoldings;
  const openPortfolioHoldings = useMemo(
    () => displayPortfolioHoldings.filter((row) => row.quantity > 0),
    [displayPortfolioHoldings],
  );
  const displayPortfolioValue =
    liveHoldingsTotalValue ?? portfolioValue ?? null;
  const youngBook = isYoungBook({
    openHoldingsCount: openPortfolioHoldings.length,
    portfolioValue: displayPortfolioValue,
  });
  const liveBookFresh =
    liveHoldings.length > 0 ||
    liveLastSyncedAt !== null ||
    liveHoldingsTotalValue !== null;
  const snapshotStale = portfolioStale && !liveBookFresh;
  const dataFreshness = useMemo(
    () =>
      resolveTodayDataFreshness({
        connectionStatus,
        portfolioStale,
        pollError: livePollError,
        fundsSyncError,
        liveBookFresh,
        emptyBookConnected:
          connectionStatus === "CONNECTED" &&
          isEmptyBook({
            openHoldingsCount: openPortfolioHoldings.length,
            portfolioValue: liveHoldingsTotalValue ?? portfolioValue ?? null,
          }),
      }),
    [
      connectionStatus,
      fundsSyncError,
      liveBookFresh,
      liveHoldingsTotalValue,
      livePollError,
      openPortfolioHoldings.length,
      portfolioStale,
      portfolioValue,
    ],
  );
  const collapsePlanByDefault = disciplineDays.length >= 7;
  const heroHoldingQty = useMemo(() => {
    if (!todayHero.symbol || displayPortfolioHoldings.length === 0) {
      return undefined;
    }

    const symbol = todayHero.symbol.trim().toUpperCase();
    return displayPortfolioHoldings.find(
      (holding) => holding.tradingsymbol.trim().toUpperCase() === symbol,
    )?.quantity;
  }, [displayPortfolioHoldings, todayHero.symbol]);
  const todayHeroResolved = useMemo(
    () => enrichTodayHeroWithSellTrim(todayHero, heroHoldingQty),
    [heroHoldingQty, todayHero],
  );
  const displayHero = useMemo(
    () =>
      resolveTodayHeroDisplay(todayHeroResolved, brokerStepCompleted, {
        actualPortfolioWeight: actualSymbolWeight,
        brokerFillSummary,
        brokerStepSkipped: youngBook ? false : brokerStepSkipped,
      }),
    [
      actualSymbolWeight,
      brokerFillSummary,
      brokerStepCompleted,
      brokerStepSkipped,
      todayHeroResolved,
      youngBook,
    ],
  );

  const brokerStepResolved = brokerStepCompleted || brokerStepSkipped;
  const emptyBook = isEmptyBook({
    openHoldingsCount: openPortfolioHoldings.length,
    portfolioValue: displayPortfolioValue,
  });
  const starterBook = isStarterBook({
    openHoldingsCount: openPortfolioHoldings.length,
    portfolioValue: displayPortfolioValue,
  });
  const youngBookHoldings = useMemo(
    () => orderYoungBookHoldings(openPortfolioHoldings),
    [openPortfolioHoldings],
  );
  const starterHoldingSymbol =
    youngBookHoldings[0]?.tradingsymbol ?? todayHero.symbol ?? "";
  const firstBuyTicket = ticketOverride ?? todayHero.deployAmount ?? 0;
  const firstBuyCandidate = isFirstBuyCandidate({
    emptyBook,
    executionKind: todayHero.executionKind,
    symbol: todayHero.symbol,
    deployAmount: todayHero.deployAmount,
  });
  const firstBuyPick = useMemo(() => {
    const symbol = todayHero.symbol?.trim().toUpperCase();
    if (!symbol) {
      return null;
    }

    return (
      decision.picks?.find(
        (pick) => pick.stock.trim().toUpperCase() === symbol,
      ) ?? null
    );
  }, [decision.picks, todayHero.symbol]);
  const firstBuyPlanLines = {
    entryInr: firstBuyPick?.activationLevel ?? firstBuyPick?.price ?? null,
    stopInr: plan?.stopLoss ?? null,
    holdLabel: FIRST_BUY_HOLD_LABEL,
  };
  const firstBuyPlanReady =
    firstBuyCandidate &&
    !planLoading &&
    hasCompleteFirstBuyPlan(firstBuyPlanLines);
  const firstBuySize = buildFirstBuySize(availableCash ?? 0, firstBuyTicket);
  const firstBuyWhy =
    firstBuyCandidate && todayHero.symbol
      ? buildFirstBuyWhy({
          symbol: todayHero.symbol,
          size: firstBuySize,
          holdLabel: FIRST_BUY_HOLD_LABEL,
        })
      : "";
  const displayPortfolioTotalPnl =
    liveHoldingsTotalPnl ?? portfolioTotalPnl ?? null;
  const breakdownOpenPnl =
    livePositionsBreakdown.length > 0
      ? Math.round(
          livePositionsBreakdown.reduce((sum, row) => sum + row.pnl, 0) * 10,
        ) / 10
      : null;
  const resolvedOpenPnl =
    livePositionsPnl ??
    breakdownOpenPnl ??
    openPnlFromPortfolio ??
    null;
  const breakdownLoading =
    connectionStatus === "CONNECTED" &&
    !livePollError &&
    livePositionsBreakdown.length === 0 &&
    resolvedOpenPnl === null &&
    !liveLastSyncedAt;
  const monitorStripOpenPnl = resolvedOpenPnl;
  const monitorLiveTicksById = useMemo(() => {
    const map: Record<string, (typeof positionTicks)[number]> = {};
    for (const tick of positionTicks) {
      map[tick.id] = tick;
    }
    return map;
  }, [positionTicks]);

  const handleExecuted = useCallback(
    (fill?: BrokerFillSummary) => {
      if (todayHero.symbol) {
        markBrokerStepCompleted(todayHero.symbol);
        setBrokerStepCompleted(true);
      }

      if (fill?.orderId) {
        setBrokerFillSummary(fill);
        setReceiptDismissed(false);

        void (async () => {
          try {
            await apiFetch("/api/receipts", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                symbol: todayHero.symbol,
                executionKind: todayHero.executionKind,
                verdictWord: morningBrief?.decision.verdict_display,
                headline: morningBrief?.decision.headline ?? displayHero.headline,
                subline: morningBrief?.decision.subline ?? displayHero.subline,
                trustScore: morningBrief?.trust.trust_score ?? trustScore,
                trustDelta: morningBrief?.trust.trust_delta ?? trustDelta,
                orderId: fill.orderId,
                fillSide: fill.side,
                fillQuantity: fill.quantity,
                fillPrice: fill.price,
                fillAmount:
                  fill.price !== undefined
                    ? fill.price * fill.quantity
                    : undefined,
                briefSnapshot: morningBrief ?? undefined,
              }),
            });
          } catch {
            // Receipt persistence must not block execution UX.
          }
        })();
      }

      onCapitalRefresh?.();
      void refreshMonitor();
      void refreshLiveDayPnl();
      void refreshTrust();
    },
    [displayHero.headline, displayHero.subline, morningBrief, onCapitalRefresh, refreshLiveDayPnl, refreshMonitor, refreshMorningBrief, refreshTrust, renderIntent, todayHero.executionKind, todayHero.symbol, trustDelta, trustScore],
  );

  const handleHoldTrim = useCallback(async () => {
    if (!todayHero.symbol || processingHoldTrim) {
      return;
    }

    setProcessingHoldTrim(true);

    try {
      markBrokerStepSkipped(todayHero.symbol);
      setBrokerStepSkipped(true);
      setBrokerStepCompleted(false);

      await apiFetch("/api/discipline/streak", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          intent: renderIntent,
          action: "WAIT",
          stock: todayHero.symbol,
        }),
      });

      onDisciplineCommitted?.();
    } catch {
      // Holding the position is still recorded locally for today's broker step.
    } finally {
      setProcessingHoldTrim(false);
    }
  }, [
    onDisciplineCommitted,
    processingHoldTrim,
    renderIntent,
    todayHero.symbol,
  ]);

  useEffect(() => {
    if (!brokerStepCompleted) {
      return;
    }

    onDisciplineCommitted?.();
  }, [brokerStepCompleted, onDisciplineCommitted]);

  const watchCarry = useMemo(
    () => {
      const local = resolveWatchCarry({
        today: readTodayContract(),
        yesterday: readTodayContract(shiftIstDateKey(tradingDateKey(), -1)),
      });
      return {
        preferredSymbol: local.preferredSymbol,
        bannedSymbols: [...new Set([...local.bannedSymbols, ...bannedSymbols])],
      };
    },
    [bannedSymbols, watchFilledToday, youngBookHoldings],
  );
  const liveHeldSymbols = useMemo(
    () => youngBookHoldings.map((holding) => holding.tradingsymbol),
    [youngBookHoldings],
  );
  const placedWatchSymbol = useMemo(() => {
    const watch = watchCarry.preferredSymbol;
    if (!watch) {
      return null;
    }

    if (watchFilledToday) {
      return watch;
    }

    const live = normalizeSymbols(liveHeldSymbols);
    const morning = normalizeSymbols(readTodayContract()?.heldSymbols);
    if (live.includes(watch) && morning.length > 0 && !morning.includes(watch)) {
      return watch;
    }

    return null;
  }, [liveHeldSymbols, watchCarry.preferredSymbol, watchFilledToday]);
  const deskHeldSymbols = useMemo(
    () => [
      ...liveHeldSymbols,
      ...(placedWatchSymbol ? [placedWatchSymbol] : []),
    ],
    [liveHeldSymbols, placedWatchSymbol],
  );
  const deskHeldCount = normalizeSymbols(deskHeldSymbols).length;

  const nextNamePick = useMemo(() => {
    if (isExplore) {
      return null;
    }

    if (starterBook) {
      return pickSecondName({
        heldSymbol: starterHoldingSymbol,
        heldSymbols: deskHeldSymbols,
        bannedSymbols: watchCarry.bannedSymbols,
        picks: decision.picks,
      });
    }

    if (youngBook) {
      return pickSecondName({
        heldSymbols: deskHeldSymbols,
        bannedSymbols: watchCarry.bannedSymbols,
        picks: decision.picks,
      });
    }

    return null;
  }, [
    decision.picks,
    deskHeldSymbols,
    isExplore,
    starterBook,
    starterHoldingSymbol,
    watchCarry.bannedSymbols,
    youngBook,
  ]);

  const explorePicks = useMemo(() => {
    if (!isExplore && (starterBook || youngBook)) {
      const ranked = rankSecondNames({
        heldSymbol: starterBook ? starterHoldingSymbol : undefined,
        heldSymbols: deskHeldSymbols,
        bannedSymbols: watchCarry.bannedSymbols,
        picks: decision.picks,
      });
      const preferred = watchCarry.preferredSymbol
        ? decision.picks?.find(
            (pick) =>
              pick.stock.trim().toUpperCase() === watchCarry.preferredSymbol,
          )
        : null;
      const merged = preferred ? [preferred, ...ranked] : ranked;
      const seen = new Set<string>();
      const unique: typeof ranked = [];
      for (const pick of merged) {
        const symbol = pick.stock.trim().toUpperCase();
        if (seen.has(symbol)) {
          continue;
        }
        seen.add(symbol);
        unique.push(pick);
        if (unique.length >= 3) {
          break;
        }
      }
      return unique;
    }

    if (!isExplore || !decision.picks?.length) {
      return [];
    }

    const symbols = new Set(
      capitalDecision.exploreSetups.map((setup) => setup.symbol),
    );

    return decision.picks.filter((pick) => symbols.has(pick.stock));
  }, [
    capitalDecision.exploreSetups,
    decision.picks,
    isExplore,
    deskHeldSymbols,
    starterBook,
    starterHoldingSymbol,
    watchCarry.bannedSymbols,
    watchCarry.preferredSymbol,
    youngBook,
  ]);

  const {
    triggerBySymbol: exploreTriggerBySymbol,
  } = useExploreTriggers({
    enabled: explorePicks.length > 0 && (isExplore || starterBook || youngBook),
    picks: explorePicks,
    refreshKey: decisionUpdatedAt,
  });
  const nextNameWatch =
    !isExplore && (starterBook || youngBook)
      ? buildSecondNameWatch({
          heldSymbol: starterBook ? starterHoldingSymbol : undefined,
          heldSymbols: deskHeldSymbols,
          bannedSymbols: watchCarry.bannedSymbols,
          picks: decision.picks,
          cashInr: availableCash ?? 0,
          livePriceBySymbol: (() => {
            const prices = new Map<string, number>();
            for (const [symbol, trigger] of exploreTriggerBySymbol.entries()) {
              const live = trigger.livePrice;
              if (live !== null && live !== undefined && Number.isFinite(live) && live > 0) {
                prices.set(symbol.trim().toUpperCase(), live);
              }
            }
            return prices;
          })(),
          preferredSymbol: watchCarry.preferredSymbol,
          bandPct: watchBandPct(campaignDay || 1),
          eyebrow: starterBook
            ? "Next name"
            : deskHeldCount >= 3
              ? "Fourth name"
              : "Third name",
        })
      : null;
  const todayContract = useMemo(() => {
    const previous = readTodayContract();
    const morningBook = previous?.heldSymbols;
    const liveBook =
      youngBookHoldings.length > 0
        ? youngBookHoldings.map((holding) => holding.tradingsymbol)
        : [starterHoldingSymbol];

    const built = buildTodayContract({
      heldSymbols: morningBook && morningBook.length > 0 ? morningBook : liveBook,
      watch: nextNameWatch
        ? {
            symbol: nextNameWatch.symbol,
            through: nextNameWatch.through,
            dead: nextNameWatch.dead,
            triggerInr: nextNameWatch.triggerInr,
            killInr: nextNameWatch.killInr,
            ticketInr: nextNameWatch.size.ticketInr,
            gapLabel: nextNameWatch.gapLabel,
          }
        : null,
      tapeHardWait: liveTapeHardWait,
    });

    let highs = previous?.sessionHighBySymbol;
    let lows = previous?.sessionLowBySymbol;
    if (nextNameWatch?.symbol && nextNameWatch.livePriceInr) {
      highs = mergeSessionExtrema(
        highs,
        nextNameWatch.symbol,
        nextNameWatch.livePriceInr,
        "high",
      );
      lows = mergeSessionExtrema(
        lows,
        nextNameWatch.symbol,
        nextNameWatch.livePriceInr,
        "low",
      );
    }
    for (const holding of youngBookHoldings) {
      const symbol = holding.tradingsymbol?.trim().toUpperCase();
      if (!symbol || !holding.last_price) {
        continue;
      }
      highs = mergeSessionExtrema(highs, symbol, holding.last_price, "high");
      lows = mergeSessionExtrema(lows, symbol, holding.last_price, "low");
    }

    return {
      ...built,
      sessionHighBySymbol: highs,
      sessionLowBySymbol: lows,
      holdCutsBySymbol: Object.keys(holdCuts).length > 0 ? holdCuts : previous?.holdCutsBySymbol,
      lastWatchAt: lastWatchAt ?? previous?.lastWatchAt,
      nameDiary: nameDiary.length > 0 ? nameDiary : previous?.nameDiary,
    };
  }, [
    holdCuts,
    lastWatchAt,
    liveTapeHardWait,
    nameDiary,
    nextNameWatch,
    starterHoldingSymbol,
    youngBookHoldings,
  ]);

  const todayLoop = resolveTodayLoop({
    contract: todayContract,
    liveHeldSymbols: youngBookHoldings.map((holding) => holding.tradingsymbol),
    watchFilledToday,
    committedWait: retention.committedToday,
  });

  useEffect(() => {
    if (!todayContract.kiteLine || !todayContract.rule || !todayContract.dateKey) {
      return;
    }

    const merged = rememberDeskFields(
      {
        ...todayContract,
        outcome: todayLoop.state === "open" ? todayContract.outcome : todayLoop.state,
        outcomeLine:
          todayLoop.state === "open" ? todayContract.outcomeLine : todayLoop.line,
        campaignDay: campaignDay || todayContract.campaignDay,
        cashMandate: nextNameWatch
          ? `Mandate: sit until ${nextNameWatch.symbol} confirms. Not a leftover.`
          : "Idle on purpose. No third name until a line exists.",
      },
      readTodayContract(),
    );
    syncTodayContractToServer(merged);
  }, [campaignDay, nextNameWatch, todayContract, todayLoop]);

  useEffect(() => {
    const symbol = nextNameWatch?.symbol;
    if (!symbol || !(youngBook || starterBook)) {
      setWatchFilledToday(false);
      return;
    }

    let cancelled = false;

    void (async () => {
      try {
        const response = await apiFetch(
          `/api/trade/status?stock=${encodeURIComponent(symbol)}`,
          { cache: "no-store" },
        );
        const payload = await parseApiJson<{ filledToday?: boolean }>(
          response,
          "Watch fill",
        );
        if (!cancelled && response.ok && payload?.filledToday) {
          setWatchFilledToday(true);
        }
      } catch {
        // Live holdings remain the fallback when fill status is unavailable.
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [nextNameWatch?.symbol, starterBook, youngBook]);

  useEffect(() => {
    setYesterdayLine(readYesterdayLoopLine());

    void (async () => {
      try {
        const response = await apiFetch("/api/receipts?days=7", { cache: "no-store" });
        const payload = await parseApiJson<{
          receipts?: Array<{
            receipt_date?: string;
            headline?: string | null;
            order_id?: string | null;
          }>;
        }>(response, "Receipts");
        if (response.ok && payload?.receipts) {
          setYesterdayLine(pickYesterdayLoopLine(payload.receipts));
        }
      } catch {
        // Local yesterday line remains the fallback.
      }
    })();
  }, []);

  useEffect(() => {
    void (async () => {
      try {
        const response = await apiFetch("/api/today/contract", { cache: "no-store" });
        const payload = await parseApiJson<{
          contract?: {
            kiteLine?: string;
            rule?: string;
            dateKey?: string;
            campaignDay?: number;
            closeLetter?: string;
            gttStatus?: string;
          } | null;
          campaignDay?: number;
          bannedSymbols?: string[];
          interrupt?: { ready?: boolean };
          lastWatchAt?: string | null;
        }>(response, "Contract");
        if (!response.ok) {
          return;
        }

        if (payload?.contract?.kiteLine && payload.contract.rule && payload.contract.dateKey) {
          persistTodayContract(payload.contract as Parameters<typeof persistTodayContract>[0]);
        }
        if (payload?.campaignDay) {
          setCampaignDay(payload.campaignDay);
        } else if (payload?.contract?.campaignDay) {
          setCampaignDay(payload.contract.campaignDay);
        }
        if (payload?.bannedSymbols) {
          setBannedSymbols(payload.bannedSymbols);
        }
        if (payload?.interrupt) {
          setInterruptReady(payload.interrupt.ready === true);
        }
        if (payload?.lastWatchAt) {
          setLastWatchAt(payload.lastWatchAt);
        }
        if (payload?.contract && "nameDiary" in payload.contract) {
          const diary = (
            payload.contract as { nameDiary?: Array<{ dateKey: string; symbol: string; line: string }> }
          ).nameDiary;
          if (diary) {
            setNameDiary(diary);
          }
        }
        if (payload?.contract?.closeLetter) {
          setCloseLetter(payload.contract.closeLetter);
        }
        if (payload?.contract?.gttStatus) {
          setGttStatus(normalizeGttStatus(payload.contract.gttStatus));
        }
      } catch {
        // Same-browser localStorage remains.
      }

      try {
        const yday = shiftIstDateKey(tradingDateKey(), -1);
        const ydayResponse = await apiFetch(
          `/api/today/contract?date=${encodeURIComponent(yday)}`,
          { cache: "no-store" },
        );
        const ydayPayload = await parseApiJson<{
          contract?: Parameters<typeof persistTodayContract>[0] | null;
        }>(ydayResponse, "Yesterday contract");
        if (ydayResponse.ok && ydayPayload?.contract?.kiteLine) {
          persistTodayContract(ydayPayload.contract);
        }
      } catch {
        // Watch carry still reads the local yesterday contract.
      }
    })();
  }, []);

  useEffect(() => {
    if (!(youngBook || starterBook)) {
      return;
    }

    void (async () => {
      try {
        const response = await apiFetch("/api/trade/gtt", { cache: "no-store" });
        const payload = await parseApiJson<{
          watchStatus?: string | null;
        }>(response, "GTT");
        if (response.ok && payload?.watchStatus) {
          setGttStatus(normalizeGttStatus(payload.watchStatus));
        }
      } catch {
        // GTT status is optional until Kite answers.
      }
    })();
  }, [starterBook, youngBook]);

  useEffect(() => {
    const body = buildLoopReceiptBody({ loop: todayLoop, contract: todayContract });
    if (!body || !(youngBook || starterBook)) {
      return;
    }

    const stamp = `apex_loop_receipt:${todayContract.dateKey}:${todayLoop.state}`;
    if (typeof window !== "undefined" && window.localStorage.getItem(stamp)) {
      return;
    }

    void (async () => {
      try {
        const response = await apiFetch("/api/receipts", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        if (response.ok && typeof window !== "undefined") {
          window.localStorage.setItem(stamp, "1");
        }
      } catch {
        // Review still reads yesterday from the local contract.
      }
    })();
  }, [starterBook, todayContract, todayLoop, youngBook]);

  useEffect(() => {
    if (!nextNameWatch || liveTapeHardWait || !(youngBook || starterBook)) {
      return;
    }

    const nextKey = watchNotifyKey(nextNameWatch);
    if (!shouldNotifyWatch(readWatchNotifyKey(), nextKey)) {
      return;
    }

    persistWatchNotifyKey(nextKey);
    void fireWatchInterrupt(buildWatchInterruptCopy(nextNameWatch));
  }, [liveTapeHardWait, nextNameWatch, starterBook, youngBook]);

  useEffect(() => {
    if (!(youngBook || starterBook)) {
      return;
    }

    const seen = readHoldNotifyKeys();
    for (const holding of youngBookHoldings) {
      const symbol = holding.tradingsymbol?.trim().toUpperCase();
      if (!symbol) {
        continue;
      }

      const hold = buildBookHoldRule({
        averagePriceInr: holding.average_price,
        lastPriceInr: holding.last_price,
        cutInr: holdCuts[symbol],
      });
      if (!hold.ruleBroken) {
        continue;
      }

      const nextKey = holdNotifyKey(symbol);
      if (!shouldNotifyHold(seen, nextKey)) {
        continue;
      }

      persistHoldNotifyKey(nextKey);
      seen.push(nextKey);
      void fireWatchInterrupt(
        buildHoldInterruptCopy({ symbol, cutLabel: hold.cutLabel }),
      );
    }
  }, [holdCuts, starterBook, youngBook, youngBookHoldings]);

  useEffect(() => {
    const symbol = nextNameWatch?.symbol;
    if (!symbol || !(youngBook || starterBook)) {
      setHumanThesis(null);
      return;
    }

    let cancelled = false;

    void (async () => {
      try {
        const response = await apiFetch(
          `/api/research/summary?symbol=${encodeURIComponent(symbol)}`,
          { cache: "no-store" },
        );
        const payload = await parseApiJson<{
          summary?: {
            summary?: string | null;
            questions?: Array<{ id?: string; answer?: string | null }>;
          };
        }>(response, "Research");
        if (cancelled || !response.ok) {
          return;
        }

        setHumanThesis(
          buildHumanThesis({
            symbol,
            triggerInr: nextNameWatch.triggerInr,
            fallback: nextNameWatch.whyLine ?? "",
            research: payload?.summary ?? null,
          }),
        );
      } catch {
        if (!cancelled) {
          setHumanThesis(nextNameWatch.whyLine);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [nextNameWatch, starterBook, youngBook]);

  useEffect(() => {
    if (!(youngBook || starterBook)) {
      return;
    }

    void (async () => {
      try {
        const response = await apiFetch("/api/thesis", { cache: "no-store" });
        const payload = await parseApiJson<{
          theses?: Array<{
            symbol?: string;
            thesis?: string;
            invalidation?: string | null;
            updated_at?: string;
          }>;
        }>(response, "Thesis");
        if (!response.ok || !payload?.theses) {
          return;
        }

        const next: Record<string, number> = {};
        const lines: Record<string, string> = {};
        let checkIn: {
          symbol: string;
          thesis: string;
          invalidation: string | null;
          line: string;
        } | null = null;
        for (const row of payload.theses) {
          const symbol = row.symbol?.trim().toUpperCase();
          const cut = cutInrFromInvalidation(row.invalidation);
          if (symbol && cut) {
            next[symbol] = cut;
          }
          if (symbol && row.thesis) {
            lines[symbol] = row.thesis;
          }
          if (
            !checkIn &&
            symbol &&
            row.thesis &&
            thesisNeedsCheckIn(row.updated_at)
          ) {
            checkIn = {
              symbol,
              thesis: row.thesis,
              invalidation: row.invalidation ?? null,
              line: buildStillTrueLine(symbol, row.thesis),
            };
          }
        }
        setHoldCuts(next);
        setHoldTheses(lines);
        setStillTrue(checkIn);
        setNameDiary((current) => {
          let diary = current;
          for (const row of payload.theses) {
            const symbol = row.symbol?.trim().toUpperCase();
            const line = row.invalidation?.trim() || row.thesis?.trim();
            if (!symbol || !line) {
              continue;
            }
            diary = appendNameDiary(diary, {
              dateKey: (row.updated_at ?? "").slice(0, 10) || tradingDateKey(),
              symbol,
              line,
            });
          }
          return diary;
        });
      } catch {
        // Default 3% hold line remains.
      }
    })();
  }, [starterBook, youngBook]);

  const isExploreEmpty =
    isExplore &&
    capitalDecision.exploreSetups.length === 0 &&
    capitalDecision.actions.length === 0;
  let sectionDelay = 80;

  const nextDelay = () => {
    const value = sectionDelay;
    sectionDelay += 80;
    return value;
  };

  const brokerStepLine = isCapitalDeployment
    ? getBrokerStepLine(
        retention.committedToday,
        todayHero.executionKind,
        brokerStepCompleted,
      )
    : null;
  const consecutiveLossDays = useMemo(
    () => countConsecutiveLossDays(disciplineHistory, disciplineDays),
    [disciplineDays, disciplineHistory],
  );
  const targetIsSacredCore = useMemo(() => {
    if (!todayHero.symbol || displayPortfolioHoldings.length === 0) {
      return false;
    }

    return isSacredCoreSymbol({
      symbol: todayHero.symbol,
      holdings: displayPortfolioHoldings,
      topSymbol,
    });
  }, [displayPortfolioHoldings, todayHero.symbol, topSymbol]);
  const sectorCapSummary = useMemo(
    () =>
      buildSectorCapSummary({
        holdings: displayPortfolioHoldings,
        totalValue: displayPortfolioValue,
      }),
    [displayPortfolioHoldings, displayPortfolioValue],
  );

  const verdictPresentation = useMemo(() => {
    const base = buildDailyVerdictPresentation({
      verdictInput: {
        executionKind: displayHero.executionKind,
        entryConfirmed: entryTiming.enter,
        consecutiveLossDays,
        portfolioDayPnl: liveDayPnl,
        portfolioValue: displayPortfolioValue,
        riskBlocked: decision.validation?.risk_ok === false,
        brokerStepCompleted,
        brokerStepSkipped: youngBook ? false : brokerStepSkipped,
        targetIsSacredCore,
        targetSymbol: todayHero.symbol,
        tapeHardWait: liveTapeHardWait,
      },
      heroHeadline: displayHero.headline,
      heroSubline: displayHero.subline,
    });

    if (isExplore && !isExploreEmpty) {
      const top = capitalDecision.exploreSetups[0];
      const closeCount = capitalDecision.exploreSetups.filter(
        (setup) => setup.stage === "Close to readiness",
      ).length;

      return applyEmptyBookPresentation({
        presentation: {
          ...base,
          verdict: "wait" as const,
          displayWord: "Wait",
          headline:
            closeCount > 0
              ? `${closeCount} almost ready — still no trade today`
              : "Watch today — cash stays in your account",
          subline: top
            ? `Top watch: ${top.symbol}. ${formatExploreSetupSummary(top)}`
            : capitalDecision.heroSubline,
          ctaLabel: "You're done for today",
          doneForToday: true,
          tradingLocked: true,
        },
        emptyBook,
        lens: renderIntent,
      });
    }

    const firstBuyApplied = applyFirstBuyPresentation({
      presentation: base,
      firstBuy: firstBuyCandidate,
      planReady: firstBuyPlanReady,
      symbol: todayHero.symbol ?? "",
      ticketInr: firstBuyTicket,
      why: firstBuyWhy,
      brokerDone: brokerStepCompleted || brokerStepSkipped,
    });

    const namedWait =
      emptyBook &&
      renderIntent === "grow" &&
      firstBuyApplied.verdict === "wait"
        ? {
            ...firstBuyApplied,
            ...buildEmptyBookWaitCopy({
              symbol: todayHero.symbol ?? firstBuyPick?.stock,
              livePriceInr: firstBuyPick?.price ?? null,
              triggerInr: firstBuyPick?.activationLevel ?? null,
            }),
          }
        : starterBook &&
            renderIntent === "grow" &&
            firstBuyApplied.verdict === "wait"
          ? (() => {
              const starterWait = buildStarterBookWaitCopy({
                symbol: starterHoldingSymbol || todayHero.symbol,
              });
              const flip = buildDeskFlip({
                through: nextNameWatch?.through,
                dead: nextNameWatch?.dead,
                tapeHardWait: liveTapeHardWait,
                watchSymbol: nextNameWatch?.symbol,
                ticketInr: nextNameWatch?.size.ticketInr,
                triggerInr: nextNameWatch?.triggerInr,
                waitHeadline: starterWait.headline,
                waitSubline: starterWait.subline,
              });

              return {
                ...firstBuyApplied,
                ...flip,
              };
            })()
          : youngBook &&
              renderIntent === "grow" &&
              firstBuyApplied.verdict !== "pause"
            ? (() => {
                const youngWait = buildYoungBookWaitCopy({
                  symbols: deskHeldSymbols,
                  nextSymbol: nextNamePick?.stock,
                  tapeHardWait: liveTapeHardWait,
                });
                const flip = buildDeskFlip({
                  through: nextNameWatch?.through,
                  dead: nextNameWatch?.dead,
                  tapeHardWait: liveTapeHardWait,
                  watchSymbol: nextNameWatch?.symbol,
                  ticketInr: nextNameWatch?.size.ticketInr,
                  triggerInr: nextNameWatch?.triggerInr,
                  waitHeadline: youngWait.headline,
                  waitSubline: youngWait.subline,
                });

                return {
                  ...firstBuyApplied,
                  verdict: "wait" as const,
                  displayWord: flip.displayWord,
                  headline: flip.headline,
                  subline: flip.subline,
                };
              })()
            : firstBuyApplied;

    return applyStarterBookPresentation({
      presentation: applyEmptyBookPresentation({
        presentation: namedWait,
        emptyBook,
        lens: renderIntent,
      }),
      starterBook: starterBook || youngBook,
    });
  }, [
    brokerStepCompleted,
    brokerStepSkipped,
    capitalDecision.exploreSetups,
    capitalDecision.heroSubline,
    consecutiveLossDays,
    decision.validation?.risk_ok,
    displayHero.executionKind,
    displayHero.headline,
    displayHero.subline,
    displayPortfolioValue,
    emptyBook,
    starterBook,
    youngBook,
    youngBookHoldings,
    starterHoldingSymbol,
    entryTiming.enter,
    firstBuyCandidate,
    firstBuyPick,
    firstBuyPlanReady,
    firstBuyTicket,
    firstBuyWhy,
    isExplore,
    isExploreEmpty,
    liveDayPnl,
    renderIntent,
    liveTapeHardWait,
    nextNamePick,
    nextNameWatch,
    deskHeldSymbols,
    targetIsSacredCore,
    todayHero.symbol,
  ]);
  const hideTodayDump =
    emptyBook ||
    youngBook ||
    verdictPresentation.verdict === "pause";
  const showExecutionPanel =
    !youngBook &&
    (!verdictPresentation.tradingLocked ||
      brokerStepResolved ||
      firstBuyCandidate);
  const starterHoldLines =
    starterBook && !isExplore
      ? buildStarterBookHoldLines({
          symbol:
            starterHoldingSymbol ||
            youngBookHoldings[0]?.tradingsymbol ||
            todayHero.symbol,
          quantity: youngBookHoldings[0]?.quantity,
          averagePriceInr: youngBookHoldings[0]?.average_price,
          lastPriceInr: youngBookHoldings[0]?.last_price,
          dayPnlInr: liveDayPnl ?? youngBookHoldings[0]?.pnl,
          stopInr: firstBuyPlanLines.stopInr,
          cashInr: availableCash ?? null,
          cutInr:
            holdCuts[
              (
                starterHoldingSymbol ||
                youngBookHoldings[0]?.tradingsymbol ||
                todayHero.symbol ||
                ""
              )
                .trim()
                .toUpperCase()
            ] ?? null,
        })
      : null;
  const youngHoldLines =
    youngBook && !starterBook && !isExplore
      ? buildYoungBookHoldLines({ holdings: youngBookHoldings, cuts: holdCuts })
      : [];
  const youngCashCopy =
    youngBook && !starterBook && !isExplore
      ? buildYoungBookCashCopy({
          cashInr: availableCash,
          nextSymbol: nextNameWatch?.symbol,
          heldCount: deskHeldCount,
        })
      : null;
  const prefillPreview =
    nextNameWatch && !nextNameWatch.dead && !liveTapeHardWait
      ? buildPrefillPreview({
          heldSymbols: deskHeldSymbols,
          watchSymbol: nextNameWatch.symbol,
          ticketInr: nextNameWatch.size.ticketInr,
          leftoverInr: nextNameWatch.size.leftoverInr,
        })
      : null;
  const campaignLine = buildCampaignLine({
    watchSymbol: nextNameWatch?.symbol ?? todayContract.watchSymbol,
    day: campaignDay || (nextNameWatch ? 1 : 0),
  });
  const firstBuyCommitLabel = resolveEmptyBookCommitLabel({
    emptyBook,
    firstBuy: firstBuyCandidate,
    starterBook,
    planReady: firstBuyPlanReady,
    verdict: verdictPresentation.verdict,
    marketOpen: canPlaceMarketOrder,
    brokerDone: brokerStepCompleted || brokerStepSkipped,
  });
  const executionHero = firstBuyCandidate
    ? {
        ...todayHeroResolved,
        deployAmount: firstBuyTicket,
      }
    : todayHeroResolved;

  const primarySymbol = useMemo(
    () =>
      resolvePrimaryTradeSymbol({
        stock: decision.stock ?? topSymbol,
        growDecision,
      }),
    [decision.stock, growDecision, topSymbol],
  );

  const waitInsight = useMemo(() => {
    if (!isCapitalDeployment || verdictPresentation.verdict !== "wait") {
      return null;
    }

    return buildAlignedWaitInsight({
      intent: renderIntent,
      primarySymbol,
      growDecision,
      protectDecision,
      openHoldingsCount: openPortfolioHoldings.length,
    });
  }, [
    growDecision,
    isCapitalDeployment,
    primarySymbol,
    protectDecision,
    renderIntent,
    verdictPresentation.verdict,
    openPortfolioHoldings.length,
  ]);

  const verdictCanvasProps = useMemo(
    () => ({
      verdictWord: verdictPresentation.displayWord,
      dailyVerdict: verdictPresentation.verdict,
      headline: verdictPresentation.headline,
      subline: verdictPresentation.subline,
      executionKind: displayHero.executionKind,
      trustScore: morningBrief?.trust.trust_score ?? trustScore,
      trustDelta: morningBrief?.trust.trust_delta ?? trustDelta,
      trustMessage: morningBrief?.trust.trust_message ?? trustMessage,
      evidenceTeaser:
        firstBuyCandidate || waitInsight || youngBook
          ? undefined
          : morningBrief?.evidence.key_reasons[0] ??
            decision.reason ??
            decision.confidence_factors?.[0] ??
            decision.message ??
            undefined,
      confidence: decision.confidence,
      portfolioStale: snapshotStale,
      pollError: morningBriefError ?? livePollError,
      connectionStatus,
      brokerStepCompleted,
      brokerStepSkipped: youngBook ? false : brokerStepSkipped,
      doneForToday: verdictPresentation.doneForToday,
      ctaLabel: verdictPresentation.ctaLabel,
      tradingLocked: verdictPresentation.tradingLocked,
      hideStaleRibbon: dataFreshness.isStale || liveBookFresh,
      suppressTrustScore: dataFreshness.suppressTrustScore,
      trustFootnote: dataFreshness.trustFootnote || undefined,
      hideSetupConfidence: true,
      compactWaitCopy: false,
      chipLabel:
        firstBuyCandidate && verdictPresentation.displayWord === "Start"
          ? "First position in Kite"
          : undefined,
      hideChip:
        (emptyBook || youngBook || verdictPresentation.verdict === "pause") &&
        verdictPresentation.displayWord !== "Start",
      desk: Boolean(youngBook || starterBook),
    }),
    [
      brokerStepCompleted,
      brokerStepSkipped,
      connectionStatus,
      dataFreshness.isStale,
      dataFreshness.suppressTrustScore,
      dataFreshness.trustFootnote,
      decision.confidence,
      decision.confidence_factors,
      decision.message,
      decision.reason,
      displayHero.executionKind,
      emptyBook,
      youngBook,
      firstBuyCandidate,
      starterBook,
      liveBookFresh,
      livePollError,
      morningBrief,
      morningBriefError,
      snapshotStale,
      verdictPresentation.displayWord,
      trustDelta,
      trustMessage,
      trustScore,
      verdictPresentation,
      waitInsight,
      isExplore,
      isExploreEmpty,
    ],
  );

  const watchlistSummary = formatExplorePipelineSummaryPlain(
    capitalDecision.explorePipelineSummary,
  );

  const showPortfolioSummary =
    connectionStatus === "CONNECTED" ||
    connectionStatus === "TOKEN_EXPIRED" ||
    fundsSynced ||
    displayPortfolioHoldings.length > 0;

  const portfolioSummaryProps = useMemo(
    () => ({
      trust: {
        connectionStatus,
        marginAvailable: availableCash,
        ledgerCash,
        collateral,
        portfolioValue: displayPortfolioValue ?? portfolioValue,
        totalCapital:
          totalCapital ??
          ((displayPortfolioValue ?? portfolioValue) !== undefined &&
          ledgerCash !== undefined
            ? (displayPortfolioValue ?? portfolioValue)! + ledgerCash
            : undefined),
        openPnl: resolvedOpenPnl,
        portfolioDayPnl: liveDayPnl,
        positionsBreakdown: livePositionsBreakdown,
        lastSyncedAt: liveLastSyncedAt,
        portfolioStale: snapshotStale,
        pollError: livePollError,
        breakdownLoading,
        isPolling: livePnlPolling,
        fundsLoading,
        fundsSynced,
        fundsSyncError,
        proofHref,
        suppressStaleWarnings: dataFreshness.isStale || liveBookFresh,
      },
      holdings: {
        holdings: displayPortfolioHoldings,
        totalValue: displayPortfolioValue,
        totalPnl: displayPortfolioTotalPnl,
        deployableCash: availableCash,
        stale: snapshotStale,
        suppressStaleLabel: dataFreshness.isStale || liveBookFresh,
        loading:
          portfolioLoading &&
          displayPortfolioHoldings.length === 0 &&
          connectionStatus === "CONNECTED",
        showEmptyWhenSynced:
          !portfolioLoading &&
          (openPortfolioHoldings.length === 0 ||
            displayPortfolioHoldings.length === 0) &&
          (connectionStatus === "CONNECTED" ||
            connectionStatus === "TOKEN_EXPIRED" ||
            fundsSynced),
      },
    }),
    [
      availableCash,
      breakdownLoading,
      collateral,
      connectionStatus,
      dataFreshness.isStale,
      liveBookFresh,
      displayPortfolioHoldings,
      displayPortfolioTotalPnl,
      displayPortfolioValue,
      fundsLoading,
      fundsSynced,
      fundsSyncError,
      ledgerCash,
      liveDayPnl,
      liveLastSyncedAt,
      livePollError,
      livePnlPolling,
      livePositionsBreakdown,
      openPortfolioHoldings.length,
      portfolioLoading,
      snapshotStale,
      portfolioValue,
      proofHref,
      resolvedOpenPnl,
      totalCapital,
    ],
  );

  const primarySymbolPrice = useMemo(() => {
    if (!primarySymbol) {
      return null;
    }

    const normalized = primarySymbol.trim().toUpperCase();
    const holding = openPortfolioHoldings.find(
      (row) => row.tradingsymbol.trim().toUpperCase() === normalized,
    );

    return holding?.last_price ?? null;
  }, [openPortfolioHoldings, primarySymbol]);

  const primarySymbolQty = useMemo(() => {
    if (!primarySymbol) {
      return undefined;
    }

    const normalized = primarySymbol.trim().toUpperCase();
    return openPortfolioHoldings.find(
      (row) => row.tradingsymbol.trim().toUpperCase() === normalized,
    )?.quantity;
  }, [openPortfolioHoldings, primarySymbol]);

  const journeyBlockedByStale = dataFreshness.isStale;

  const journeyExploreSetup = capitalDecision.exploreSetups[0];
  const journeySymbol = useMemo(() => {
    if (isExplore && journeyExploreSetup?.symbol) {
      return journeyExploreSetup.symbol;
    }

    return primarySymbol;
  }, [isExplore, journeyExploreSetup?.symbol, primarySymbol]);

  const journeySymbolPrice = useMemo(() => {
    if (!journeySymbol) {
      return null;
    }

    const normalized = journeySymbol.trim().toUpperCase();
    const holding = openPortfolioHoldings.find(
      (row) => row.tradingsymbol.trim().toUpperCase() === normalized,
    );

    if (holding?.last_price) {
      return holding.last_price;
    }

    const trigger = exploreTriggerBySymbol.get(normalized);
    if (trigger?.livePrice) {
      return trigger.livePrice;
    }

    const pick = decision.picks?.find(
      (row) => row.stock.trim().toUpperCase() === normalized,
    );

    if (pick?.price && pick.price > 0) {
      return pick.price;
    }

    return primarySymbolPrice;
  }, [
    decision.picks,
    exploreTriggerBySymbol,
    journeySymbol,
    openPortfolioHoldings,
    primarySymbolPrice,
  ]);

  const journeyApexSuggested = Boolean(journeySymbol && (isExplore || isCapitalDeployment));
  const journeyPreferSwing =
    isExplore &&
    (journeyExploreSetup?.stage === "Close to readiness" ||
      journeyExploreSetup?.stage === "Developing setup");

  const showTodayVerdict = isCapitalDeployment || isExplore;

  return (
    <div className={`mx-auto w-full max-w-[600px] ${className}`.trim()}>
      <ApexCard
        hover={false}
        padding="none"
        className="relative overflow-hidden border-transparent bg-transparent shadow-none animate-apex-rise-in"
      >
        <div
          className={[
            "pointer-events-none absolute inset-0 bg-gradient-to-b to-transparent",
            experience.cardGradient,
          ].join(" ")}
        />

        <div className={`relative p-4 sm:p-6 ${contentClassName}`}>
          <div className="mb-6 space-y-4">
            {researchHandoff ? (
              <ResearchTodayHandoff
                symbol={researchHandoff.symbol}
                verdict={researchHandoff.verdict}
                headline={researchHandoff.headline}
                onDismiss={researchHandoff.onDismiss}
              />
            ) : null}

            {showTodayVerdict ? (
              <>
                {morningBriefLoading && !morningBrief && isCapitalDeployment ? (
                  <p className="text-xs text-apex-muted/60">Loading today&apos;s decision…</p>
                ) : null}
                {morningBriefError && !morningBrief && isCapitalDeployment ? (
                  <p className="text-xs text-amber-200/80">{morningBriefError}</p>
                ) : null}
                <TodaySyncStatusBanner
                  freshness={dataFreshness}
                  onSoftRefresh={onBrokerDataRefresh}
                  refreshing={brokerDataRefreshing}
                  autoRetryInProgress={autoSyncRetrying}
                  autoRetryDetail={autoSyncRetryDetail}
                />
                {youngBook || starterBook ? (
                  <TodayDeskStatus
                    heartbeat={deskHeartbeatLine({
                      lastWatchAt,
                      marketOpen: isNseCashSessionOpen(),
                    })}
                    interrupt={interruptHealthLine(interruptReady)}
                  />
                ) : null}
                {yesterdayLine && (youngBook || starterBook) ? (
                  <p className="text-center text-xs font-medium uppercase tracking-[0.18em] text-apex-muted/70">
                    {yesterdayLine}
                  </p>
                ) : null}
                {closeLetter && (youngBook || starterBook) ? (
                  <TodayCloseLetter letter={closeLetter} />
                ) : null}
                {stillTrue && (youngBook || starterBook) ? (
                  <TodayStillTrue
                    line={stillTrue.line}
                    saving={stillTrueSaving}
                    onConfirm={() => {
                      setStillTrueSaving(true);
                      void apiFetch("/api/thesis", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                          symbol: stillTrue.symbol,
                          thesis: stillTrue.thesis,
                          invalidation: stillTrue.invalidation,
                        }),
                      })
                        .then(() => setStillTrue(null))
                        .finally(() => setStillTrueSaving(false));
                    }}
                  />
                ) : null}
                <VerdictCanvas {...verdictCanvasProps} />
                {(youngBook || starterBook) &&
                verdictPresentation.verdict === "wait" &&
                (!nextNameWatch || liveTapeHardWait) ? (
                  <TodayKiteContract contract={todayContract} />
                ) : null}
                <TodayBookLine
                  connectionStatus={connectionStatus}
                  portfolioValue={displayPortfolioValue}
                  cashInr={emptyBook ? availableCash ?? null : null}
                  dayPnl={starterHoldLines ? null : liveDayPnl}
                />
                {starterHoldLines ? (
                  <TodayStarterHoldCard
                    lines={starterHoldLines}
                    hideCashFork={Boolean(nextNameWatch)}
                    diary={latestDiaryLine(nameDiary, starterHoldLines.symbol)}
                    yourCutInr={
                      holdCuts[starterHoldLines.symbol.trim().toUpperCase()] ?? null
                    }
                    cutSaving={cutSaving === starterHoldLines.symbol.trim().toUpperCase()}
                    onSaveCut={(cut) => {
                      const name = starterHoldLines.symbol.trim().toUpperCase();
                      setCutSaving(name);
                      setHoldCuts((current) => ({ ...current, [name]: cut }));
                      setNameDiary((current) =>
                        appendNameDiary(current, {
                          dateKey: tradingDateKey(),
                          symbol: name,
                          line: `Break below ₹${Math.round(cut)}`,
                        }),
                      );
                      void apiFetch("/api/thesis", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                          symbol: name,
                          thesis: holdTheses[name] || `Hold ${name}.`,
                          invalidation: `Break below ₹${Math.round(cut)}`,
                        }),
                      }).finally(() => setCutSaving(null));
                    }}
                  />
                ) : null}
                {starterHoldLines ? (
                  <TodayNameDiary
                    symbol={starterHoldLines.symbol}
                    dateKey={latestDiaryLine(nameDiary, starterHoldLines.symbol)?.dateKey}
                    line={latestDiaryLine(nameDiary, starterHoldLines.symbol)?.line}
                  />
                ) : null}
                {youngHoldLines.length > 0 ? (
                  <div className="space-y-3">
                    {youngHoldLines.map((lines) => (
                      <TodayStarterHoldCard
                        key={lines.symbol}
                        lines={lines}
                        hideCashFork
                        compact
                        yourCutInr={holdCuts[lines.symbol.trim().toUpperCase()] ?? null}
                        cutSaving={cutSaving === lines.symbol.trim().toUpperCase()}
                        onSaveCut={(cut) => {
                          const name = lines.symbol.trim().toUpperCase();
                          setCutSaving(name);
                          setHoldCuts((current) => ({ ...current, [name]: cut }));
                          setNameDiary((current) =>
                            appendNameDiary(current, {
                              dateKey: tradingDateKey(),
                              symbol: name,
                              line: `Break below ₹${Math.round(cut)}`,
                            }),
                          );
                          void apiFetch("/api/thesis", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                              symbol: name,
                              thesis: holdTheses[name] || `Hold ${name}.`,
                              invalidation: `Break below ₹${Math.round(cut)}`,
                            }),
                          }).finally(() => setCutSaving(null));
                        }}
                      />
                    ))}
                    {youngHoldLines.map((lines) => (
                      <TodayNameDiary
                        key={`diary-${lines.symbol}`}
                        symbol={lines.symbol}
                        dateKey={latestDiaryLine(nameDiary, lines.symbol)?.dateKey}
                        line={latestDiaryLine(nameDiary, lines.symbol)?.line}
                      />
                    ))}
                    {youngCashCopy && !nextNameWatch ? (
                      <div className="rounded-2xl border border-sky-300/15 bg-sky-400/[0.08] px-4 py-3">
                        <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-sky-100/70">
                          Cash mandate
                        </p>
                        <p className="mt-1 text-xl font-semibold tracking-tight text-apex-text">
                          {youngCashCopy.amountLabel}
                        </p>
                        <p className="mt-1 text-sm leading-relaxed text-apex-muted/85">
                          {youngCashCopy.line}
                        </p>
                      </div>
                    ) : null}
                  </div>
                ) : null}
                {prefillPreview && (youngBook || starterBook) ? (
                  <TodayPrefillCard
                    headline={prefillPreview.headline}
                    bookLine={prefillPreview.bookLine}
                    leftoverLine={prefillPreview.leftoverLine}
                  />
                ) : null}
                {nextNameWatch && !liveTapeHardWait ? (
                  <TodaySecondNameCard
                    watch={nextNameWatch}
                    kiteLine={todayContract.kiteLine}
                    thesis={humanThesis}
                    campaignLine={campaignLine}
                    gttStatus={gttStatus}
                    gttBusy={gttBusy}
                    onSetGtt={
                      nextNameWatch.triggerInr && nextNameWatch.livePriceInr
                        ? () => {
                            setGttBusy(true);
                            void apiFetch("/api/trade/gtt", {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({
                                tradingsymbol: nextNameWatch.symbol,
                                triggerPrice: nextNameWatch.triggerInr,
                                lastPrice: nextNameWatch.livePriceInr,
                                ticketInr: nextNameWatch.size.ticketInr,
                              }),
                            })
                              .then(async (response) => {
                                const payload = await parseApiJson<{
                                  status?: string;
                                }>(response, "GTT");
                                if (response.ok) {
                                  setGttStatus(
                                    normalizeGttStatus(payload?.status) ?? "active",
                                  );
                                }
                              })
                              .finally(() => setGttBusy(false));
                          }
                        : undefined
                    }
                  />
                ) : null}
                {(youngBook || starterBook) && todayLoop.line ? (
                  <p className="text-center text-sm font-medium text-apex-text/90">
                    {todayLoop.line}
                  </p>
                ) : null}
                {(youngBook || starterBook) &&
                verdictPresentation.verdict === "wait" &&
                todayLoop.state !== "placed_watch" ? (
                  todayLoop.state === "followed_wait" ||
                  retention.committedToday ? (
                    <p className="text-center text-xs font-semibold uppercase tracking-[0.22em] text-apex-muted/70">
                      Waited · day closed
                    </p>
                  ) : (
                    <button
                      type="button"
                      onClick={() => {
                        persistTodayContract({
                          ...todayContract,
                          outcome: "followed_wait",
                          outcomeLine: todayLoop.watchSymbol
                            ? `Followed. No ${todayLoop.watchSymbol} fill.`
                            : "Followed. Day closed.",
                        });
                        retention.commitFollowed();
                      }}
                      className="w-full rounded-2xl border border-white/15 bg-white px-4 py-3.5 text-sm font-semibold text-black transition-colors hover:bg-white/90"
                    >
                      I waited
                    </button>
                  )
                ) : null}
                {emptyBook &&
                onIntentChange &&
                !isExplore &&
                capitalDecision.exploreSetups.length > 0 ? (
                  <button
                    type="button"
                    onClick={() => onIntentChange("explore")}
                    className="text-xs font-medium text-apex-muted/70 underline underline-offset-2 hover:text-apex-text"
                  >
                    {capitalDecision.exploreSetups.length} names watching →
                  </button>
                ) : null}
                {emptyBook && isExplore && onIntentChange ? (
                  <button
                    type="button"
                    onClick={() => onIntentChange("grow")}
                    className="text-xs font-medium text-apex-muted/70 underline underline-offset-2 hover:text-apex-text"
                  >
                    Today →
                  </button>
                ) : null}
              </>
            ) : null}

            {isRefreshing ? (
              <p className="text-xs text-apex-muted/60">Refreshing decision…</p>
            ) : null}
          </div>

          <div id="today-execution" />

          {isCapitalDeployment ? (
            <div className="mb-6 space-y-4">
              {brokerFillSummary &&
              brokerStepCompleted &&
              !receiptDismissed &&
              todayHero.symbol ? (
                <DecisionReceipt
                  symbol={todayHero.symbol}
                  executionKind={todayHero.executionKind}
                  fill={brokerFillSummary}
                  trustDelta={trustDelta}
                  onDismiss={() => setReceiptDismissed(true)}
                />
              ) : null}
              {showExecutionPanel ? (
                <TodayExecutionPanel
                  hero={executionHero}
                  portfolioValue={displayPortfolioValue ?? portfolioValue ?? 0}
                  holdingAllocationPct={holdingAllocationPct}
                  entryTiming={entryTiming}
                  plan={plan}
                  planLoading={planLoading}
                  brokerStepCompleted={brokerStepResolved}
                  brokerStepSkipped={brokerStepSkipped}
                  brokerFillSummary={brokerFillSummary}
                  postTrimPortfolioWeight={actualSymbolWeight}
                  brokerFillStatusLoading={brokerFillStatusLoading}
                  tradingLocked={verdictPresentation.tradingLocked}
                  dailyVerdict={verdictPresentation.verdict}
                  pauseReason={verdictPresentation.pauseReason}
                  onHoldTrim={() => void handleHoldTrim()}
                  holdTrimProcessing={processingHoldTrim}
                  onExecuted={handleExecuted}
                  firstBuy={firstBuyCandidate}
                  planReady={firstBuyPlanReady}
                  availableCash={availableCash}
                  entryInr={firstBuyPlanLines.entryInr}
                  holdLabel={FIRST_BUY_HOLD_LABEL}
                  onTicketChange={setTicketOverride}
                />
              ) : null}
              {hideTodayDump ? null : (
              <TodayDetailsAccordion>
                {showPortfolioSummary ? (
                  <TodayPortfolioSummary {...portfolioSummaryProps} />
                ) : null}
                {openPortfolioHoldings.length > 0 ? (
                  <SectorCapStrip summary={sectorCapSummary} compact />
                ) : null}
                {waitInsight ? (
                  <TodayWaitInsightCard insight={waitInsight} />
                ) : null}
                {journeySymbol ? (
                  <InvestmentJourneyPanel
                    symbol={journeySymbol}
                    currentPriceInr={journeySymbolPrice}
                    quantity={primarySymbolQty}
                    dailyVerdict={verdictPresentation.verdict}
                    brokerStepCompleted={brokerStepCompleted}
                    compact={verdictPresentation.verdict === "wait"}
                    portfolioDataStale={journeyBlockedByStale}
                    apexSuggested={journeyApexSuggested}
                    preferSwing={journeyPreferSwing}
                    activationLevelInr={
                      decision.picks?.find(
                        (pick) =>
                          pick.stock.trim().toUpperCase() ===
                          journeySymbol.trim().toUpperCase(),
                      )?.activationLevel
                    }
                    onTakeProfit={() => {
                      document
                        .getElementById("today-execution")
                        ?.scrollIntoView({ behavior: "smooth", block: "start" });
                    }}
                  />
                ) : null}
                <OperatingManualStrip
                  dailyVerdict={verdictPresentation.verdict}
                  tacticalPoolInr={decision.amount ?? morningBrief?.portfolio.tactical_pool_inr}
                  collapseByDefault={collapsePlanByDefault}
                />
                <CapitalDamsStrip
                  portfolioValue={displayPortfolioValue}
                  portfolioDayPnl={liveDayPnl}
                  consecutiveLossDays={consecutiveLossDays}
                />
                <TodayProgressStrip
                  portfolioDayPnl={liveDayPnl}
                  trustScore={trustScore}
                  trustDelta={trustDelta}
                  streakCount={retention.streakCount}
                  streakMessage={retention.streakMessage}
                />
                <WeeklyReviewStrip
                  history={disciplineHistory}
                  summary={disciplineSummary}
                  days={disciplineDays}
                />
                {lastOutcome ? (
                  <LastClosedTrustBlock
                    lastOutcome={lastOutcome}
                    lastOutcomeStock={lastOutcomeStock}
                    compact
                  />
                ) : null}
                {onCapitalModeChange ? (
                  <CapitalModeToggle
                    mode={capitalMode ?? "CASH"}
                    onModeChange={onCapitalModeChange}
                    collateral={collateral}
                    premiumLocked={!features.marginMode}
                    activationEnabled={premiumActivationEnabled}
                    onPremiumActivated={onPremiumActivated}
                  />
                ) : null}
                <div className="space-y-2">
                  <p className="text-xs text-apex-muted/60">
                    {retention.dailyContextLabel}
                  </p>
                  {retention.decisionTensionLine ? (
                    <p className="text-xs text-apex-muted/55">
                      {retention.decisionTensionLine}
                    </p>
                  ) : null}
                  {brokerStepLine ? (
                    <p className="text-xs text-apex-muted/55">{brokerStepLine}</p>
                  ) : null}
                  <p className="text-xs text-apex-muted/50">
                    {retention.sessionTimeContext}
                  </p>
                </div>
                <TodayMonitorStrip
                  positions={monitorPositions}
                  openPnl={monitorStripOpenPnl}
                  liveTicksById={monitorLiveTicksById}
                  loading={monitorLoading && monitorPositions.length === 0}
                  showWhenEmpty={monitorEnabled}
                />
                {morningBrief ? (
                  <div className="space-y-3">
                    <TodayDisciplineChip discipline={morningBrief.discipline} />
                    <TodayBelowFold brief={morningBrief} />
                  </div>
                ) : null}
                <details className="group rounded-xl border border-apex-border/15 bg-white/[0.02]">
                  <summary className="cursor-pointer list-none px-4 py-3 text-sm font-medium text-apex-text/85 marker:content-none">
                    Decision depth
                  </summary>
                  <div className="border-t border-apex-border/10 px-4 py-4">
                    {features.decisionDepth ? (
                      <CapitalActionsBlock
                        decision={capitalDecision}
                        delayMs={nextDelay()}
                        depthOnly
                        brokerStepCompleted={brokerStepCompleted}
                        brokerSymbol={todayHero.symbol}
                        executionKind={todayHero.executionKind}
                        postTrimPortfolioWeight={actualSymbolWeight}
                        projectedWeightAfter={todayHero.targetWeightAfter}
                        brokerFillSummary={brokerFillSummary}
                      />
                    ) : (
                      <PremiumFeatureGate
                        feature="decisionDepth"
                        activationEnabled={premiumActivationEnabled}
                        onActivated={onPremiumActivated}
                      />
                    )}
                  </div>
                </details>
              </TodayDetailsAccordion>
              )}
            </div>
          ) : isExplore ? (
            <div className="mb-6">
              {emptyBook ? (
                !isExploreEmpty ? (
                  <TodayWatchlistPanel
                    setups={capitalDecision.exploreSetups}
                    summary={watchlistSummary}
                    liveTriggers={exploreTriggerBySymbol}
                  />
                ) : (
                  <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-3">
                    <p className="text-sm text-apex-text/90">No ideas on the watchlist yet.</p>
                    <Link
                      href="/app/research"
                      className="mt-2 inline-block text-sm font-medium text-sky-200 underline underline-offset-2 hover:text-white"
                    >
                      Open Research →
                    </Link>
                  </section>
                )
              ) : (
              <TodayDetailsAccordion>
                {!isExploreEmpty ? (
                  <TodayWatchlistPanel
                    setups={capitalDecision.exploreSetups}
                    summary={watchlistSummary}
                    liveTriggers={exploreTriggerBySymbol}
                  />
                ) : (
                  <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-3">
                    <p className="text-sm text-apex-text/90">No ideas on the watchlist yet.</p>
                    <Link
                      href="/app/research"
                      className="mt-2 inline-block text-sm font-medium text-sky-200 underline underline-offset-2 hover:text-white"
                    >
                      Open Research →
                    </Link>
                  </section>
                )}
                {showPortfolioSummary ? (
                  <TodayPortfolioSummary {...portfolioSummaryProps} />
                ) : null}
                {waitInsight ? (
                  <TodayWaitInsightCard insight={waitInsight} />
                ) : null}
                {journeySymbol ? (
                  <InvestmentJourneyPanel
                    symbol={journeySymbol}
                    currentPriceInr={journeySymbolPrice}
                    quantity={primarySymbolQty}
                    dailyVerdict={verdictPresentation.verdict}
                    brokerStepCompleted={brokerStepCompleted}
                    compact={verdictPresentation.verdict === "wait"}
                    portfolioDataStale={journeyBlockedByStale}
                    apexSuggested={journeyApexSuggested}
                    preferSwing={journeyPreferSwing}
                    activationLevelInr={
                      decision.picks?.find(
                        (pick) =>
                          pick.stock.trim().toUpperCase() ===
                          journeySymbol.trim().toUpperCase(),
                      )?.activationLevel
                    }
                    onTakeProfit={() => {
                      document
                        .getElementById("today-execution")
                        ?.scrollIntoView({ behavior: "smooth", block: "start" });
                    }}
                  />
                ) : null}
                <OperatingManualStrip
                  dailyVerdict={verdictPresentation.verdict}
                  tacticalPoolInr={decision.amount ?? morningBrief?.portfolio.tactical_pool_inr}
                  collapseByDefault={collapsePlanByDefault}
                />
                <CapitalDamsStrip
                  portfolioValue={displayPortfolioValue}
                  portfolioDayPnl={liveDayPnl}
                  consecutiveLossDays={consecutiveLossDays}
                />
                <TodayProgressStrip
                  portfolioDayPnl={liveDayPnl}
                  trustScore={trustScore}
                  trustDelta={trustDelta}
                  streakCount={retention.streakCount}
                  streakMessage={retention.streakMessage}
                />
                <WeeklyReviewStrip
                  history={disciplineHistory}
                  summary={disciplineSummary}
                  days={disciplineDays}
                />
              </TodayDetailsAccordion>
              )}
            </div>
          ) : null}

          {youngBook ? null : (
          <ExecutionStatusBlock
            committedToday={retention.committedToday}
            onMarkFollowed={retention.commitFollowed}
            streakMessage={retention.streakMessage}
            pressureLine={retention.pressureLine}
            waitDisciplineReward={retention.waitDisciplineReward}
            rewardHook={retention.rewardHook}
            commitmentHeadline={retention.commitmentHeadline}
            commitmentMicroReward={retention.commitmentMicroReward}
            delayMs={nextDelay()}
            capitalDeployment={isCapitalDeployment}
            decision={capitalDecision}
            executionKind={todayHero.executionKind}
            brokerStepCompleted={brokerStepCompleted}
            followCtaLabel={firstBuyCommitLabel ?? undefined}
            quiet={hideTodayDump}
          />
          )}

        </div>
      </ApexCard>
    </div>
  );
}
