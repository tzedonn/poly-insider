"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { classifyTrade, DEFAULT_FILTERS } from "@/lib/categories";
import type { Filters, Trade } from "@/lib/types";
import { FilterBar } from "./filter-bar";
import { TradeRow } from "./trade-row";

const POLL_INTERVAL = 5_000;
const TICK_INTERVAL = 1_000;

export function TradeFeed() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [filters, setFilters] = useState<Filters>({
    categories: { ...DEFAULT_FILTERS },
    minAmount: 0,
  });
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");
  const [tick, setTick] = useState(0);
  const [lastPoll, setLastPoll] = useState<number | null>(null);
  const seenHashes = useRef(new Set<string>());

  const fetchTrades = useCallback(async () => {
    try {
      const res = await fetch(`/api/trades?t=${Date.now()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const json = await res.json();
      const incoming: Trade[] = Array.isArray(json) ? json : [];
      const newTrades = incoming.filter(
        (t) => !seenHashes.current.has(t.transactionHash),
      );

      if (newTrades.length > 0) {
        for (const t of newTrades) {
          seenHashes.current.add(t.transactionHash);
        }

        setTrades((prev) => [...newTrades, ...prev]);
      }

      setLastPoll(Math.floor(Date.now() / 1000));
      setStatus("ok");
    } catch {
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    fetchTrades();
    const pollId = setInterval(fetchTrades, POLL_INTERVAL);
    const tickId = setInterval(() => setTick((t) => t + 1), TICK_INTERVAL);
    return () => {
      clearInterval(pollId);
      clearInterval(tickId);
    };
  }, [fetchTrades]);

  void tick;

  const filteredTrades = trades.filter((trade) => {
    const category = classifyTrade(trade);
    if (!filters.categories[category]) return false;

    const amount = trade.size * trade.price;
    return amount >= filters.minAmount;
  });

  const pollAgo = lastPoll ? Math.floor(Date.now() / 1000) - lastPoll : null;

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-4 p-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-zinc-100">Activity</h1>
        <div className="flex items-center gap-2">
          {status === "loading" && (
            <span className="text-xs text-zinc-500">Loading...</span>
          )}
          {status === "ok" && (
            <span className="text-xs text-zinc-500">
              {filteredTrades.length} trades
              {pollAgo !== null && ` · ${pollAgo}s ago`}
            </span>
          )}
          {status === "error" && (
            <span className="text-xs text-red-400">Connection error</span>
          )}
          <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
        </div>
      </div>

      <FilterBar filters={filters} onFiltersChange={setFilters} />

      <div className="overflow-hidden rounded-lg border border-zinc-800 bg-zinc-950">
        {filteredTrades.length === 0 && status !== "loading" && (
          <div className="py-12 text-center text-sm text-zinc-500">
            No trades match your filters.
          </div>
        )}

        {filteredTrades.map((trade) => (
          <TradeRow key={trade.transactionHash} trade={trade} />
        ))}
      </div>
    </div>
  );
}
