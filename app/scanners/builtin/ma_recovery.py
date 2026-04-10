"""스캐너 3. 바닥권 횡보 후 이평선 회복"""

from __future__ import annotations

import pandas as pd

from app.market.indicators import TechnicalIndicators as TI
from app.scanners.base import Scanner, ScanResult


class MARecoveryScanner(Scanner):
    name = "ma_recovery"

    def scan(self, candidates: dict[str, pd.DataFrame]) -> list[ScanResult]:
        results = []
        for code, df in candidates.items():
            if len(df) < 60:
                continue
            sma20 = TI.sma(df["close"], 20)
            last = df.iloc[-1]
            prev = df.iloc[-2]
            if prev["close"] < sma20.iloc[-2] and last["close"] > sma20.iloc[-1]:
                score = 50.0
                results.append(ScanResult(stock_code=code, stock_name="", score=score,
                                          reasons=["20일선 상향 돌파"]))
        results.sort(key=lambda r: r.score, reverse=True)
        return results
