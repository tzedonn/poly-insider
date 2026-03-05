from __future__ import annotations

import time


_DAY = 86400
_MAX_AGE_DAYS = 7


def is_fresh_wallet(first_seen_ts: int | None) -> bool:
    if first_seen_ts is None:
        return True
    age_days = (time.time() - first_seen_ts) / _DAY
    return age_days < _MAX_AGE_DAYS
