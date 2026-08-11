import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { existsSync } from "node:fs";
import { join } from "node:path";

const execFileAsync = promisify(execFile);

export type AlphaAiBridgePayload = {
  symbol: string;
  name?: string;
  recommendation?: string;
  overall_score?: number;
  investment_grade_stars?: number;
  confidence_pct?: number | null;
  risk_level?: string;
  buy_decision?: string;
  buy_decision_why?: string;
  business_overview?: string;
  valuation_verdict?: string;
  technical_summary?: string;
  red_flags?: string[];
  data_gaps?: string[];
};

function resolveAnalyzerRoot(): string | null {
  const candidates = [
    process.env.ANALYZER_REPO_ROOT,
    join(process.cwd(), ".."),
    join(process.cwd()),
  ].filter(Boolean) as string[];

  for (const root of candidates) {
    if (existsSync(join(root, "analyzer", "alpha_ai_report.py"))) {
      return root;
    }
  }

  return null;
}

export async function fetchAlphaAiSummary(
  symbol: string,
): Promise<AlphaAiBridgePayload | null> {
  const remoteUrl = process.env.ALPHA_AI_SERVICE_URL?.trim();

  if (remoteUrl) {
    try {
      const response = await fetch(
        `${remoteUrl.replace(/\/$/, "")}/summary?symbol=${encodeURIComponent(symbol.trim().toUpperCase())}`,
        {
          headers: { Accept: "application/json" },
          signal: AbortSignal.timeout(120_000),
        },
      );

      if (response.ok) {
        const parsed = (await response.json()) as AlphaAiBridgePayload;

        if (parsed?.symbol) {
          return parsed;
        }
      }
    } catch {
      // Fall through to local Python bridge.
    }
  }

  const root = resolveAnalyzerRoot();

  if (!root) {
    return null;
  }

  const script = join(root, "apex-ui/scripts/alpha_ai_json.py");
  const python = process.env.ANALYZER_PYTHON ?? "python3";

  try {
    const { stdout } = await execFileAsync(
      python,
      [script, symbol.trim().toUpperCase()],
      {
        cwd: root,
        timeout: 120_000,
        maxBuffer: 4 * 1024 * 1024,
        env: { ...process.env, PYTHONPATH: root },
      },
    );

    const parsed = JSON.parse(stdout) as AlphaAiBridgePayload;

    if (!parsed?.symbol) {
      return null;
    }

    return parsed;
  } catch {
    return null;
  }
}

export function runAlphaAiBridgeSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Alpha AI bridge self-check failed: ${message}`);
    }
  };

  assert(typeof fetchAlphaAiSummary === "function", "Bridge export missing");
}
