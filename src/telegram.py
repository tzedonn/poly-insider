from __future__ import annotations

import asyncio
import logging
import time
from collections import deque

import httpx

from src.config import settings
from src.models import WalletAnalysis

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org"
_PAUSE_DURATION = 3600
_DAY_SECONDS = 86400

_HELP_TEXT = (
    "<b>Available commands:</b>\n\n"
    "/check — 24h funnel stats (streamed → filtered → alerts)\n"
    "/pause — Pause alerts for 1 hour\n"
    "/resume — Resume alerts\n"
    "/help — Show this message"
)


def _format_alert(analysis: WalletAnalysis) -> str:
    addr = analysis.address
    short_addr = f"{addr[:6]}...{addr[-4:]}"

    profile_line = analysis.profile_name or "Anonymous (no profile)"

    age_line = "unknown"
    if analysis.first_seen is not None:
        age_days = (time.time() - analysis.first_seen) / 86400
        age_line = f"{age_days:.1f} days old"

    position_block = ""
    if analysis.positions:
        top = max(analysis.positions, key=lambda p: p.initialValue)
        direction = f"{top.outcome} at ${top.curPrice:.2f}"
        position_block = (
            f"\n<b>Top Position:</b>\n"
            f'  Market: "{top.title}"\n'
            f"  Direction: {direction}\n"
            f"  Size: ${top.initialValue:,.0f}\n"
            f"  https://polymarket.com/event/{top.eventSlug}"
        )

    return (
        f"<b>INSIDER ALERT</b>\n\n"
        f"Wallet: <code>{short_addr}</code>\n"
        f"Profile: {profile_line}\n"
        f"Wallet age: {age_line}"
        f"{position_block}\n\n"
        f"https://polymarket.com/profile/{addr}"
    )


class TelegramNotifier:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=10.0)
        self._bot_base = f"{_TELEGRAM_API}/bot{settings.telegram_bot_token}"
        self._url = f"{self._bot_base}/sendMessage"
        self._paused_until: float | None = None
        self._start_time: float = time.time()
        self._last_heartbeat_time: float = time.time()
        self.trades_streamed: int = 0
        self.wallets_streamed: int = 0
        self.wallets_after_exclusions: int = 0
        self.wallets_above_threshold: int = 0
        self.alerts_fired: int = 0
        self._trades_streamed_log: deque[float] = deque()
        self._streamed_log: deque[float] = deque()
        self._after_exclusions_log: deque[float] = deque()
        self._above_threshold_log: deque[float] = deque()
        self._alerts_log: deque[float] = deque()

    @property
    def is_paused(self) -> bool:
        if self._paused_until is None:
            return False
        if time.time() >= self._paused_until:
            self._paused_until = None
            return False
        return True

    async def close(self) -> None:
        await self._client.aclose()

    async def send_alert(self, analysis: WalletAnalysis) -> bool:
        if self.is_paused:
            logger.debug("Alert suppressed (paused) for %s", analysis.address)
            return False

        text = _format_alert(analysis)
        payload = {
            "chat_id": settings.telegram_chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        try:
            resp = await self._client.post(self._url, json=payload)
            resp.raise_for_status()
            self.alerts_fired += 1
            self._alerts_log.append(time.time())
            logger.info("Alert sent for %s", analysis.address)
            return True
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            logger.error("Failed to send Telegram alert: %s", exc)
            return False

    def record_funnel(
        self, trades_streamed: int, streamed: int, after_exclusions: int,
        above_threshold: int,
    ) -> None:
        now = time.time()
        self.trades_streamed += trades_streamed
        self.wallets_streamed += streamed
        self.wallets_after_exclusions += after_exclusions
        self.wallets_above_threshold += above_threshold
        for _ in range(trades_streamed):
            self._trades_streamed_log.append(now)
        for _ in range(streamed):
            self._streamed_log.append(now)
        for _ in range(after_exclusions):
            self._after_exclusions_log.append(now)
        for _ in range(above_threshold):
            self._above_threshold_log.append(now)

    def _count_24h(self, log: deque[float]) -> int:
        cutoff = time.time() - _DAY_SECONDS
        while log and log[0] < cutoff:
            log.popleft()
        return len(log)

    @staticmethod
    def _fmt_elapsed(seconds: float) -> str:
        mins = int(seconds // 60)
        if mins < 60:
            return f"{mins}min"
        hours, mins = divmod(mins, 60)
        return f"{hours}h {mins}min"

    @staticmethod
    def _per_hr(count: int, seconds: float) -> str:
        if seconds < 60:
            return "—"
        rate = count / (seconds / 3600)
        return f"{rate:,.0f}/hr"

    async def listen_for_commands(self) -> None:
        url = f"{self._bot_base}/getUpdates"
        offset = 0
        target_chat = int(settings.telegram_chat_id)

        while True:
            try:
                resp = await self._client.get(
                    url,
                    params={"offset": offset, "timeout": 30},
                    timeout=40.0,
                )
                resp.raise_for_status()
                updates = resp.json().get("result", [])
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                logger.error("getUpdates failed: %s", exc)
                await asyncio.sleep(5)
                continue
            except Exception:
                logger.exception("Unexpected error in command listener")
                await asyncio.sleep(5)
                continue

            for update in updates:
                offset = update["update_id"] + 1
                msg = update.get("message")
                if not msg:
                    continue
                chat_id = msg.get("chat", {}).get("id")
                if chat_id != target_chat:
                    continue
                text = (msg.get("text") or "").strip()
                if text == "/pause":
                    self._paused_until = time.time() + _PAUSE_DURATION
                    await self._reply(chat_id, "Alerts paused for 1 hour.")
                elif text == "/resume":
                    self._paused_until = None
                    await self._reply(chat_id, "Alerts resumed.")
                elif text == "/check":
                    trades = self._count_24h(self._trades_streamed_log)
                    streamed = self._count_24h(self._streamed_log)
                    after_ex = self._count_24h(self._after_exclusions_log)
                    above_thr = self._count_24h(self._above_threshold_log)
                    alerts = self._count_24h(self._alerts_log)
                    status = "paused" if self.is_paused else "active"
                    elapsed = min(time.time() - self._start_time, _DAY_SECONDS)
                    el_str = self._fmt_elapsed(elapsed)
                    await self._reply(
                        chat_id,
                        f"Last 24h funnel ({el_str}):\n"
                        f"Trades streamed: {trades} ({self._per_hr(trades, elapsed)})\n"
                        f"Wallets streamed: {streamed} ({self._per_hr(streamed, elapsed)})\n"
                        f"After exclusions: {after_ex}\n"
                        f"Trades > $1,000: {above_thr}\n"
                        f"Insider alerts: {alerts}\n"
                        f"Status: {status}",
                    )
                elif text == "/help":
                    await self._reply_html(chat_id, _HELP_TEXT)

    async def send_heartbeat(self) -> None:
        now = time.time()
        elapsed = now - self._last_heartbeat_time
        self._last_heartbeat_time = now
        trades = self.trades_streamed
        streamed = self.wallets_streamed
        after_ex = self.wallets_after_exclusions
        above_thr = self.wallets_above_threshold
        alerts = self.alerts_fired
        self.trades_streamed = 0
        self.wallets_streamed = 0
        self.wallets_after_exclusions = 0
        self.wallets_above_threshold = 0
        self.alerts_fired = 0

        el_str = self._fmt_elapsed(elapsed)
        text = (
            f"Insidor bot is alive.\n\n"
            f"Funnel (since last heartbeat, {el_str}):\n"
            f"Trades streamed: {trades} ({self._per_hr(trades, elapsed)})\n"
            f"Wallets streamed: {streamed} ({self._per_hr(streamed, elapsed)})\n"
            f"After exclusions: {after_ex}\n"
            f"Trades > $1,000: {above_thr}\n"
            f"Insider alerts: {alerts}\n\n"
            f"Active filters:\n"
            f"• Min trade size: ${settings.min_trade_size_usd:,.0f}\n"
            f"• Max markets traded: 10\n"
            f"• Max wallet age: 30 days"
        )
        payload = {
            "chat_id": settings.telegram_chat_id,
            "text": text,
        }
        try:
            resp = await self._client.post(self._url, json=payload)
            resp.raise_for_status()
            logger.info("Heartbeat sent")
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            logger.error("Failed to send heartbeat: %s", exc)

    async def _reply(self, chat_id: int, text: str) -> None:
        try:
            await self._client.post(
                self._url,
                json={"chat_id": chat_id, "text": text},
            )
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            logger.error("Failed to send command reply: %s", exc)

    async def _reply_html(self, chat_id: int, text: str) -> None:
        try:
            await self._client.post(
                self._url,
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            )
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            logger.error("Failed to send command reply: %s", exc)
