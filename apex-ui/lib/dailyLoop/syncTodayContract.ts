import { apiFetch } from "@/lib/api/clientFetch";
import {
  persistTodayContract,
  readTodayContract,
  type TodayContract,
} from "@/lib/dailyLoop/todayContract";

export function syncTodayContractToServer(contract: TodayContract): void {
  persistTodayContract(contract);
  void apiFetch("/api/today/contract", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(contract),
  }).catch(() => {
    // Local contract remains the same-device fallback.
  });
}

/** Load the server desk, then write today's local contract if one already exists. */
export function hydrateAndSyncTodayContract(): void {
  void (async () => {
    try {
      await apiFetch("/api/today/contract", { cache: "no-store" });
    } catch {
      // Persist still runs below from localStorage.
    }

    const local = readTodayContract();
    if (local?.kiteLine && local.rule && local.dateKey) {
      syncTodayContractToServer(local);
    }
  })();
}
