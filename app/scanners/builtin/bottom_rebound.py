"""스캐너 2. 저점 반등 후보"""

from __future__ import annotations

import pandas as pd

from app.market.indicators import TechnicalIndicators as TI
from app.scanners.base import Scanner, ScanResult


class BottomReboundScanner(Scanner):
    name = "bottom_rebound"

    def scan(self, candidates: dict[str, pd.DataFrame]) -> list[ScanResult]:
        results = []
        for code, df in candidates.items():
            if len(df) < 30:
                continue
            last = df.iloc[-1]
            rsi = TI.rsi(df["close"], 5)
            pct5 = df["close"].pct_change(5).iloc[-1] * 100
            last_rsi = rsi.iloc[-1] if not rsi.empty else 50

            if last_rsi < 30 and pct5 < -5:
                score = (30 - float(last_rsi)) + abs(pct5)
                results.append(ScanResult(stock_code=code, stock_name="", score=score,
                                          reasons=[f"RSI(5)={last_rsi:.1f}", f"5일 낙폭={pct5:.1f}%"]))

        results.sort(key=lambda r: r.score, reverse=True)
        return results
