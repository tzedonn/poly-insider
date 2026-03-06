from __future__ import annotations

import asyncio
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
                    await asyncio.sleep(backoff)
        raise last_exc  # type: ignore[misc]

    async def get_recent_trades(self, limit: int = 1000, pages: int = 3) -> list[Trade]:
        cb = int(time.time() * 1000)
        coros = [
            self._get(
                self._data, "/trades",
                params={"limit": limit, "offset": i * limit, "_": cb},
            )
            for i in range(pages)
        ]
        results = await asyncio.gather(*coros, return_exceptions=True)
        seen: set[str] = set()
        trades: list[Trade] = []
        for data in results:
            if isinstance(data, Exception):
                logger.warning("Trade page fetch failed: %s", data)
                continue
            if not isinstance(data, list):
                continue
            for raw in data:
                tx = raw.get("transactionHash")
                if tx and tx not in seen:
                    seen.add(tx)
                    trades.append(Trade.model_validate(raw))
        return trades

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


_NATIVE_USDC = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
_BRIDGED_USDC_E = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
_USDC_CONTRACTS = {_NATIVE_USDC.lower(), _BRIDGED_USDC_E.lower()}
_ETHERSCAN_V2 = "https://api.etherscan.io/v2/api"
_RELAY_API = "https://api.relay.link"

CHAIN_NAMES: dict[int, str] = {
    1: "Ethereum", 8453: "Base", 42161: "Arbitrum",
    10: "Optimism", 137: "Polygon", 43114: "Avalanche",
}


class ChainClient:
    def __init__(self) -> None:
        self._http = httpx.AsyncClient(timeout=15.0)
        self._etherscan_sem = asyncio.Semaphore(1)

    async def close(self) -> None:
        await self._http.aclose()

    async def _etherscan_get(self, params: dict[str, Any]) -> dict[str, Any]:
        _MAX_RETRIES = 2
        for attempt in range(_MAX_RETRIES + 1):
            async with self._etherscan_sem:
                resp = await self._http.get(_ETHERSCAN_V2, params=params)
                resp.raise_for_status()
                data: dict[str, Any] = resp.json()
                await asyncio.sleep(0.25)

            is_rate_limited = (
                data.get("status") == "0"
                and isinstance(data.get("result"), str)
                and "rate limit" in data["result"].lower()
            )
            if is_rate_limited and attempt < _MAX_RETRIES:
                logger.warning("Etherscan rate-limited (attempt %d), retrying...", attempt + 1)
                await asyncio.sleep(1.0)
                continue
            return data
        return data  # unreachable, satisfies type checker

    async def _etherscan_token_balance(self, contract: str, address: str) -> int:
        if not settings.etherscan_api_key:
            return 0
        data = await self._etherscan_get({
            "chainid": 137, "module": "account", "action": "tokenbalance",
            "contractaddress": contract, "address": address, "tag": "latest",
            "apikey": settings.etherscan_api_key,
        })
        if data.get("status") == "1":
            return int(data.get("result", "0"))
        return 0

    async def get_usdc_balance(self, address: str) -> float:
        native, bridged = await asyncio.gather(
            self._etherscan_token_balance(_NATIVE_USDC, address),
            self._etherscan_token_balance(_BRIDGED_USDC_E, address),
            return_exceptions=True,
        )
        total = 0
        if isinstance(native, int):
            total += native
        else:
            logger.warning("Failed to fetch native USDC balance: %s", native)
        if isinstance(bridged, int):
            total += bridged
        else:
            logger.warning("Failed to fetch bridged USDC.e balance: %s", bridged)
        return total / 1e6

    async def get_first_funding_tx(self, address: str) -> tuple[str, str] | None:
        if not settings.etherscan_api_key:
            return None
        try:
            data = await self._etherscan_get({
                "chainid": 137, "module": "account", "action": "tokentx",
                "address": address,
                "sort": "asc", "page": 1, "offset": 50,
                "apikey": settings.etherscan_api_key,
            })
            if data.get("status") != "1":
                return None
            addr_lower = address.lower()
            for tx in data.get("result", []):
                if (
                    tx.get("contractAddress", "").lower() in _USDC_CONTRACTS
                    and tx.get("to", "").lower() == addr_lower
                ):
                    return (tx["hash"], tx["from"])
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            logger.warning("Etherscan tokentx failed: %s", exc)
        return None

    async def get_relay_sender(self, tx_hash: str) -> tuple[str, int] | None:
        try:
            resp = await self._http.get(
                f"{_RELAY_API}/requests/v2", params={"hash": tx_hash},
            )
            resp.raise_for_status()
            requests = resp.json().get("requests", [])
            if not requests:
                return None
            req = requests[0]
            sender = req.get("user", "")
            in_txs = req.get("data", {}).get("inTxs", [])
            source_chain_id = in_txs[0].get("chainId", 0) if in_txs else 0
            if sender:
                return (sender, int(source_chain_id))
        except (httpx.HTTPStatusError, httpx.TransportError, KeyError, IndexError) as exc:
            logger.warning("Relay lookup failed for %s: %s", tx_hash, exc)
        return None
