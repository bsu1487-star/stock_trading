"""기술지표 테스트"""

import numpy as np
import pandas as pd
import pytest

from app.market.indicators import TechnicalIndicators as TI


@pytest.fixture
def sample_series():
    return pd.Series([10, 11, 12, 11, 13, 14, 13, 15, 16, 14, 15, 17, 18, 16, 19])


@pytest.fixture
def sample_ohlcv():
    return pd.DataFrame(
        {
            "open": [100, 102, 101, 103, 105, 104, 106, 107, 108, 106],
            "high": [103, 104, 103, 106, 107, 106, 108, 110, 109, 108],
            "low": [99, 100, 99, 101, 103, 102, 104, 105, 105, 104],
            "close": [102, 101, 103, 105, 104, 106, 107, 108, 106, 107],
            "volume": [1000, 1200, 800, 1500, 1100, 900, 1300, 1400, 1000, 1100],
        }
    )


class TestSMA:
    def test_basic(self, sample_series):
        result = TI.sma(sample_series, 3)
        assert result.iloc[2] == pytest.approx((10 + 11 + 12) / 3)
        assert pd.isna(result.iloc[0])

    def test_period_larger_than_data(self):
        s = pd.Series([1, 2, 3])
        result = TI.sma(s, 5)
        assert result.isna().all()


class TestEMA:
    def test_basic(self, sample_series):
        result = TI.ema(sample_series, 3)
        assert len(result) == len(sample_series)
        assert not result.isna().any()


class TestRSI:
    def test_range(self, sample_series):
        result = TI.rsi(sample_series, 5)
        valid = result.dropna()
        assert (valid >= 0).all()
        assert (valid <= 100).all()

    def test_all_up(self):
        s = pd.Series(range(1, 20))
        result = TI.rsi(s, 5)
        valid = result.dropna()
        assert (valid > 90).all()


class TestATR:
    def test_positive(self, sample_ohlcv):
        result = TI.atr(sample_ohlcv, 5)
        valid = result.dropna()
        assert (valid > 0).all()


class TestBollingerBands:
    def test_upper_above_lower(self, sample_series):
        upper, middle, lower = TI.bollinger_bands(sample_series, 5, 2.0)
        valid_idx = upper.dropna().index
        assert (upper[valid_idx] >= middle[valid_idx]).all()
        assert (middle[valid_idx] >= lower[valid_idx]).all()


class TestVolumeRatio:
    def test_ratio(self, sample_ohlcv):
        result = TI.volume_ratio(sample_ohlcv["volume"], 5)
        valid = result.dropna()
        assert len(valid) > 0


class TestHighestLowest:
    def test_highest(self, sample_series):
        result = TI.highest(sample_series, 5)
        assert result.iloc[4] == 13

    def test_lowest(self, sample_series):
        result = TI.lowest(sample_series, 5)
        assert result.iloc[4] == 10
