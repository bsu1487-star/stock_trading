from __future__ import annotations

import pandas as pd

from .master import StockInfo, StockMaster


class UniverseBuilder:
    """유니버스 필터링"""

    def __init__(
        self,
        master: StockMaster,
        min_turnover_20d: float = 1_000_000_000,
        min_price: float = 3000,
        min_volume_5d: int = 0,
    ):
        self._master = master
        self._min_turnover_20d = min_turnover_20d
        self._min_price = min_price
        self._min_volume_5d = min_volume_5d

    def build(self, daily_data: dict[str, pd.DataFrame]) -> list[str]:
        """
        필터 조건:
        - KOSPI + KOSDAQ 보통주
        - ETF, ETN, 스팩, 우선주 제외
        - 거래정지/관리종목 제외
        - 최근 20일 평균 거래대금 >= min_turnover_20d
        - 주가 >= min_price
        """
        candidates = self._master.get_common_stocks()
        result = []

        for stock in candidates:
            df = daily_data.get(stock.code)
            if df is None or df.empty:
                continue

            recent = df.tail(20)
            if len(recent) < 5:
                continue

            last_close = recent["close"].iloc[-1]
            if last_close < self._min_price:
                continue

            avg_turnover = recent["turnover"].mean() if "turnover" in recent.columns else 0
            if avg_turnover < self._min_turnover_20d:
                continue

            if self._min_volume_5d > 0:
                avg_vol_5d = recent.tail(5)["volume"].mean()
                if avg_vol_5d < self._min_volume_5d:
                    continue

            result.append(stock.code)

        return result
