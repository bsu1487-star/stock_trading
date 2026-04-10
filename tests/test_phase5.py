"""Phase 5 실행 엔진 테스트"""

from datetime import time

import pytest

from app.core.types import AccountState, OrderRequest, OrderSide, OrderType, Position
from app.execution.conflict_resolver import ConflictResolver
from app.portfolio.manager import PortfolioManager
from app.portfolio.position_sizer import PositionSizer
from app.risk.drawdown import DrawdownManager
from app.risk.kill_switch import KillSwitch
from app.risk.manager import RiskManager


class TestPositionSizer:
    def test_equal_weight(self):
        qty = PositionSizer.equal_weight(10_000_000, 5, 80000)
        assert qty == 25  # 2,000,000 / 80,000 = 25

    def test_equal_weight_zero_price(self):
        assert PositionSizer.equal_weight(10_000_000, 5, 0) == 0

    def test_fixed_amount(self):
        qty = PositionSizer.fixed_amount(2_000_000, 80000)
        assert qty == 25


class TestRiskManager:
    def test_entry_allowed(self):
        rm = RiskManager(max_daily_loss_pct=2.0, max_positions=5)
        state = AccountState(total_equity=10_000_000, available_cash=5_000_000)
        allowed, reason = rm.check_entry_allowed(state, 3)
        assert allowed is True

    def test_daily_loss_exceeded(self):
        rm = RiskManager(max_daily_loss_pct=2.0)
        state = AccountState(total_equity=10_000_000, daily_realized_pnl=-250000)
        allowed, reason = rm.check_entry_allowed(state, 0)
        assert allowed is False
        assert "일일 손실" in reason

    def test_max_positions(self):
        rm = RiskManager(max_positions=5)
        state = AccountState(total_equity=10_000_000)
        allowed, reason = rm.check_entry_allowed(state, 5)
        assert allowed is False
        assert "포지션" in reason

    def test_consecutive_losses(self):
        rm = RiskManager(max_consecutive_losses=3)
        state = AccountState(total_equity=10_000_000, consecutive_losses=3)
        allowed, reason = rm.check_entry_allowed(state, 0)
        assert allowed is False

    def test_no_entry_after_close(self):
        rm = RiskManager(no_entry_after=time(15, 0))
        state = AccountState(total_equity=10_000_000)
        allowed, reason = rm.check_entry_allowed(state, 0, time(15, 5))
        assert allowed is False
        assert "마감" in reason

    def test_stop_loss_check(self):
        rm = RiskManager(stop_loss_pct=3.0)
        assert rm.check_stop_loss(-3.5) is True
        assert rm.check_stop_loss(-2.0) is False

    def test_take_profit_check(self):
        rm = RiskManager(take_profit_pct=5.0)
        assert rm.check_take_profit(5.5) is True
        assert rm.check_take_profit(3.0) is False


class TestDrawdownManager:
    def test_no_drawdown(self):
        dm = DrawdownManager(reduce_threshold_pct=1.0, stop_threshold_pct=2.0)
        dm.update_peak(10_000_000)
        assert dm.get_weight_multiplier(10_000_000) == 1.0

    def test_reduce_at_1pct(self):
        dm = DrawdownManager(reduce_threshold_pct=1.0, stop_threshold_pct=2.0)
        dm.update_peak(10_000_000)
        assert dm.get_weight_multiplier(9_850_000) == 0.5

    def test_stop_at_2pct(self):
        dm = DrawdownManager(reduce_threshold_pct=1.0, stop_threshold_pct=2.0)
        dm.update_peak(10_000_000)
        assert dm.get_weight_multiplier(9_750_000) == 0.0

    def test_peak_updates(self):
        dm = DrawdownManager()
        dm.update_peak(100)
        dm.update_peak(110)
        assert dm.peak_equity == 110
        dm.update_peak(105)  # 하락은 peak 갱신 안 됨
        assert dm.peak_equity == 110

    def test_mdd_pct(self):
        dm = DrawdownManager()
        dm.update_peak(10_000_000)
        assert dm.current_mdd_pct(9_500_000) == pytest.approx(5.0)


class TestKillSwitch:
    def test_initial_state(self):
        ks = KillSwitch()
        assert ks.is_triggered is False

    def test_reset(self):
        ks = KillSwitch()
        ks._triggered = True
        ks.reset()
        assert ks.is_triggered is False


class TestConflictResolver:
    def _make_buy(self, code: str, qty: int = 10) -> OrderRequest:
        return OrderRequest(code, "", OrderSide.BUY, OrderType.MARKET, qty, strategy_name="test")

    def _make_sell(self, code: str, qty: int = 10) -> OrderRequest:
        return OrderRequest(code, "", OrderSide.SELL, OrderType.MARKET, qty, strategy_name="test")

    def test_dedup_same_stock(self):
        cr = ConflictResolver()
        orders = [self._make_buy("005930"), self._make_buy("005930")]
        result = cr.resolve(orders, 10_000_000, set(), {"005930": 80000}, 2_000_000)
        buy_orders = [o for o in result if o.side == OrderSide.BUY]
        assert len(buy_orders) == 1

    def test_skip_held_stock(self):
        cr = ConflictResolver()
        orders = [self._make_buy("005930")]
        result = cr.resolve(orders, 10_000_000, {"005930"}, {}, 2_000_000)
        buy_orders = [o for o in result if o.side == OrderSide.BUY]
        assert len(buy_orders) == 0

    def test_sell_always_passes(self):
        cr = ConflictResolver()
        orders = [self._make_sell("005930")]
        result = cr.resolve(orders, 0, set(), {}, 0)
        assert len(result) == 1

    def test_cash_limit(self):
        cr = ConflictResolver()
        orders = [self._make_buy("A"), self._make_buy("B"), self._make_buy("C")]
        # 예산이 2건분만 있음
        result = cr.resolve(orders, 4_000_000, set(), {}, 2_000_000)
        buy_orders = [o for o in result if o.side == OrderSide.BUY]
        assert len(buy_orders) == 2


class TestPortfolioManager:
    def test_add_position(self):
        pm = PortfolioManager()
        pm.add_or_update(Position("005930", "삼성전자", "test", 10, 80000, 82000))
        assert pm.count == 1
        assert pm.get("005930").qty == 10

    def test_remove_on_zero_qty(self):
        pm = PortfolioManager()
        pm.add_or_update(Position("005930", "삼성전자", "test", 10, 80000))
        pm.add_or_update(Position("005930", "삼성전자", "test", 0, 80000))
        assert pm.count == 0

    def test_total_equity(self):
        pm = PortfolioManager()
        pm.add_or_update(Position("005930", "삼성전자", "test", 10, 80000, 82000))
        equity = pm.total_equity(5_000_000)
        assert equity == 5_000_000 + 82000 * 10
