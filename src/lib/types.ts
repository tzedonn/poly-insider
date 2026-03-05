export interface Trade {
  proxyWallet: string;
  side: "BUY" | "SELL";
  asset: string;
  conditionId: string;
  size: number;
  price: number;
  timestamp: number;
  title: string;
  slug: string;
  icon: string;
  eventSlug: string;
  outcome: string;
  outcomeIndex: number;
  name: string;
  pseudonym: string;
  bio: string;
  profileImage: string;
  profileImageOptimized: string;
  transactionHash: string;
}

export type Category =
  | "politics"
  | "sports"
  | "crypto"
  | "iran"
  | "finance"
  | "geopolitics"
  | "culture"
  | "economy"
  | "climate"
  | "updown"
  | "other";

export interface Filters {
  categories: Record<Category, boolean>;
  minAmount: number;
}
