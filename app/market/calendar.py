from __future__ import annotations

from datetime import date, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.models import TradingCalendar


class MarketCalendar:
    """거래일 캘린더 관리"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def is_trading_day(self, dt: date) -> bool:
        # 주말은 무조건 휴장
        if dt.weekday() >= 5:
            return False
        row = await self._get_calendar(dt)
        if row is None:
            return True  # 캘린더에 없으면 평일은 거래일로 간주
        return row.is_trading_day

    async def is_half_day(self, dt: date) -> bool:
        row = await self._get_calendar(dt)
        if row is None:
            return False
        return row.is_half_day

    async def get_close_time(self, dt: date) -> time:
        if await self.is_half_day(dt):
            return time(12, 30)
        return time(15, 30)

    async def get_next_trading_day(self, dt: date) -> date:
        candidate = dt + timedelta(days=1)
        for _ in range(10):  # 최대 10일 탐색 (연휴 대비)
            if await self.is_trading_day(candidate):
                return candidate
            candidate += timedelta(days=1)
        return candidate

    async def _get_calendar(self, dt: date) -> TradingCalendar | None:
        result = await self._session.execute(
            select(TradingCalendar).where(TradingCalendar.date == dt)
        )
        return result.scalar_one_or_none()
