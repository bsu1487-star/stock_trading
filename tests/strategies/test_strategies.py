"""전략 엔진 테스트"""

import numpy as np
import pandas as pd
import pytest

from app.core.types import AccountState, OrderSide, Position, SignalAction

# 전략 import → 자동 등록
from app.strategies.mean_reversion import MeanReversion
from app.strategies.momentum_breakout import MomentumBreakout
from app.strategies.multi_factor import MultiFactor
from app.strategies.pullback_trend import PullbackTrend
from app.strategies.low_volatility_trend import LowVolTrend
from app.strategies.registry import StrategyRegistry


def make_bars(n: int = 100, base_price: float = 10000, trend: float = 0.001):
    """테스트용 분봉 데이터 생성"""
    np.random.seed(42)
    closes = [base_price]
    for i in range(1, n):
        closes.append(closes[-1] * (1 + trend + np.random.normal(0, 0.005)))
    closes = np.array(closes)
    return pd.DataFrame({
        "stock_code": ["005930"] * n,
        "open": closes * 0.999,
        "high": closes * 1.005,
        "low": closes * 0.995,
        "close": closes,
        "volume": np.random.randint(10000, 100000, n),
        "turnover": closes * np.random.randint(10000, 100000, n),
    })


class TestStrategyRegistry:
    def test_all_registered(self):
        names = StrategyRegistry.list_all()
        assert "momentum_breakout" in names
        assert "pullback_trend" in names
        assert "mean_reversion" in names
        assert "low_volatility_trend" in names
        assert "multi_factor" in names

    def test_get_strategy(self):
        cls = StrategyRegistry.get("multi_factor")
        assert cls is MultiFactor

    def test_get_unknown_raises(self):
        with pytest.raises(KeyError):
            StrategyRegistry.get("nonexistent")

    def test_create_instance(self):
        strategy = StrategyRegistry.create("multi_factor")
        assert isinstance(strategy, MultiFactor)
        assert strategy.name == "multi_factor"


class TestMomentumBreakout:
    def test_interface(self):
        s = MomentumBreakout()
        assert s.name == "momentum_breakout"
        assert s.timeframe == "5m"
        assert s.warmup_bars == 80

    def test_prepare_features(self):
        s = MomentumBreakout()
        bars = make_bars(100)
        result = s.prepare_features(bars)
        assert "highest_n" in result.columns
        assert "vol_ratio" in result.columns
        assert "sma_20" in result.columns

    def test_no_signal_during_warmup(self):
        s = MomentumBreakout()
        bars = make_bars(10)
        bars = s.prepare_features(bars)
        signals = s.on_bar(None, bars, [], AccountState())
        assert signals == []

    def test_exit_on_stop_loss(self):
        s = MomentumBreakout(stop_loss_pct=3.0)
        bars = make_bars(100)
        bars = s.prepare_features(bars)
        pos = Position("005930", "삼성전자", "momentum_breakout", 10, 10000, 9500)
        signals = s.on_bar(None, bars, [pos], AccountState())
        exit_signals = [sig for sig in signals if sig.action == SignalAction.EXIT]
        assert len(exit_signals) == 1
        assert "손절" in exit_signals[0].reason


class TestMultiFactor:
    def test_score_stock(self):
        s = MultiFactor()
        row = pd.Series({
            "return_20": 10.0,
            "return_60": 15.0,
            "vol_ratio": 2.0,
            "sma_20": 100,
            "sma_60": 95,
            "atr_20": 2.0,
            "close": 100,
        })
        score = s.score_stock(row)
        assert score > 0

    def test_score_penalizes_gap(self):
        s = MultiFactor()
        normal = pd.Series({"return_20": 10, "return_60": 5, "vol_ratio": 1.5, "sma_20": 100, "sma_60": 95, "atr_20": 1, "close": 100})
        gap = pd.Series({"return_20": 35, "return_60": 5, "vol_ratio": 1.5, "sma_20": 100, "sma_60": 95, "atr_20": 1, "close": 100})
        assert s.score_stock(normal) <= s.score_stock(gap) + 20  # 갭 패널티 적용

    def test_generate_orders_entry(self):
        s = MultiFactor()
        from app.core.types import Signal
        sig = Signal(stock_code="005930", action=SignalAction.ENTRY, side=OrderSide.BUY,
                     reason="test", score=50, strategy_name="multi_factor")
        orders = s.generate_orders([sig], [], AccountState())
        assert len(orders) == 1
        assert orders[0].side == OrderSide.BUY


class TestMeanReversion:
    def test_interface(self):
        s = MeanReversion()
        assert s.name == "mean_reversion"
        assert s.supports_overnight is False


class TestPullbackTrend:
    def test_interface(self):
        s = PullbackTrend()
        assert s.name == "pullback_trend"
        assert s.supports_overnight is True


class TestLowVolTrend:
    def test_interface(self):
        s = LowVolTrend()
        assert s.name == "low_volatility_trend"
        assert s.timeframe == "15m"
