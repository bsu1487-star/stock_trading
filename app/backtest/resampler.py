"""분봉 리샘플링"""

from __future__ import annotations

import pandas as pd


class BarResampler:
    """1분봉 -> N분봉 리샘플링"""

    @staticmethod
    def resample(minute_bars: pd.DataFrame, target_interval: int) -> pd.DataFrame:
        """
        1분봉을 N분봉으로 리샘플링.
        거래일 경계 기준으로 정확히 재구성.

        Args:
            minute_bars: datetime, open, high, low, close, volume 컬럼 필요
            target_interval: 3, 5, 10, 15 등

        Returns:
            리샘플링된 DataFrame
        """
        if target_interval <= 1:
            return minute_bars.copy()

        df = minute_bars.copy()
        if "datetime" in df.columns:
            df = df.set_index("datetime")

        # N분 단위로 그룹핑
        resampled = df.resample(f"{target_interval}min", label="left", closed="left").agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )

        # turnover 컬럼이 있으면 합산
        if "turnover" in df.columns:
            turnover = df["turnover"].resample(f"{target_interval}min", label="left", closed="left").sum()
            resampled["turnover"] = turnover

        # NaN 행 제거 (장 시작/마감 경계)
        resampled = resampled.dropna(subset=["open", "close"])

        resampled = resampled.reset_index()
        return resampled
