from __future__ import annotations

import time


class WalletCache:
    def __init__(self, ttl_hours: int = 24) -> None:
        self._ttl = ttl_hours * 3600
        self._entries: dict[str, float] = {}

    def seen(self, address: str) -> bool:
        ts = self._entries.get(address)
        if ts is None:
            return False
        if time.time() - ts > self._ttl:
            del self._entries[address]
            return False
        return True

    def mark(self, address: str) -> None:
        self._entries[address] = time.time()

    def cleanup(self) -> int:
        now = time.time()
        expired = [k for k, v in self._entries.items() if now - v > self._ttl]
        for k in expired:
            del self._entries[k]
        return len(expired)
