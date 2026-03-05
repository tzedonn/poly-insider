"use client";

import { formatUsd, formatTime } from "@/lib/format";
import type { Trade } from "@/lib/types";

interface TradeRowProps {
  trade: Trade;
}

export function TradeRow({ trade }: TradeRowProps) {
  const amount = trade.size * trade.price;
  const priceInCents = (trade.price * 100).toFixed(1);
  const isBuy = trade.side === "BUY";
  const traderDisplay = trade.pseudonym || trade.proxyWallet.slice(0, 6) + "..." + trade.proxyWallet.slice(-4);

  const eventUrl = trade.eventSlug
    ? `https://polymarket.com/event/${trade.eventSlug}`
    : undefined;

  const polygonscanUrl = trade.transactionHash
    ? `https://polygonscan.com/tx/${trade.transactionHash}`
    : undefined;

  return (
    <div className="flex items-start gap-3 border-b border-zinc-800/60 px-4 py-3 hover:bg-zinc-900/40 transition-colors">
      {trade.icon ? (
        <img
          src={trade.icon}
          alt=""
          className="h-12 w-12 shrink-0 rounded-lg bg-zinc-800 object-cover"
        />
      ) : (
        <div className="h-12 w-12 shrink-0 rounded-lg bg-zinc-800" />
      )}

      <div className="min-w-0 flex-1">
        {eventUrl ? (
          <a
            href={eventUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="block truncate text-sm font-medium text-zinc-100 hover:text-blue-400 transition-colors"
          >
            {trade.title}
          </a>
        ) : (
          <span className="block truncate text-sm font-medium text-zinc-100">
            {trade.title}
          </span>
        )}

        <p className="mt-0.5 text-sm text-zinc-400">
          <span className="text-zinc-300">{traderDisplay}</span>
          {" "}
          <span className={isBuy ? "text-emerald-400" : "text-red-400"}>
            {isBuy ? "bought" : "sold"}
          </span>
          {" "}
          <span className="text-zinc-300">{trade.outcome}</span>
          {" "}at {priceInCents}¢
          {" "}
          <span className="text-zinc-300">({formatUsd(amount)})</span>
        </p>
      </div>

      <div className="flex shrink-0 items-center gap-2 pt-0.5">
        <span className="text-xs text-zinc-500 whitespace-nowrap">
          {formatTime(trade.timestamp)}
        </span>
        {polygonscanUrl && (
          <a
            href={polygonscanUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-zinc-600 hover:text-zinc-400 transition-colors"
            title="View on Polygonscan"
          >
            <svg className="h-3.5 w-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M6 3H3v10h10v-3M9 3h4v4M14 2L7 9" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </a>
        )}
      </div>
    </div>
  );
}
