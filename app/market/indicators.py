from __future__ import annotations

import numpy as np
import pandas as pd


class TechnicalIndicators:
    """기술지표 계산"""

    @staticmethod
    def sma(series: pd.Series, period: int) -> pd.Series:
        return series.rolling(window=period).mean()

    @staticmethod
    def ema(series: pd.Series, period: int) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        # avg_loss가 0이면 RS=무한대 → RSI=100
        rs = np.where(avg_loss == 0, np.inf, avg_gain / avg_loss)
        rsi = 100 - (100 / (1 + pd.Series(rs, index=series.index)))
        return rsi

    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift(1)).abs()
        low_close = (df["low"] - df["close"].shift(1)).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

    @staticmethod
    def bollinger_bands(
        series: pd.Series, period: int = 20, std_dev: float = 2.0
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        middle = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        return upper, middle, lower

    @staticmethod
    def volume_ratio(volume: pd.Series, period: int = 20) -> pd.Series:
        avg_vol = volume.rolling(window=period).mean()
        return volume / avg_vol.replace(0, np.inf)

    @staticmethod
    def ma_slope(series: pd.Series, period: int = 20, lookback: int = 5) -> pd.Series:
        ma = series.rolling(window=period).mean()
        return (ma - ma.shift(lookback)) / ma.shift(lookback) * 100

    @staticmethod
    def highest(series: pd.Series, period: int) -> pd.Series:
        return series.rolling(window=period).max()

    @staticmethod
    def lowest(series: pd.Series, period: int) -> pd.Series:
        return series.rolling(window=period).min()
