from __future__ import annotations

import asyncio
import logging

from src.api_client import PolymarketClient
from src.models import Position, WalletAnalysis
from src.signals import is_fresh_wallet

logger = logging.getLogger(__name__)


class WalletAnalyzer:
    def __init__(self, client: PolymarketClient) -> None:
        self._client = client

    async def analyze(
        self,
        address: str,
        name: str = "",
        bio: str = "",
        profile_image: str = "",
    ) -> WalletAnalysis | None:
        market_count = 0
        try:
            market_count = await self._client.get_market_count(address)
        except Exception:
            logger.warning("Failed to fetch market count for %s", address)

        if market_count > 10:
            logger.info("Skipping %s — %d markets traded", address[:10], market_count)
            return None

        positions: list[Position] = []
        first_seen: int | None = None

        results = await asyncio.gather(
            self._client.get_positions(address),
            self._client.get_first_trade_timestamp(address),
            return_exceptions=True,
        )

        if isinstance(results[0], list):
            positions = results[0]
        else:
            logger.warning("Failed to fetch positions for %s: %s", address, results[0])

        if isinstance(results[1], int):
            first_seen = results[1]
        elif results[1] is not None and not isinstance(results[1], BaseException):
            first_seen = results[1]
        else:
            logger.warning("Failed to fetch first trade for %s: %s", address, results[1])

        if not is_fresh_wallet(first_seen):
            logger.info("Skipping %s — wallet older than 30 days", address[:10])
            return None

        return WalletAnalysis(
            address=address,
            positions=positions,
            market_count=market_count,
            first_seen=first_seen,
            profile_name=name,
            profile_bio=bio,
            profile_image=profile_image,
        )
