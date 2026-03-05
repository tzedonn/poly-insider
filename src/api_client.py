from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from src.config import settings
from src.models import Position, Trade, TradedResponse

logger = logging.getLogger(__name__)

_RETRY_ATTEMPTS = 3
_RETRY_BACKOFF = [0.5, 1.0, 2.0]


class PolymarketClient:
    def __init__(self) -> None:
        self._data = httpx.AsyncClient(
            base_url=settings.data_api_base,
            timeout=15.0,
        )
        self._gamma = httpx.AsyncClient(
            base_url=settings.gamma_api_base,
            timeout=15.0,
        )

    async def close(self) -> None:
        await self._data.aclose()
        await self._gamma.aclose()

    async def _get(
        self, client: httpx.AsyncClient, path: str, params: dict[str, Any] | None = None
    ) -> Any:
        last_exc: Exception | None = None
        for attempt, backoff in enumerate(_RETRY_BACKOFF):
            try:
                resp = await client.get(path, params=params)
                resp.raise_for_status()
                return resp.json()
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                last_exc = exc
                logger.warning("API %s attempt %d failed: %s", path, attempt + 1, exc)
                if attempt < _RETRY_ATTEMPTS - 1:
                    import asyncio
                    await asyncio.sleep(backoff)
        raise last_exc  # type: ignore[misc]

    async def get_recent_trades(self, limit: int = 100) -> list[Trade]:
        data = await self._get(
            self._data, "/trades",
            params={"limit": limit, "_": int(time.time() * 1000)},
        )
        return [Trade.model_validate(t) for t in data]

    async def get_positions(self, address: str) -> list[Position]:
        data = await self._get(self._data, "/positions", params={"user": address})
        return [Position.model_validate(p) for p in data]

    async def get_market_count(self, address: str) -> int:
        data = await self._get(self._data, "/traded", params={"user": address})
        resp = TradedResponse.model_validate(data)
        return resp.traded

    async def get_first_trade_timestamp(self, address: str) -> int | None:
        data = await self._get(
            self._data,
            "/trades",
            params={"user": address, "limit": 1, "sortBy": "timestamp", "sortOrder": "asc"},
        )
        if data and isinstance(data, list) and len(data) > 0:
            return int(data[0].get("timestamp", 0)) or None
        return None

    async def get_event(self, event_slug: str) -> dict[str, Any]:
        return await self._get(self._gamma, f"/events/{event_slug}")
