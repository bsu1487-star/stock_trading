from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StockInfo:
    code: str
    name: str
    market: str  # "KOSPI" | "KOSDAQ"
    stock_type: str  # "common" | "etf" | "etn" | "spac" | "preferred"
    is_suspended: bool = False
    is_managed: bool = False


class StockMaster:
    """종목 마스터 관리 (메모리 캐시)"""

    def __init__(self):
        self._stocks: dict[str, StockInfo] = {}

    def load(self, stocks: list[StockInfo]):
        self._stocks = {s.code: s for s in stocks}

    def get(self, code: str) -> StockInfo | None:
        return self._stocks.get(code)

    def get_all(self) -> list[StockInfo]:
        return list(self._stocks.values())

    def get_common_stocks(self) -> list[StockInfo]:
        """보통주만 반환 (ETF, ETN, 스팩, 우선주, 거래정지, 관리종목 제외)"""
        return [
            s
            for s in self._stocks.values()
            if s.stock_type == "common" and not s.is_suspended and not s.is_managed
        ]

    @property
    def count(self) -> int:
        return len(self._stocks)
