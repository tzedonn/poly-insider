"use client";

import { classifyTrade, CATEGORY_LABELS } from "@/lib/categories";
import { formatUsd, formatTime, truncateAddress } from "@/lib/format";
import type { Trade } from "@/lib/types";

interface TradeRowProps {
  trade: Trade;
}

export function TradeRow({ trade }: TradeRowProps) {
  const amount = parseFloat(trade.size) * parseFloat(trade.price);
  const priceInCents = (parseFloat(trade.price) * 100).toFixed(1);
  const isBuy = trade.side === "BUY";
  const category = classifyTrade(trade);
  const traderDisplay = trade.trader
    ? truncateAddress(trade.trader)
    : truncateAddress(trade.owner);

  const eventUrl = trade.event_slug
    ? `https://polymarket.com/event/${trade.event_slug}`
    : undefined;

  const profileUrl = trade.trader
    ? `https://polymarket.com/profile/${trade.trader}`
    : `https://polymarket.com/profile/${trade.owner}`;

  return (
    <div className="flex items-center gap-3 border-b border-zinc-800 px-3 py-2.5 text-sm hover:bg-zinc-900/50">
      {trade.icon && (
        <img
          src={trade.icon}
          alt=""
          className="h-8 w-8 shrink-0 rounded-full bg-zinc-800"
        />
      )}

      <div className="min-w-0 flex-1">
        {eventUrl ? (
          <a
            href={eventUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="truncate font-medium text-zinc-100 hover:text-indigo-400"
          >
            {trade.title || trade.market}
          </a>
        ) : (
          <span className="truncate font-medium text-zinc-100">
            {trade.title || trade.market}
          </span>
        )}
      </div>

      <span
        className={`shrink-0 rounded px-1.5 py-0.5 text-xs font-bold ${
          isBuy
            ? "bg-emerald-500/20 text-emerald-400"
            : "bg-red-500/20 text-red-400"
        }`}
      >
        {trade.side}
      </span>

      <span className="w-16 shrink-0 text-right text-zinc-300">
        {trade.outcome}
      </span>

      <span className="w-20 shrink-0 text-right font-mono text-zinc-100">
        {formatUsd(amount)}
      </span>

      <span className="w-14 shrink-0 text-right font-mono text-zinc-400">
        {priceInCents}¢
      </span>

      <a
        href={profileUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="w-24 shrink-0 truncate text-right text-zinc-500 hover:text-indigo-400"
      >
        {traderDisplay}
      </a>

      <span className="w-16 shrink-0 text-right text-zinc-500">
        {formatTime(trade.match_time)}
      </span>

      <span className="shrink-0 rounded-full bg-zinc-800 px-2 py-0.5 text-xs text-zinc-400">
        {CATEGORY_LABELS[category]}
      </span>
    </div>
  );
}
