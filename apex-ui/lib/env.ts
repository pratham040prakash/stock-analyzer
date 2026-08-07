export const isDev = process.env.NODE_ENV !== "production";
export const isProd = process.env.NODE_ENV === "production";

export function devLog(message: string, detail?: unknown): void {
  if (process.env.NODE_ENV === "production") return;

  if (detail !== undefined) {
    console.log(message, detail);
    return;
  }

  console.log(message);
}

export function devError(message: string, detail?: unknown): void {
  if (process.env.NODE_ENV === "production") return;

  if (detail !== undefined) {
    console.error(message, detail);
    return;
  }

  console.error(message);
}
