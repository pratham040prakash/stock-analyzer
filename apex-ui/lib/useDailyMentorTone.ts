"use client";

import { useSyncExternalStore } from "react";
import type { MentorTone } from "@/lib/mentorCopy";

const TONES: MentorTone[] = [
  "calm",
  "concerned",
  "encouraging",
  "observational",
];

const DEFAULT_TONE: MentorTone = "calm";

function computeDailyTone(): MentorTone {
  const day = new Date().getDate();
  return TONES[day % TONES.length];
}

export function useDailyMentorTone(): MentorTone {
  return useSyncExternalStore(
    () => () => {},
    computeDailyTone,
    () => DEFAULT_TONE,
  );
}
