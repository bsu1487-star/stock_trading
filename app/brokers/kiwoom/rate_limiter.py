from __future__ import annotations

import asyncio
import time


class RateLimiter:
    """토큰 버킷 기반 API 호출 제한 관리"""

    def __init__(self, max_calls_per_second: int = 5):
        self._max_calls = max_calls_per_second
        self._call_times: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self):
        """호출 슬롯 획득. 제한 초과 시 대기."""
        async with self._lock:
            now = time.monotonic()
            self._call_times = [t for t in self._call_times if now - t < 1.0]

            if len(self._call_times) >= self._max_calls:
                wait = 1.0 - (now - self._call_times[0])
                if wait > 0:
                    await asyncio.sleep(wait)

            self._call_times.append(time.monotonic())

    @property
    def recent_call_count(self) -> int:
        now = time.monotonic()
        return len([t for t in self._call_times if now - t < 1.0])
