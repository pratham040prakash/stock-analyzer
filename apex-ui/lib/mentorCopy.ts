import type { Decision, Insight, Portfolio } from "@/types/portfolio";

export type PortfolioMood = "stable" | "high_risk" | "loss";
export type UrgencyLevel = "none" | "moderate" | "high";
export type MentorTone = "calm" | "concerned" | "encouraging" | "observational";

export function getDailyMentorTone(): MentorTone {
  const day = new Date().getDate();
  const tones: MentorTone[] = [
    "calm",
    "concerned",
    "encouraging",
    "observational",
  ];
  return tones[day % tones.length];
}

export function getMentorGreeting(name = "Prakash"): string {
  const hour = new Date().getHours();

  if (hour < 12) return `Good morning, ${name}.`;
  if (hour < 17) return `Good afternoon, ${name}.`;
  return "Let's look at your portfolio today.";
}

export function getPortfolioMood(
  concentration: number,
  insights: Insight[],
): PortfolioMood {
  const inLoss = insights.some(
    (i) => i.type === "performance" && i.message.includes("down"),
  );

  if (inLoss) return "loss";
  if (concentration > 60 || insights.some((i) => i.severity === "high")) {
    return "high_risk";
  }
  return "stable";
}

export function getUrgencyLevel(
  mood: PortfolioMood,
  concentration: number,
  insights: Insight[],
): UrgencyLevel {
  if (mood === "loss" || mood === "high_risk") return "high";
  if (
    concentration > 40 ||
    insights.some((i) => i.severity === "medium" || i.severity === "high")
  ) {
    return "moderate";
  }
  return "none";
}

export function getTodayMattersSignal(
  urgency: UrgencyLevel,
  useSharp = false,
): string {
  if (useSharp && urgency === "high") {
    return "I wouldn't ignore this — it's worth your attention today.";
  }

  switch (urgency) {
    case "none":
      return "Nothing critical today — but let's stay aware.";
    case "moderate":
      return "There's one thing I'd keep an eye on today.";
    case "high":
      return "I'd pay attention today — something needs your focus.";
  }
}

export type DeepInsight = {
  focus: string | null;
  ifYouDoNothing: string | null;
  optionalAction: string | null;
  contrast: string | null;
};

function getTopHoldings(portfolio: Portfolio) {
  return [...portfolio.holdings].sort(
    (a, b) => b.quantity * b.currentPrice - a.quantity * a.currentPrice,
  );
}

function portfolioPerformingWell(insights: Insight[]): boolean {
  return (
    insights.some((i) => i.message.includes("up")) ||
    !insights.some((i) => i.type === "performance" && i.message.includes("down"))
  );
}

export function shouldUseSharpMoment(
  mood: PortfolioMood,
  concentration: number,
): boolean {
  return mood === "high_risk" && concentration > 65;
}

export function getDeepInsight(
  portfolio: Portfolio,
  mood: PortfolioMood,
  urgency: UrgencyLevel,
  concentration: number,
  insights: Insight[],
): DeepInsight {
  if (urgency === "none" || portfolio.holdings.length === 0) {
    return {
      focus: null,
      ifYouDoNothing: null,
      optionalAction: null,
      contrast: null,
    };
  }

  const top = getTopHoldings(portfolio)[0];
  const second = getTopHoldings(portfolio)[1];
  const inLoss = mood === "loss";
  const concentrated = concentration > 40;

  let focus: string | null = null;

  if (inLoss) {
    const weakest = [...portfolio.holdings].sort(
      (a, b) =>
        (a.currentPrice - a.avgPrice) / a.avgPrice -
        (b.currentPrice - b.avgPrice) / b.avgPrice,
    )[0];
    focus = weakest
      ? `Focus: ${weakest.symbol} has been pulling your portfolio down — that's where I'd start looking.`
      : "Focus: Your portfolio has been under pressure — a calm review of your weakest spots would help.";
  } else if (concentrated && top) {
    focus = second
      ? `Focus: Your exposure to ${top.symbol} and ${second.symbol} is higher than usual compared to your other holdings.`
      : `Focus: Your exposure to ${top.symbol} is higher than usual compared to your other holdings.`;
  } else if (urgency === "moderate") {
    focus = top
      ? `Focus: ${top.symbol} stands out in your portfolio — worth a closer look today.`
      : null;
  }

  let ifYouDoNothing: string | null = null;

  if (concentrated) {
    ifYouDoNothing =
      "If left as is, your portfolio could become overly dependent on a single stock.";
  } else if (inLoss) {
    ifYouDoNothing =
      "If left as is, small losses can quietly turn into harder decisions later.";
  }

  let optionalAction: string | null = null;

  if (concentrated) {
    optionalAction =
      "If you were to act, you might consider gradually balancing this over time — no urgency.";
  } else if (inLoss) {
    optionalAction =
      "If you were to act, revisiting your weakest positions calmly might help — no rush.";
  } else if (urgency === "moderate") {
    optionalAction =
      "If you were to act, a light rebalance over time could help — only if it feels right to you.";
  }

  let contrast: string | null = null;

  if (concentrated && portfolioPerformingWell(insights) && !inLoss) {
    contrast =
      "Even though your overall returns look stable, this concentration is quietly increasing risk.";
  } else if (inLoss && concentrated) {
    contrast =
      "Even though only part of your portfolio is struggling, concentration can amplify the impact.";
  }

  return { focus, ifYouDoNothing, optionalAction, contrast };
}

export function getMentorLine(
  mood: PortfolioMood,
  tone: MentorTone = getDailyMentorTone(),
): string {
  const lines: Record<MentorTone, Record<PortfolioMood, string>> = {
    calm: {
      stable:
        "Nothing urgent — but there's something you should be aware of.",
      high_risk:
        "I'm slightly concerned about your portfolio balance.",
      loss: "Let's slow down — your portfolio needs attention.",
    },
    concerned: {
      stable:
        "Things look steady — still worth a quiet check-in today.",
      high_risk:
        "I'm slightly concerned about your portfolio balance.",
      loss: "Let's slow down — your portfolio needs attention.",
    },
    encouraging: {
      stable:
        "You're in a good rhythm — let's keep that awareness going.",
      high_risk:
        "A little imbalance is normal — catching it early is what matters.",
      loss: "Tough stretches pass — reviewing calmly is how you stay ahead.",
    },
    observational: {
      stable:
        "Nothing urgent — but there's something you should be aware of.",
      high_risk:
        "A few patterns stand out — worth noticing before they grow.",
      loss: "The picture has shifted — let's look at it without rushing.",
    },
  };

  return lines[tone][mood];
}

export function getToneFlavor(tone: MentorTone = getDailyMentorTone()): string {
  switch (tone) {
    case "calm":
      return "No rush — we have room to think this through.";
    case "concerned":
      return "I want to make sure we don't miss what's shifting here.";
    case "encouraging":
      return "You're showing up — that already puts you ahead of most.";
    case "observational":
      return "Let's notice the patterns before we decide anything.";
  }
}

export function getPersonalReflection(): string {
  return "This is something many investors overlook — you're already ahead by noticing it.";
}

export function getProgressLine(isRevisit: boolean): string | null {
  if (!isRevisit) return null;
  return "You're building a good habit — reviewing consistently matters more than timing the market.";
}

export function getSessionClosing(
  tone: MentorTone = getDailyMentorTone(),
): string {
  switch (tone) {
    case "calm":
      return "That's all for today — no need to overthink. Come back tomorrow and we'll take the next step.";
    case "concerned":
      return "That's enough for today — rest easy knowing we've flagged what matters. Come back tomorrow and we'll continue.";
    case "encouraging":
      return "You showed up today — that counts. Come back tomorrow and we'll keep building on this.";
    case "observational":
      return "That's all for today — sit with what you noticed. Come back tomorrow and we'll see what's changed.";
  }
}

export function getTodaysFocus(
  mood: PortfolioMood,
  concentration: number,
): string {
  if (mood === "loss") {
    return "Your portfolio needs a thoughtful review — that's where I'd focus.";
  }
  if (concentration > 40) {
    return "Your portfolio is slightly concentrated — that's where I'd focus.";
  }
  return "Staying balanced across your holdings — that's a good place to start.";
}

export function humanizeStance(stance: Decision["stance"]): string {
  switch (stance) {
    case "WAIT":
      return "I'd stay patient here.";
    case "SELL":
      return "I'd consider reducing exposure.";
    case "BUY":
      return "This might be worth adding carefully.";
    case "HOLD":
      return "I'd hold steady for now.";
  }
}

export function getWhyThisMatters(
  mood: PortfolioMood,
  concentration: number,
): string {
  if (mood === "loss") {
    return "When a portfolio is under pressure, rushed decisions often make things worse. Pausing to review helps you stay in control.";
  }
  if (concentration > 40) {
    return "Overexposure to a few stocks can quietly increase risk even if returns look fine.";
  }
  return "Staying aware of how your portfolio is shaped helps you act with intention, not impulse.";
}

export function humanizeStockGuidance(
  decision: "BUY" | "SELL" | "HOLD",
): string {
  switch (decision) {
    case "BUY":
      return "This might be worth adding carefully.";
    case "SELL":
      return "I'd consider reducing exposure here.";
    case "HOLD":
      return "I'd stay patient with this one.";
  }
}

export function softenInsightMessage(message: string): string {
  return message
    .replace(/make up \d+%/, "carry a lot of weight in your portfolio")
    .replace(/Portfolio is down ([-\d.]+)%/, "Your portfolio has been under some pressure lately")
    .replace(/Portfolio is up ([\d.]+)%/, "Your portfolio has been doing well lately")
    .replace(/Top holdings \(([^)]+)\)/, "A few positions ($1) stand out")
    .replace(/ is your weakest performer right now/, " has been the toughest spot lately");
}

export function humanizeConfidence(
  confidence: "low" | "medium" | "high",
): string {
  if (confidence === "high") return "I feel fairly confident about this read.";
  if (confidence === "medium") return "This is worth a closer look on your end.";
  return "The picture here is still forming.";
}

export function getCapacityIntro(): string {
  return "I'm trying to understand your full picture — not just your portfolio.";
}

export function getComfortableInvestLine(monthlySurplus: number): string {
  if (monthlySurplus <= 0) {
    return "Right now, your expenses look close to or above your income — investing may need a lighter touch until there's breathing room.";
  }
  const formatted = formatRupeeAmount(monthlySurplus);
  return `Based on your current lifestyle, you could comfortably invest around ${formatted} per month.`;
}

export function getPortfolioCapacityLine(
  level: "low" | "high" | "neutral",
): string {
  if (level === "low") {
    return "You're investing less than what you could — there's room to grow.";
  }
  if (level === "high") {
    return "You're already allocating well — consistency will matter more now.";
  }
  return "Once your expenses settle, small consistent steps can make a real difference.";
}

function formatRupeeAmount(amount: number): string {
  const rounded = Math.round(amount / 1000) * 1000;
  return `₹${rounded.toLocaleString("en-IN")}`;
}
