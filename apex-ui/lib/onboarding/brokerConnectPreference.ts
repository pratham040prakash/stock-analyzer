const SKIP_KEY = "apex_broker_connect_skipped_v1";
const PENDING_KEY = "apex_kite_connect_pending_v1";

function getLocalStorage(): Storage | null {
  if (typeof globalThis.localStorage === "undefined") {
    return null;
  }

  return globalThis.localStorage;
}

function getSessionStorage(): Storage | null {
  if (typeof globalThis.sessionStorage === "undefined") {
    return null;
  }

  return globalThis.sessionStorage;
}

export function readBrokerConnectSkipped(): boolean {
  return getLocalStorage()?.getItem(SKIP_KEY) === "1";
}

export function writeBrokerConnectSkipped(skipped: boolean): void {
  const storage = getLocalStorage();
  if (!storage) {
    return;
  }

  if (skipped) {
    storage.setItem(SKIP_KEY, "1");
    return;
  }

  storage.removeItem(SKIP_KEY);
}

export function markKiteConnectAttempt(): void {
  getSessionStorage()?.setItem(PENDING_KEY, "1");
}

export function consumeKiteConnectAttempt(): boolean {
  const storage = getSessionStorage();
  if (!storage) {
    return false;
  }

  const pending = storage.getItem(PENDING_KEY) === "1";
  storage.removeItem(PENDING_KEY);
  return pending;
}

export function runBrokerConnectPreferenceSelfCheck(): void {
  const store = new Map<string, string>();
  const session = new Map<string, string>();
  const originalLocal = globalThis.localStorage;
  const originalSession = globalThis.sessionStorage;

  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    value: {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => {
        store.set(key, value);
      },
      removeItem: (key: string) => {
        store.delete(key);
      },
    },
  });

  Object.defineProperty(globalThis, "sessionStorage", {
    configurable: true,
    value: {
      getItem: (key: string) => session.get(key) ?? null,
      setItem: (key: string, value: string) => {
        session.set(key, value);
      },
      removeItem: (key: string) => {
        session.delete(key);
      },
    },
  });

  try {
    writeBrokerConnectSkipped(true);
    if (!readBrokerConnectSkipped()) {
      throw new Error("Broker connect preference self-check failed: skip write");
    }

    markKiteConnectAttempt();
    if (!consumeKiteConnectAttempt() || consumeKiteConnectAttempt()) {
      throw new Error("Broker connect preference self-check failed: pending");
    }

    writeBrokerConnectSkipped(false);
    if (readBrokerConnectSkipped()) {
      throw new Error("Broker connect preference self-check failed: clear skip");
    }
  } finally {
    Object.defineProperty(globalThis, "localStorage", {
      configurable: true,
      value: originalLocal,
    });
    Object.defineProperty(globalThis, "sessionStorage", {
      configurable: true,
      value: originalSession,
    });
  }
}
