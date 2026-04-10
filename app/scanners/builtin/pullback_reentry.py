"""스캐너 5. 눌림목 후 재상승 후보"""

from __future__ import annotations

import pandas as pd

from app.market.indicators import TechnicalIndicators as TI
from app.scanners.base import Scanner, ScanResult


class PullbackReentryScanner(Scanner):
    name = "pullback_reentry"

    def scan(self, candidates: dict[str, pd.DataFrame]) -> list[ScanResult]:
        results = []
        for code, df in candidates.items():
            if len(df) < 40:
                continue

            sma20 = TI.sma(df["close"], 20)
            sma60 = TI.sma(df["close"], 60) if len(df) >= 60 else sma20
            vol_ratio = TI.volume_ratio(df["volume"], 20)
            last = df.iloc[-1]

            trend_up = sma20.iloc[-1] > sma60.iloc[-1] if len(df) >= 60 else True
            pullback = df["close"].iloc[-5:-1].mean() < sma20.iloc[-5:-1].mean()
            recovery = last["close"] > sma20.iloc[-1]
            vol_expand = vol_ratio.iloc[-1] > 1.2

            if trend_up and pullback and recovery and vol_expand:
                score = float(vol_ratio.iloc[-1]) * 20
                results.append(ScanResult(stock_code=code, stock_name="", score=score,
                                          reasons=["상승추세 눌림 후 재상승", f"거래량 {vol_ratio.iloc[-1]:.1f}배"]))

        results.sort(key=lambda r: r.score, reverse=True)
        return results
