"""스캐너 7. C자리 탐색기"""

from __future__ import annotations

import pandas as pd

from app.market.indicators import TechnicalIndicators as TI
from app.scanners.base import Scanner, ScanResult


class CSpotScanner(Scanner):
    name = "c_spot"

    def __init__(self, surge_pct: float = 15.0, pullback_min: float = 20.0, pullback_max: float = 50.0):
        self.surge_pct = surge_pct
        self.pullback_min = pullback_min
        self.pullback_max = pullback_max

    def scan(self, candidates: dict[str, pd.DataFrame]) -> list[ScanResult]:
        results = []
        for code, df in candidates.items():
            if len(df) < 60:
                continue

            # 1단계: 선행 급등 확인
            recent_high = df["high"].tail(20).max()
            low_20 = df["low"].tail(60).iloc[:40].min()
            if low_20 <= 0:
                continue
            surge_pct = (recent_high - low_20) / low_20 * 100
            if surge_pct < self.surge_pct:
                continue

            # 2단계: 눌림 확인
            last = df.iloc[-1]
            pullback_pct = (recent_high - last["close"]) / recent_high * 100
            if not (self.pullback_min <= pullback_pct <= self.pullback_max):
                continue

            # 3단계: 재출발 신호 (최근 봉들의 저점이 올라가는지)
            recent_lows = df["low"].tail(5)
            rising_lows = recent_lows.iloc[-1] > recent_lows.iloc[0]

            # 점수 계산
            surge_score = min(surge_pct, 50)
            pullback_score = 50 - abs(pullback_pct - 35)  # 35% 조정이 최적
            rebound_score = 20 if rising_lows else 0

            total_score = surge_score + pullback_score + rebound_score

            results.append(ScanResult(
                stock_code=code, stock_name="", score=total_score,
                reasons=[
                    f"선행 급등 {surge_pct:.1f}%",
                    f"눌림 {pullback_pct:.1f}%",
                    "저점 상승 중" if rising_lows else "저점 하락 중",
                ],
            ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results
