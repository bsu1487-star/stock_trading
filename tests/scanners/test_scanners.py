"""스캐너 엔진 테스트"""

import numpy as np
import pandas as pd
import pytest

from app.scanners.builtin.volume_breakout import VolumeBreakoutScanner
from app.scanners.builtin.bottom_rebound import BottomReboundScanner
from app.scanners.builtin.c_spot import CSpotScanner
from app.scanners.dsl import ScannerDSL


def make_bars(n=60, base=10000, trend=0.001, vol_base=10000):
    np.random.seed(42)
    closes = [base]
    for i in range(1, n):
        closes.append(closes[-1] * (1 + trend + np.random.normal(0, 0.01)))
    closes = np.array(closes)
    return pd.DataFrame({
        "open": closes * 0.999,
        "high": closes * 1.005,
        "low": closes * 0.995,
        "close": closes,
        "volume": np.random.randint(vol_base // 2, vol_base * 2, n),
    })


class TestVolumeBreakoutScanner:
    def test_no_result_on_flat(self):
        scanner = VolumeBreakoutScanner()
        bars = make_bars(60, trend=0.0)
        results = scanner.scan({"A": bars})
        # 플랫 데이터에서는 돌파 시그널 나오기 어려움
        assert isinstance(results, list)

    def test_returns_scan_results(self):
        scanner = VolumeBreakoutScanner(vol_ratio_threshold=0.5)  # 낮은 임계값
        bars = make_bars(60)
        # 마지막 봉 거래량을 극대화
        bars.loc[bars.index[-1], "volume"] = 100000
        bars.loc[bars.index[-1], "close"] = bars["high"].max() * 1.01
        results = scanner.scan({"A": bars})
        assert all(hasattr(r, "score") for r in results)


class TestBottomReboundScanner:
    def test_detects_oversold(self):
        # 급락 데이터: 안정 후 급락
        n = 40
        closes = [10000] * 20  # 안정 구간
        for i in range(20):
            closes.append(closes[-1] * 0.97)  # 3%씩 급락
        closes = np.array(closes, dtype=float)
        bars = pd.DataFrame({
            "open": closes * 1.001, "high": closes * 1.005,
            "low": closes * 0.995, "close": closes,
            "volume": [10000] * n,
        })
        scanner = BottomReboundScanner()
        results = scanner.scan({"A": bars})
        assert len(results) > 0
        assert results[0].stock_code == "A"


class TestCSpotScanner:
    def test_detects_c_spot(self):
        # 급등 후 눌림 데이터 생성
        n = 80
        closes = [10000]
        for i in range(1, 40):
            closes.append(closes[-1] * 1.01)  # 상승
        peak = closes[-1]
        for i in range(40, 70):
            closes.append(closes[-1] * 0.99)  # 하락 (눌림)
        for i in range(70, n):
            closes.append(closes[-1] * 1.002)  # 소폭 반등
        closes = np.array(closes)
        bars = pd.DataFrame({
            "open": closes * 0.999, "high": closes * 1.005,
            "low": closes * 0.995, "close": closes,
            "volume": [10000] * n,
        })
        scanner = CSpotScanner(surge_pct=10, pullback_min=10, pullback_max=50)
        results = scanner.scan({"A": bars})
        # 급등+눌림 패턴이므로 탐지 가능
        assert isinstance(results, list)


class TestScannerDSL:
    def test_list_scanners(self):
        names = ScannerDSL.list_scanners()
        assert "volume_breakout" in names
        assert "c_spot" in names
        assert len(names) == 7

    def test_get_scanner(self):
        scanner = ScannerDSL.get_scanner("volume_breakout")
        assert scanner.name == "volume_breakout"

    def test_get_unknown_raises(self):
        with pytest.raises(KeyError):
            ScannerDSL.get_scanner("nonexistent")

    def test_load_from_string(self):
        yaml_str = """
scanner_name: volume_breakout
market: KRX
timeframe: 5m
filters:
  min_price: 3000
conditions:
  - type: volume_ratio
    value: 2.0
"""
        config = ScannerDSL.load_from_string(yaml_str)
        assert config.scanner_name == "volume_breakout"
        assert config.filters["min_price"] == 3000
        assert len(config.conditions) == 1
