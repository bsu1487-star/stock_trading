from __future__ import annotations

from datetime import date, datetime

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.brokers.kiwoom.market_data import KiwoomMarketData
from app.monitoring.logger import get_logger
from app.storage.models import DailyBar, MinuteBar

log = get_logger("market.bars")


class BarCollector:
    """일봉/분봉 수집 및 DB 캐시"""

    def __init__(self, session: AsyncSession, market_data: KiwoomMarketData | None = None):
        self._session = session
        self._market_data = market_data

    async def get_daily(self, code: str, days: int = 60) -> pd.DataFrame:
        """DB에서 일봉 조회"""
        result = await self._session.execute(
            select(DailyBar)
            .where(DailyBar.stock_code == code)
            .order_by(DailyBar.date.desc())
            .limit(days)
        )
        rows = result.scalars().all()
        if not rows:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume", "turnover"])

        data = [
            {
                "date": r.date,
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
                "turnover": r.turnover,
            }
            for r in reversed(rows)
        ]
        return pd.DataFrame(data)

    async def get_minute(self, code: str, interval: int = 1, bars: int = 390) -> pd.DataFrame:
        """DB에서 분봉 조회"""
        result = await self._session.execute(
            select(MinuteBar)
            .where(MinuteBar.stock_code == code, MinuteBar.interval == interval)
            .order_by(MinuteBar.datetime.desc())
            .limit(bars)
        )
        rows = result.scalars().all()
        if not rows:
            return pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume", "turnover"])

        data = [
            {
                "datetime": r.datetime,
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
                "turnover": r.turnover,
            }
            for r in reversed(rows)
        ]
        return pd.DataFrame(data)

    async def save_daily(self, code: str, df: pd.DataFrame):
        """일봉 데이터 DB 저장"""
        for _, row in df.iterrows():
            bar = DailyBar(
                stock_code=code,
                date=row["date"] if isinstance(row["date"], date) else datetime.strptime(str(row["date"]), "%Y-%m-%d").date(),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=int(row["volume"]) if pd.notna(row["volume"]) else 0,
                turnover=float(row["turnover"]) if "turnover" in row and pd.notna(row.get("turnover")) else 0.0,
            )
            await self._session.merge(bar)
        await self._session.commit()

    async def save_minute(self, code: str, df: pd.DataFrame, interval: int = 1):
        """분봉 데이터 DB 저장"""
        for _, row in df.iterrows():
            bar = MinuteBar(
                stock_code=code,
                datetime=row["datetime"],
                interval=interval,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=int(row["volume"]) if pd.notna(row["volume"]) else 0,
                turnover=float(row["turnover"]) if "turnover" in row and pd.notna(row.get("turnover")) else 0.0,
            )
            await self._session.merge(bar)
        await self._session.commit()
