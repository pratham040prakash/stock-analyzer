import type { ConnectionStatus } from "@/lib/broker/zerodha";
import { KITE_CONNECT_DISCIPLINE } from "@/lib/gtm/kiteConnectDisciplineCopy";

export type FirstRunStepId = "profile" | "style" | "connect" | "today";

export type FirstRunStepStatus = "done" | "current" | "pending";

export type FirstRunStep = {
  id: FirstRunStepId;
  label: string;
  detail: string;
  status: FirstRunStepStatus;
};

export type FirstRunProgress = {
  steps: FirstRunStep[];
  complete: boolean;
  currentIndex: number;
  headline: string;
};

function isBrokerConnected(status: ConnectionStatus): boolean {
  return status === "CONNECTED";
}

export function buildFirstRunProgress(input: {
  connectionStatus: ConnectionStatus;
  profileComplete: boolean;
  operatingProfileComplete: boolean;
  todayReady: boolean;
  decisionLoading?: boolean;
  brokerConnectSkipped?: boolean;
}): FirstRunProgress {
  const profileDone = input.profileComplete;
  const styleDone = input.operatingProfileComplete;
  const connectDone =
    isBrokerConnected(input.connectionStatus) || Boolean(input.brokerConnectSkipped);
  const todayDone = input.todayReady;

  const rawSteps: Array<{
    id: FirstRunStepId;
    label: string;
    detail: string;
    done: boolean;
  }> = [
    {
      id: "profile",
      label: "Set capital context",
      detail: "Income and expense ranges — rough numbers are fine.",
      done: profileDone,
    },
    {
      id: "style",
      label: "Choose investment style",
      detail: "Long-term vs tactical — and confirm APEX is not for intraday.",
      done: styleDone,
    },
    {
      id: "connect",
      label: input.brokerConnectSkipped && !isBrokerConnected(input.connectionStatus)
        ? "Connect Zerodha later"
        : "Connect Zerodha",
      detail: input.brokerConnectSkipped && !isBrokerConnected(input.connectionStatus)
        ? KITE_CONNECT_DISCIPLINE.skipDetail
        : KITE_CONNECT_DISCIPLINE.firstRunConnectDetail,
      done: connectDone,
    },
    {
      id: "today",
      label: "Open Today",
      detail: input.decisionLoading
        ? "Preparing today's capital decision…"
        : "One clear Wait · Trade · Pause verdict.",
      done: todayDone,
    },
  ];

  let currentIndex = rawSteps.findIndex((step) => !step.done);

  if (currentIndex === -1) {
    currentIndex = rawSteps.length - 1;
  }

  const steps: FirstRunStep[] = rawSteps.map((step, index) => {
    if (step.done) {
      return { ...step, status: "done" };
    }

    if (index === currentIndex) {
      return { ...step, status: "current" };
    }

    return { ...step, status: "pending" };
  });

  const complete = profileDone && styleDone && todayDone;
  const stepNumber = Math.min(currentIndex + 1, rawSteps.length);

  return {
    steps,
    complete,
    currentIndex,
    headline: complete
      ? "You're set for Today."
      : `Getting started · step ${stepNumber} of ${rawSteps.length}`,
  };
}

export function runFirstRunSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`First run self-check failed: ${message}`);
    }
  };

  const blocked = buildFirstRunProgress({
    connectionStatus: "NOT_CONNECTED",
    profileComplete: true,
    operatingProfileComplete: false,
    todayReady: false,
  });

  assert(blocked.steps.length === 4, "First run must have four steps");
  assert(blocked.steps[0]?.id === "profile", "Profile must be first");
  assert(blocked.steps[1]?.id === "style", "Style step must be second");
  assert(blocked.steps[1]?.status === "current", "Style must be current when pending");
  assert(blocked.steps[2]?.id === "connect", "Connect must be third and skippable");

  const skipped = buildFirstRunProgress({
    connectionStatus: "NOT_CONNECTED",
    profileComplete: true,
    operatingProfileComplete: true,
    brokerConnectSkipped: true,
    todayReady: true,
  });

  assert(skipped.complete, "Skip + setup must complete first-run");
  assert(
    skipped.steps[2]?.status === "done",
    "Skipped connect must count as done",
  );

  const todayWithoutKite = buildFirstRunProgress({
    connectionStatus: "NOT_CONNECTED",
    profileComplete: true,
    operatingProfileComplete: true,
    todayReady: true,
  });

  assert(
    todayWithoutKite.complete,
    "Today after setup must finish first-run even if Kite waits",
  );

  const complete = buildFirstRunProgress({
    connectionStatus: "CONNECTED",
    profileComplete: true,
    operatingProfileComplete: true,
    todayReady: true,
  });

  assert(complete.complete, "All steps done must mark complete");
}
