export function isAdvisorPilotEnabled(): boolean {
  return process.env.APEX_ADVISOR_PILOT_ENABLED === "true";
}

export function readAdvisorPilotSeats(): number {
  const raw = Number(process.env.APEX_ADVISOR_PILOT_SEATS ?? "1");

  if (!Number.isFinite(raw) || raw < 1) {
    return 1;
  }

  return Math.min(10, Math.floor(raw));
}

export function runAdvisorPilotConfigSelfCheck(): void {
  const seats = readAdvisorPilotSeats();

  if (seats < 1 || seats > 10) {
    throw new Error("Advisor pilot config self-check failed: seats bounds");
  }
}
