import type { Category, Trade } from "./types";

const UPDOWN_KEYWORDS = ["updown", "up-down", "up-or-down"];

const SPORTS_KEYWORDS = [
  "nfl", "nba", "mlb", "nhl", "ufc", "mma", "boxing", "tennis", "golf",
  "pga", "soccer", "football", "basketball", "baseball", "hockey",
  "f1-", "formula-1", "nascar", "cricket", "rugby",
  "premier-league", "champions-league", "world-cup",
  "super-bowl", "stanley-cup", "world-series",
];

const CRYPTO_KEYWORDS = [
  "bitcoin", "btc-", "ethereum", "eth-", "solana", "sol-",
  "xrp", "dogecoin", "doge-",
];

function slugMatches(slug: string, keywords: string[]): boolean {
  const lower = slug.toLowerCase();
  return keywords.some((kw) => lower.includes(kw));
}

export function classifyTrade(trade: Trade): Category {
  const slug = trade.market_slug || trade.event_slug || "";

  if (slugMatches(slug, UPDOWN_KEYWORDS)) return "updown";
  if (slugMatches(slug, SPORTS_KEYWORDS)) return "sports";
  if (slugMatches(slug, CRYPTO_KEYWORDS)) return "crypto";
  return "other";
}

export const CATEGORY_LABELS: Record<Category, string> = {
  sports: "Sports",
  crypto: "Crypto",
  updown: "Up/Down",
  other: "Other",
};

export const DEFAULT_FILTERS: Record<Category, boolean> = {
  sports: false,
  crypto: false,
  updown: false,
  other: true,
};
