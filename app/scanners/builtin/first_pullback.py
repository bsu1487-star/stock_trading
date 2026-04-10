"""스캐너 6. 장중 랭킹 진입 후 첫 조정 후보"""

from __future__ import annotations

import pandas as pd

from app.market.indicators import TechnicalIndicators as TI
from app.scanners.base import Scanner, ScanResult


class FirstPullbackScanner(Scanner):
    name = "first_pullback"

    def scan(self, candidates: dict[str, pd.DataFrame]) -> list[ScanResult]:
        results = []
        for code, df in candidates.items():
            if len(df) < 20:
                continue

            last = df.iloc[-1]
            day_high = df["high"].max()
            day_change = (last["close"] - df["open"].iloc[0]) / df["open"].iloc[0] * 100

            # 당일 상승률 상위 + 고가 대비 조정
            if day_change > 3.0:
                pullback_pct = (day_high - last["close"]) / day_high * 100
                if 2.0 < pullback_pct < 10.0:
                    score = day_change + (10 - pullback_pct)
                    results.append(ScanResult(stock_code=code, stock_name="", score=score,
                                              reasons=[f"당일 +{day_change:.1f}%", f"고가 대비 -{pullback_pct:.1f}% 조정"]))

        results.sort(key=lambda r: r.score, reverse=True)
        return results
