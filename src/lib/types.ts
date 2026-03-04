export interface Trade {
  id: string;
  taker_order_id: string;
  market: string;
  asset_id: string;
  side: "BUY" | "SELL";
  size: string;
  fee_rate_bps: string;
  price: string;
  status: string;
  match_time: string;
  last_update: string;
  outcome: string;
  bucket_index: string;
  owner: string;
  transaction_hash: string;
  maker_address: string;
  trader: string;
  event_slug: string;
  market_slug: string;
  title: string;
  icon: string;
}

export type Category = "sports" | "crypto" | "updown" | "other";

export interface Filters {
  categories: Record<Category, boolean>;
  minAmount: number;
}
