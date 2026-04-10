"""스캐너 공통 인터페이스"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd


@dataclass
class ScanResult:
    stock_code: str
    stock_name: str
    score: float
    reasons: list[str] = field(default_factory=list)
    scanned_at: datetime = field(default_factory=datetime.now)


class Scanner(ABC):
    name: str = ""
    market: str = "KRX"
    timeframe: str = "5m"

    @abstractmethod
    def scan(self, candidates: dict[str, pd.DataFrame]) -> list[ScanResult]:
        """
        Args:
            candidates: {종목코드: 봉 DataFrame}
        Returns:
            점수 기반 정렬된 ScanResult 리스트
        """
        ...
