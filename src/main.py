from __future__ import annotations

import asyncio
import logging
import signal
import sys

from src.api_client import ChainClient, PolymarketClient
from src.analyzer import WalletAnalyzer
from src.cache import WalletCache
from src.config import settings
from src.poller import TradePoller
from src.telegram import TelegramNotifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    client = PolymarketClient()
    chain_client = ChainClient()
    analyzer = WalletAnalyzer(client, chain_client)
    notifier = TelegramNotifier()
    cache = WalletCache(ttl_hours=settings.cache_ttl_hours)
    poller = TradePoller(client, analyzer, notifier, cache)

    loop = asyncio.get_running_loop()
    stop = loop.create_future()

    def _shutdown() -> None:
        if not stop.done():
            stop.set_result(None)

    if sys.platform != "win32":
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, _shutdown)

    async def heartbeat_loop() -> None:
        while True:
            await notifier.send_heartbeat()
            await asyncio.sleep(3600)

    logger.info("Insidor starting")

    poller_task = asyncio.create_task(poller.run())
    listener_task = asyncio.create_task(notifier.listen_for_commands())
    heartbeat_task = asyncio.create_task(heartbeat_loop())

    try:
        if sys.platform == "win32":
            await poller_task
        else:
            await stop
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        poller_task.cancel()
        listener_task.cancel()
        heartbeat_task.cancel()
        for task in (poller_task, listener_task, heartbeat_task):
            try:
                await task
            except asyncio.CancelledError:
                pass
        await client.close()
        await chain_client.close()
        await notifier.close()
        logger.info("Insidor stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
