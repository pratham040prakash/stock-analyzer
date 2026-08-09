export const COMMITMENT_PRE =
  "I commit to following this capital decision today.";

export const COMMITMENT_POST =
  "Committed. This decision defines today's capital behavior.";

const COMMITMENT_MICRO_REWARDS = [
  "Consistency compounds into capital protection.",
  "Discipline today reduces risk tomorrow.",
] as const;

export type CommitmentCopy = {
  headline: string;
  microReward: string | null;
};

export function getCommitmentMicroReward(seed: string): string | null {
  let hash = 0;

  for (let index = 0; index < seed.length; index += 1) {
    hash = (hash + seed.charCodeAt(index)) % 997;
  }

  if (hash % 5 !== 0) {
    return null;
  }

  return COMMITMENT_MICRO_REWARDS[hash % COMMITMENT_MICRO_REWARDS.length];
}

export function buildCommitmentCopy(
  committedToday: boolean,
  seed: string,
): CommitmentCopy {
  if (!committedToday) {
    return {
      headline: COMMITMENT_PRE,
      microReward: null,
    };
  }

  return {
    headline: COMMITMENT_POST,
    microReward: getCommitmentMicroReward(seed),
  };
}

export function runCommitmentSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Commitment self-check failed: ${message}`);
    }
  };

  const pre = buildCommitmentCopy(false, "seed");
  assert(pre.headline === COMMITMENT_PRE, "Pre-commit must show commitment prompt");
  assert(pre.microReward === null, "Pre-commit must not show micro reward");

  const post = buildCommitmentCopy(true, "2026-08-09:grow:buy:INFY");
  assert(post.headline === COMMITMENT_POST, "Post-commit must show committed copy");
}
