import type { ConnectionStatus } from "@/lib/broker/zerodha";

export type FirstRunStepId = "connect" | "profile" | "style" | "today";

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
}): FirstRunProgress {
  const connectDone = isBrokerConnected(input.connectionStatus);
  const profileDone = input.profileComplete;
  const styleDone = input.operatingProfileComplete;
  const todayDone = input.todayReady;

  const rawSteps: Array<{
    id: FirstRunStepId;
    label: string;
    detail: string;
    done: boolean;
  }> = [
    {
      id: "connect",
      label: "Connect Zerodha",
      detail: "Read-only link to your real holdings and cash.",
      done: connectDone,
    },
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

  const complete = connectDone && profileDone && styleDone && todayDone;
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
    connectionStatus: "CONNECTED",
    profileComplete: true,
    operatingProfileComplete: false,
    todayReady: false,
  });

  assert(blocked.steps.length === 4, "First run must have four steps");
  assert(blocked.steps[2]?.id === "style", "Style step must be third");
  assert(blocked.steps[2]?.status === "current", "Style must be current when pending");

  const complete = buildFirstRunProgress({
    connectionStatus: "CONNECTED",
    profileComplete: true,
    operatingProfileComplete: true,
    todayReady: true,
  });

  assert(complete.complete, "All steps done must mark complete");
}
