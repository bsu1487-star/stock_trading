"""Rate Limiter 테스트"""

import asyncio
import time

from app.brokers.kiwoom.rate_limiter import RateLimiter


class TestRateLimiter:
    async def test_allows_within_limit(self):
        limiter = RateLimiter(max_calls_per_second=5)
        for _ in range(5):
            await limiter.acquire()
        assert limiter.recent_call_count <= 5

    async def test_throttles_over_limit(self):
        limiter = RateLimiter(max_calls_per_second=3)
        start = time.monotonic()
        for _ in range(6):
            await limiter.acquire()
        elapsed = time.monotonic() - start
        # 3회 후 대기 발생 → 최소 1초 이상 소요
        assert elapsed >= 0.9

    async def test_recent_call_count(self):
        limiter = RateLimiter(max_calls_per_second=10)
        await limiter.acquire()
        await limiter.acquire()
        assert limiter.recent_call_count == 2
