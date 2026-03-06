from __future__ import annotations

import asyncio
import logging

from src.api_client import CHAIN_NAMES, ChainClient, PolymarketClient
from src.models import Position, Trade, WalletAnalysis
from src.signals import is_fresh_wallet

logger = logging.getLogger(__name__)


class WalletAnalyzer:
    def __init__(self, client: PolymarketClient, chain_client: ChainClient) -> None:
        self._client = client
        self._chain = chain_client

    async def analyze(
        self,
        address: str,
        name: str = "",
        bio: str = "",
        profile_image: str = "",
        trigger_trade: Trade | None = None,
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

        usdc_balance = 0.0
        funder_address = ""
        funder_chain = ""
        funding_tx_hash = ""

        enrichment = await asyncio.gather(
            self._chain.get_usdc_balance(address),
            self._chain.get_first_funding_tx(address),
            return_exceptions=True,
        )

        if isinstance(enrichment[0], float):
            usdc_balance = enrichment[0]
        else:
            logger.warning("USDC balance lookup failed for %s: %s", address[:10], enrichment[0])

        funding_result = enrichment[1]
        if isinstance(funding_result, tuple):
            funding_tx_hash, funder_address = funding_result
            try:
                relay = await self._chain.get_relay_sender(funding_tx_hash)
                if relay:
                    funder_address, chain_id = relay
                    funder_chain = CHAIN_NAMES.get(chain_id, f"Chain {chain_id}")
            except Exception:
                logger.warning("Relay lookup failed for %s", funding_tx_hash[:10])
        elif not isinstance(funding_result, BaseException):
            pass
        else:
            logger.warning("Funding tx lookup failed for %s: %s", address[:10], funding_result)

        return WalletAnalysis(
            address=address,
            positions=positions,
            market_count=market_count,
            first_seen=first_seen,
            profile_name=name,
            profile_bio=bio,
            profile_image=profile_image,
            trigger_trade=trigger_trade,
            usdc_balance=usdc_balance,
            funder_address=funder_address,
            funder_chain=funder_chain,
            funding_tx_hash=funding_tx_hash,
        )
