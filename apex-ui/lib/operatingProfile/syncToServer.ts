import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import {
  readLocalOperatingProfile,
  writeLocalOperatingProfile,
} from "@/lib/operatingProfile/clientStore";
import type { OperatingProfile } from "@/types/operatingProfile";

type OperatingProfileGetResponse = {
  profile: OperatingProfile | null;
  complete: boolean;
};

type OperatingProfilePutResponse = {
  profile: OperatingProfile;
  complete: boolean;
};

/**
 * When onboarding saved locally (503 / migration pending), push to server once
 * the table is available so profile survives device changes.
 */
export async function syncLocalOperatingProfileToServer(): Promise<OperatingProfile | null> {
  const local = readLocalOperatingProfile();
  if (!local) {
    return null;
  }

  const getRes = await apiFetch("/api/operating-profile", { cache: "no-store" });
  const getData = await parseApiJson<OperatingProfileGetResponse>(
    getRes,
    "Operating profile",
  );

  if (getRes.ok && getData?.complete && getData.profile) {
    writeLocalOperatingProfile(getData.profile);
    return getData.profile;
  }

  if (!getRes.ok) {
    return local;
  }

  const putRes = await apiFetch("/api/operating-profile", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      investmentStyle: local.investmentStyle,
      intradayAcknowledged: true,
    }),
  });

  if (putRes.ok) {
    const putData = await parseApiJson<OperatingProfilePutResponse>(
      putRes,
      "Operating profile",
    );
    const synced = putData?.profile ?? local;
    writeLocalOperatingProfile(synced);
    return synced;
  }

  return local;
}

export function runOperatingProfileSyncSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Operating profile sync self-check failed: ${message}`);
    }
  };

  assert(
    typeof syncLocalOperatingProfileToServer === "function",
    "Must export syncLocalOperatingProfileToServer",
  );
}
