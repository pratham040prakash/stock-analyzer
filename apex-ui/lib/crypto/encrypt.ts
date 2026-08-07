import { createCipheriv, createDecipheriv, randomBytes } from "crypto";

const ALGORITHM = "aes-256-gcm";

function getEncryptionKey(): Buffer {
  const raw = process.env.TOKEN_ENCRYPTION_KEY?.trim();

  if (!raw) {
    throw new Error("TOKEN_ENCRYPTION_KEY is not configured");
  }

  if (/^[0-9a-fA-F]{64}$/.test(raw)) {
    return Buffer.from(raw, "hex");
  }

  const decoded = Buffer.from(raw, "base64");
  if (decoded.length !== 32) {
    throw new Error("TOKEN_ENCRYPTION_KEY must be 32 bytes (hex or base64)");
  }

  return decoded;
}

export function encryptToken(plaintext: string): string {
  const key = getEncryptionKey();
  const iv = randomBytes(12);
  const cipher = createCipheriv(ALGORITHM, key, iv);
  const encrypted = Buffer.concat([
    cipher.update(plaintext, "utf8"),
    cipher.final(),
  ]);
  const tag = cipher.getAuthTag();

  return Buffer.concat([iv, tag, encrypted]).toString("base64");
}

export function decryptToken(payload: string): string {
  const key = getEncryptionKey();
  const buffer = Buffer.from(payload, "base64");
  const iv = buffer.subarray(0, 12);
  const tag = buffer.subarray(12, 28);
  const encrypted = buffer.subarray(28);

  const decipher = createDecipheriv(ALGORITHM, key, iv);
  decipher.setAuthTag(tag);

  return Buffer.concat([decipher.update(encrypted), decipher.final()]).toString(
    "utf8",
  );
}

export function isTokenEncryptionConfigured(): boolean {
  return Boolean(process.env.TOKEN_ENCRYPTION_KEY?.trim());
}
