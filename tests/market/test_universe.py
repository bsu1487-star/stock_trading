"""유니버스 빌더 테스트"""

import pandas as pd

from app.market.master import StockInfo, StockMaster
from app.market.universe import UniverseBuilder


def make_daily(close: float, turnover: float, days: int = 20):
    return pd.DataFrame(
        {
            "date": pd.date_range("2026-03-01", periods=days),
            "open": [close] * days,
            "high": [close * 1.02] * days,
            "low": [close * 0.98] * days,
            "close": [close] * days,
            "volume": [100000] * days,
            "turnover": [turnover] * days,
        }
    )


class TestUniverseBuilder:
    def _setup(self):
        master = StockMaster()
        master.load(
            [
                StockInfo("005930", "삼성전자", "KOSPI", "common"),
                StockInfo("000660", "SK하이닉스", "KOSPI", "common"),
                StockInfo("999999", "저가주", "KOSDAQ", "common"),
                StockInfo("111111", "ETF종목", "KOSPI", "etf"),
                StockInfo("222222", "관리종목", "KOSDAQ", "common", is_managed=True),
            ]
        )
        return master

    def test_filters_correctly(self):
        master = self._setup()
        builder = UniverseBuilder(master, min_turnover_20d=1e9, min_price=3000)

        daily_data = {
            "005930": make_daily(80000, 2e9),
            "000660": make_daily(150000, 3e9),
            "999999": make_daily(1500, 5e8),  # 저가 + 거래대금 부족
            "111111": make_daily(50000, 5e9),  # ETF → 마스터에서 제외
            "222222": make_daily(10000, 2e9),  # 관리종목 → 마스터에서 제외
        }

        result = builder.build(daily_data)
        assert "005930" in result
        assert "000660" in result
        assert "999999" not in result  # 저가+거래대금 부족
        assert "111111" not in result  # ETF
        assert "222222" not in result  # 관리종목

    def test_empty_data(self):
        master = self._setup()
        builder = UniverseBuilder(master)
        result = builder.build({})
        assert result == []
