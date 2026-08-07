"use client";

import { useSyncExternalStore } from "react";

function computeGreeting(name: string): string {
  const hour = new Date().getHours();

  let message = "Hello";

  if (hour < 12) message = "Good morning";
  else if (hour < 17) message = "Good afternoon";
  else message = "Good evening";

  return `${message}, ${name}.`;
}

function getServerGreeting(name: string): string {
  return `Hello, ${name}.`;
}

export function useGreeting(name: string) {
  return useSyncExternalStore(
    () => () => {},
    () => computeGreeting(name),
    () => getServerGreeting(name),
  );
}
