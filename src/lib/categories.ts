import type { Category, Trade } from "./types";

const KEYWORD_MAP: [Category, string[]][] = [
  ["updown", ["updown", "up-down", "up-or-down"]],
  [
    "sports",
    [
      "nfl", "nba", "mlb", "nhl", "ufc", "mma", "boxing", "tennis", "golf",
      "pga", "soccer", "football", "basketball", "baseball", "hockey",
      "f1-", "formula-1", "nascar", "cricket", "rugby",
      "premier-league", "champions-league", "world-cup",
      "super-bowl", "stanley-cup", "world-series",
    ],
  ],
  [
    "crypto",
    [
      "bitcoin", "btc-", "ethereum", "eth-", "solana", "sol-",
      "xrp", "dogecoin", "doge-", "crypto",
    ],
  ],
  ["iran", ["iran"]],
  [
    "finance",
    [
      "stock", "stocks", "nasdaq", "s-p-500", "sp500", "dow-jones",
      "interest-rate", "fed-", "federal-reserve", "treasury",
    ],
  ],
  [
    "geopolitics",
    [
      "war", "nato", "china", "russia", "ukraine", "taiwan",
      "israel", "palestine", "tariff", "sanction",
    ],
  ],
  [
    "culture",
    [
      "oscar", "grammy", "emmy", "tiktok", "youtube", "celebrity",
      "movie", "film", "tv-show", "music", "kanye", "drake",
      "taylor-swift", "elon-musk", "tweet",
    ],
  ],
  [
    "economy",
    [
      "gdp", "inflation", "unemployment", "recession",
      "jobs-report", "cpi-", "economic",
    ],
  ],
  [
    "climate",
    [
      "climate", "weather", "hurricane", "earthquake", "temperature",
      "nasa", "spacex", "ai-safety",
    ],
  ],
  [
    "politics",
    [
      "trump", "biden", "election", "congress", "senate",
      "democrat", "republican", "governor", "poll-", "approval",
    ],
  ],
];

export function classifyTrade(trade: Trade): Category {
  const slug = (trade.slug || trade.eventSlug || "").toLowerCase();

  for (const [category, keywords] of KEYWORD_MAP) {
    if (keywords.some((kw) => slug.includes(kw))) return category;
  }

  return "other";
}

export const CATEGORY_LABELS: Record<Category, string> = {
  politics: "Politics",
  sports: "Sports",
  crypto: "Crypto",
  iran: "Iran",
  finance: "Finance",
  geopolitics: "Geopolitics",
  culture: "Culture",
  economy: "Economy",
  climate: "Climate & Science",
  updown: "Up/Down",
  other: "Other",
};

export const VISIBLE_CATEGORIES: Category[] = [
  "politics",
  "sports",
  "crypto",
  "iran",
  "finance",
  "geopolitics",
  "culture",
  "economy",
  "climate",
  "updown",
];

export const DEFAULT_FILTERS: Record<Category, boolean> = {
  politics: true,
  sports: true,
  crypto: true,
  iran: true,
  finance: true,
  geopolitics: true,
  culture: true,
  economy: true,
  climate: true,
  updown: false,
  other: true,
};
