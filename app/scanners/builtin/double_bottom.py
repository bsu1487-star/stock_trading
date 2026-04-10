"""스캐너 4. 이중바닥 후보"""

from __future__ import annotations

import pandas as pd

from app.market.indicators import TechnicalIndicators as TI
from app.scanners.base import Scanner, ScanResult


class DoubleBottomScanner(Scanner):
    name = "double_bottom"

    def __init__(self, lookback: int = 40, tolerance_pct: float = 3.0):
        self.lookback = lookback
        self.tolerance_pct = tolerance_pct

    def scan(self, candidates: dict[str, pd.DataFrame]) -> list[ScanResult]:
        results = []
        for code, df in candidates.items():
            if len(df) < self.lookback:
                continue

            recent = df.tail(self.lookback)
            lows = recent["low"]
            mid = len(lows) // 2

            first_low = lows.iloc[:mid].min()
            second_low = lows.iloc[mid:].min()

            if first_low <= 0:
                continue

            diff_pct = abs(second_low - first_low) / first_low * 100
            if diff_pct <= self.tolerance_pct:
                last = df.iloc[-1]
                neckline = recent["high"].iloc[:mid].max()
                if last["close"] > neckline * 0.98:
                    score = 60 - diff_pct * 5
                    results.append(ScanResult(stock_code=code, stock_name="", score=max(score, 0),
                                              reasons=[f"이중바닥 차이 {diff_pct:.1f}%", "넥라인 접근"]))

        results.sort(key=lambda r: r.score, reverse=True)
        return results
