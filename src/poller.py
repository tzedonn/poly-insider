from __future__ import annotations

import asyncio
import logging
from collections import deque

from src.analyzer import WalletAnalyzer
from src.api_client import PolymarketClient
from src.cache import WalletCache
from src.config import settings
from src.models import Trade
from src.telegram import TelegramNotifier

logger = logging.getLogger(__name__)

_MAX_SEEN_HASHES = 10_000
_MAX_CONCURRENT_WALLETS = 5
_EXCLUDED_SLUG_KEYWORDS = (
    "bitcoin", "btc-", "ethereum", "eth-", "solana", "sol-", "xrp",
    "nfl", "nba", "mlb", "nhl", "ufc", "mma", "boxing", "tennis",
    "golf", "pga", "soccer", "football", "basketball", "baseball",
    "hockey", "f1-", "formula-1", "nascar", "cricket", "rugby",
    "premier-league", "champions-league", "world-cup", "super-bowl",
    "stanley-cup", "world-series",
    "presidential-nominee", "the-masters", "crint-",
)


class TradePoller:
    def __init__(
        self,
        client: PolymarketClient,
        analyzer: WalletAnalyzer,
        notifier: TelegramNotifier,
        cache: WalletCache,
    ) -> None:
        self._client = client
        self._analyzer = analyzer
        self._notifier = notifier
        self._cache = cache
        self._seen_hashes: deque[str] = deque(maxlen=_MAX_SEEN_HASHES)
        self._seen_set: set[str] = set()

    def _dedup_hash(self, tx_hash: str) -> bool:
        if tx_hash in self._seen_set:
            return True
        self._seen_set.add(tx_hash)
        self._seen_hashes.append(tx_hash)
        if len(self._seen_set) > _MAX_SEEN_HASHES:
            oldest = self._seen_hashes[0]
            self._seen_set.discard(oldest)
        return False

    def _extract_wallets(
        self, trades: list[Trade],
    ) -> tuple[dict[str, Trade], int, int, int]:
        trades_seen = 0
        all_wallets: set[str] = set()
        after_exclusions: set[str] = set()
        wallets: dict[str, Trade] = {}
        for trade in trades:
            if self._dedup_hash(trade.transactionHash):
                continue
            trades_seen += 1
            all_wallets.add(trade.proxyWallet)
            if any(kw in trade.slug for kw in _EXCLUDED_SLUG_KEYWORDS):
                continue
            after_exclusions.add(trade.proxyWallet)
            usdc = trade.usdc_value
            if usdc < settings.min_trade_size_usd:
                continue
            addr = trade.proxyWallet
            if addr not in wallets or usdc > wallets[addr].usdc_value:
                wallets[addr] = trade
        return wallets, len(all_wallets), len(after_exclusions), trades_seen

    async def _analyze_wallet(self, address: str, trade: Trade) -> None:
        if self._cache.seen(address):
            return

        self._cache.mark(address)

        try:
            analysis = await self._analyzer.analyze(
                address=address,
                name=trade.name,
                bio=trade.bio,
                profile_image=trade.profileImage,
            )
        except Exception:
            logger.exception("Analysis failed for %s", address)
            return

        if analysis is None:
            return

        await self._notifier.send_alert(analysis)

    async def poll_once(self) -> int:
        try:
            trades = await self._client.get_recent_trades()
        except Exception:
            logger.exception("Failed to fetch trades")
            return 0

        wallets, streamed, after_exclusions, trades_seen = self._extract_wallets(trades)
        self._notifier.record_funnel(trades_seen, streamed, after_exclusions, len(wallets))
        if not wallets:
            return 0

        logger.info("Analyzing %d wallet(s)", len(wallets))

        sem = asyncio.Semaphore(_MAX_CONCURRENT_WALLETS)

        async def bounded(addr: str, trade: Trade) -> None:
            async with sem:
                await self._analyze_wallet(addr, trade)

        await asyncio.gather(*(bounded(addr, t) for addr, t in wallets.items()))
        return len(wallets)

    async def run(self) -> None:
        logger.info(
            "Poller started — interval=%ds, min_trade=$%s",
            settings.poll_interval_seconds,
            f"{settings.min_trade_size_usd:,.0f}",
        )
        while True:
            analyzed = await self.poll_once()
            if analyzed:
                logger.info("Poll cycle complete — %d wallet(s) analyzed", analyzed)
            await asyncio.sleep(settings.poll_interval_seconds)
