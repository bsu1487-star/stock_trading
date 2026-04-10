"""백테스트 엔진 테스트"""

import numpy as np
import pandas as pd
import pytest

from app.backtest.engine import BacktestEngine, BacktestResult
from app.backtest.reporter import BacktestReporter
from app.backtest.resampler import BarResampler
from app.simulation.cost_model import CostModel
from app.strategies.multi_factor import MultiFactor


def make_minute_bars(n: int = 390, base_price: float = 10000, trend: float = 0.0002):
    """1거래일분 1분봉 데이터 생성"""
    np.random.seed(42)
    times = pd.date_range("2026-04-01 09:00", periods=n, freq="1min")
    closes = [base_price]
    for i in range(1, n):
        closes.append(closes[-1] * (1 + trend + np.random.normal(0, 0.002)))
    closes = np.array(closes)
    return pd.DataFrame({
        "datetime": times,
        "open": closes * 0.9995,
        "high": closes * 1.003,
        "low": closes * 0.997,
        "close": closes,
        "volume": np.random.randint(1000, 10000, n),
        "turnover": closes * np.random.randint(1000, 10000, n),
    })


class TestBarResampler:
    def test_5min_resample(self):
        bars = make_minute_bars(390)
        result = BarResampler.resample(bars, 5)
        assert len(result) == 78  # 390 / 5

    def test_ohlcv_accuracy(self):
        bars = make_minute_bars(10)
        result = BarResampler.resample(bars, 5)
        # 첫 5분봉
        first_5 = bars.iloc[:5]
        first_bar = result.iloc[0]
        assert first_bar["open"] == pytest.approx(first_5["open"].iloc[0])
        assert first_bar["high"] == pytest.approx(first_5["high"].max())
        assert first_bar["low"] == pytest.approx(first_5["low"].min())
        assert first_bar["close"] == pytest.approx(first_5["close"].iloc[-1])
        assert first_bar["volume"] == first_5["volume"].sum()

    def test_interval_1_returns_copy(self):
        bars = make_minute_bars(10)
        result = BarResampler.resample(bars, 1)
        assert len(result) == 10

    def test_10min_resample(self):
        bars = make_minute_bars(100)
        result = BarResampler.resample(bars, 10)
        assert len(result) == 10


class TestCostModel:
    def test_buy_slippage(self):
        cm = CostModel(slippage_pct=0.10, commission_pct=0.015)
        fill_price, commission = cm.apply_buy(10000, 10)
        assert fill_price == pytest.approx(10010)
        assert commission == pytest.approx(10010 * 10 * 0.00015)

    def test_sell_slippage(self):
        cm = CostModel(slippage_pct=0.10, commission_pct=0.015, tax_pct=0.20)
        fill_price, commission, tax = cm.apply_sell(10000, 10)
        assert fill_price == pytest.approx(9990)
        assert tax == pytest.approx(9990 * 10 * 0.002)

    def test_zero_slippage(self):
        cm = CostModel(slippage_pct=0.0)
        fill_price, _ = cm.apply_buy(10000, 1)
        assert fill_price == 10000


class TestBacktestResult:
    def test_win_rate(self):
        from app.backtest.engine import BacktestTrade
        trades = [
            BacktestTrade("A", "test", "buy", exit_time=pd.Timestamp.now(), pnl=100),
            BacktestTrade("B", "test", "buy", exit_time=pd.Timestamp.now(), pnl=-50),
            BacktestTrade("C", "test", "buy", exit_time=pd.Timestamp.now(), pnl=200),
        ]
        result = BacktestResult(initial_cash=1000000, final_equity=1000250, total_return_pct=0.025, trades=trades)
        assert result.win_rate == pytest.approx(66.666, rel=0.01)
        assert result.total_trades == 3

    def test_profit_factor(self):
        from app.backtest.engine import BacktestTrade
        trades = [
            BacktestTrade("A", "test", "buy", exit_time=pd.Timestamp.now(), pnl=300),
            BacktestTrade("B", "test", "buy", exit_time=pd.Timestamp.now(), pnl=-100),
        ]
        result = BacktestResult(initial_cash=1000000, final_equity=1000200, total_return_pct=0.02, trades=trades)
        assert result.profit_factor == pytest.approx(3.0)

    def test_mdd(self):
        curve = [
            {"datetime": "1", "equity": 100},
            {"datetime": "2", "equity": 110},
            {"datetime": "3", "equity": 95},
            {"datetime": "4", "equity": 105},
        ]
        result = BacktestResult(initial_cash=100, final_equity=105, total_return_pct=5.0, equity_curve=curve)
        # peak=110, trough=95, mdd = (110-95)/110 * 100 = 13.636%
        assert result.mdd_pct == pytest.approx(13.636, rel=0.01)


class TestBacktestReporter:
    def test_generate(self):
        result = BacktestResult(initial_cash=20000000, final_equity=22500000, total_return_pct=12.5)
        report = BacktestReporter.generate(result, "multi_factor")
        assert report["strategy"] == "multi_factor"
        assert report["total_return_pct"] == 12.5

    def test_to_text(self):
        report = {
            "strategy": "multi_factor",
            "initial_cash": 20000000,
            "final_equity": 22500000,
            "total_return_pct": 12.5,
            "total_trades": 42,
            "win_rate": 58.0,
            "profit_factor": 1.82,
            "mdd_pct": 4.2,
        }
        text = BacktestReporter.to_text(report)
        assert "multi_factor" in text
        assert "12.50%" in text
