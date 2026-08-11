export function resolveOperatingProfileDbError(error: unknown): {
  message: string;
  status: number;
  migrationRequired: boolean;
} {
  const text =
    error instanceof Error
      ? `${error.message}${error.cause ? ` ${String(error.cause)}` : ""}`
      : String(error);

  const migrationRequired =
    text.includes("operating_profiles") &&
    (text.includes("does not exist") ||
      text.includes("Could not find") ||
      text.includes("schema cache"));

  if (migrationRequired) {
    return {
      message:
        "Server storage is not ready yet (operating_profile migration pending). Saved on this device for now.",
      status: 503,
      migrationRequired: true,
    };
  }

  return {
    message: "Could not save operating profile. Try again.",
    status: 500,
    migrationRequired: false,
  };
}

export function runOperatingProfileErrorsSelfCheck(): void {
  const resolved = resolveOperatingProfileDbError(
    new Error('relation "public.operating_profiles" does not exist'),
  );

  if (!resolved.migrationRequired || resolved.status !== 503) {
    throw new Error("Operating profile errors self-check failed: missing table");
  }
}
