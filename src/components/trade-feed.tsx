"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { classifyTrade, DEFAULT_FILTERS } from "@/lib/categories";
import type { Filters, Trade } from "@/lib/types";
import { FilterBar } from "./filter-bar";
import { TradeRow } from "./trade-row";

const POLL_INTERVAL = 5_000;
const MAX_TRADES = 500;

export function TradeFeed() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [filters, setFilters] = useState<Filters>({
    categories: { ...DEFAULT_FILTERS },
    minAmount: 0,
  });
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");
  const seenHashes = useRef(new Set<string>());

  const fetchTrades = useCallback(async () => {
    try {
      const res = await fetch("/api/trades");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const incoming: Trade[] = await res.json();
      const newTrades = incoming.filter(
        (t) => !seenHashes.current.has(t.transaction_hash),
      );

      if (newTrades.length > 0) {
        for (const t of newTrades) {
          seenHashes.current.add(t.transaction_hash);
        }

        setTrades((prev) => {
          const merged = [...newTrades, ...prev].slice(0, MAX_TRADES);
          return merged;
        });
      }

      setStatus("ok");
    } catch {
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    fetchTrades();
    const id = setInterval(fetchTrades, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [fetchTrades]);

  const filteredTrades = trades.filter((trade) => {
    const category = classifyTrade(trade);
    if (!filters.categories[category]) return false;

    const amount = parseFloat(trade.size) * parseFloat(trade.price);
    if (amount < filters.minAmount) return false;

    return true;
  });

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-4 p-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-zinc-100">
          Polymarket Live Feed
        </h1>
        <div className="flex items-center gap-2">
          {status === "loading" && (
            <span className="text-xs text-zinc-500">Loading...</span>
          )}
          {status === "ok" && (
            <span className="text-xs text-zinc-500">
              {filteredTrades.length} trades
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
        <div className="flex items-center gap-3 border-b border-zinc-800 bg-zinc-900/50 px-3 py-2 text-xs font-medium text-zinc-500">
          <div className="h-8 w-8 shrink-0" />
          <div className="min-w-0 flex-1">Market</div>
          <div className="w-10 shrink-0 text-center">Side</div>
          <div className="w-16 shrink-0 text-right">Outcome</div>
          <div className="w-20 shrink-0 text-right">Amount</div>
          <div className="w-14 shrink-0 text-right">Price</div>
          <div className="w-24 shrink-0 text-right">Trader</div>
          <div className="w-16 shrink-0 text-right">Time</div>
          <div className="w-16 shrink-0 text-center">Cat.</div>
        </div>

        {filteredTrades.length === 0 && status !== "loading" && (
          <div className="py-12 text-center text-zinc-500">
            No trades match your filters.
          </div>
        )}

        {filteredTrades.map((trade) => (
          <TradeRow key={trade.transaction_hash} trade={trade} />
        ))}
      </div>
    </div>
  );
}
