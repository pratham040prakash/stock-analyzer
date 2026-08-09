import type { ConnectionStatus } from "@/lib/broker/zerodha";

export type FirstRunStepId = "connect" | "profile" | "today";

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
  todayReady: boolean;
  decisionLoading?: boolean;
}): FirstRunProgress {
  const connectDone = isBrokerConnected(input.connectionStatus);
  const profileDone = input.profileComplete;
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
      id: "today",
      label: "Open Today",
      detail: input.decisionLoading
        ? "Preparing today's capital decision…"
        : "One clear action for this session.",
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

  const complete = connectDone && profileDone && todayDone;
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
