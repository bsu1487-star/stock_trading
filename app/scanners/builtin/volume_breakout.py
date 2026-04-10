"""스캐너 1. 거래량 급증 + 가격 돌파"""

from __future__ import annotations

import pandas as pd

from app.market.indicators import TechnicalIndicators as TI
from app.scanners.base import Scanner, ScanResult


class VolumeBreakoutScanner(Scanner):
    name = "volume_breakout"

    def __init__(self, vol_ratio_threshold: float = 2.0, lookback: int = 20):
        self.vol_ratio_threshold = vol_ratio_threshold
        self.lookback = lookback

    def scan(self, candidates: dict[str, pd.DataFrame]) -> list[ScanResult]:
        results = []
        for code, df in candidates.items():
            if len(df) < self.lookback + 5:
                continue

            vol_ratio = TI.volume_ratio(df["volume"], self.lookback)
            highest = TI.highest(df["high"], self.lookback)
            last = df.iloc[-1]
            last_vr = vol_ratio.iloc[-1] if not vol_ratio.empty else 0

            if last_vr >= self.vol_ratio_threshold and last["close"] > highest.iloc[-2]:
                score = float(last_vr) * 20
                results.append(ScanResult(
                    stock_code=code,
                    stock_name=last.get("stock_name", ""),
                    score=score,
                    reasons=[
                        f"거래량 {last_vr:.1f}배",
                        f"{self.lookback}봉 고가 돌파",
                    ],
                ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results
