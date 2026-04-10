"""자동매매 메인 실행 엔진"""

from __future__ import annotations

from datetime import datetime, time

from app.core.types import AccountState, MarketPhase, OrderSide, SignalAction
from app.execution.conflict_resolver import ConflictResolver
from app.monitoring.logger import get_logger
from app.portfolio.manager import PortfolioManager
from app.portfolio.position_sizer import PositionSizer
from app.risk.drawdown import DrawdownManager
from app.risk.kill_switch import KillSwitch
from app.risk.manager import RiskManager
from app.strategies.base import Strategy

log = get_logger("execution.engine")


class ExecutionEngine:
    """자동매매 메인 실행 루프"""

    def __init__(
        self,
        strategy: Strategy,
        risk_manager: RiskManager,
        drawdown_manager: DrawdownManager,
        portfolio_manager: PortfolioManager,
        conflict_resolver: ConflictResolver,
        kill_switch: KillSwitch,
        max_positions: int = 5,
        per_stock_weight_pct: float = 15.0,
    ):
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.drawdown_manager = drawdown_manager
        self.portfolio = portfolio_manager
        self.conflict_resolver = conflict_resolver
        self.kill_switch = kill_switch
        self.max_positions = max_positions
        self.per_stock_weight_pct = per_stock_weight_pct

    def get_market_phase(self, now: time) -> MarketPhase:
        if now < time(9, 0):
            return MarketPhase.PRE_MARKET
        if now < time(9, 15):
            return MarketPhase.OPENING
        if now < time(15, 0):
            return MarketPhase.REGULAR
        if now < time(15, 20):
            return MarketPhase.CLOSING
        if now < time(15, 30):
            return MarketPhase.POST_MARKET
        return MarketPhase.CLOSED

    async def run_cycle(self, account_state: AccountState, market_data, current_time: datetime | None = None):
        """1주기 실행"""
        if self.kill_switch.is_triggered:
            log.warning("engine_blocked_kill_switch")
            return []

        now = current_time or datetime.now()
        phase = self.get_market_phase(now.time())

        if phase not in (MarketPhase.REGULAR, MarketPhase.CLOSING):
            log.debug("engine_skip_phase", phase=phase.value)
            return []

        # 드로다운 비중 조절
        self.drawdown_manager.update_peak(account_state.total_equity)
        weight_mult = self.drawdown_manager.get_weight_multiplier(account_state.total_equity)

        if weight_mult == 0.0:
            log.warning("engine_mdd_stop", mdd=self.drawdown_manager.current_mdd_pct(account_state.total_equity))
            return []

        # 전략 시그널 생성
        data_with_features = self.strategy.prepare_features(market_data)
        signals = self.strategy.on_bar(now, data_with_features, self.portfolio.positions, account_state)

        if not signals:
            return []

        # 주문 생성
        orders = self.strategy.generate_orders(signals, self.portfolio.positions, account_state)

        # 매수 주문: 리스크 점검
        approved_orders = []
        for order in orders:
            if order.side == OrderSide.SELL:
                approved_orders.append(order)
                continue

            allowed, reason = self.risk_manager.check_entry_allowed(
                account_state, self.portfolio.count, now.time()
            )
            if not allowed:
                log.info("entry_blocked", stock_code=order.stock_code, reason=reason)
                continue

            # 포지션 sizing
            if order.qty == 0:
                budget = account_state.available_cash * (self.per_stock_weight_pct / 100) * weight_mult
                price = market_data["close"].iloc[-1] if "close" in market_data.columns else 0
                order.qty = PositionSizer.fixed_amount(budget, price)

            if order.qty > 0:
                approved_orders.append(order)

        # 충돌 중재
        held_codes = {p.stock_code for p in self.portfolio.positions}
        per_stock_budget = account_state.available_cash * (self.per_stock_weight_pct / 100) * weight_mult

        final_orders = self.conflict_resolver.resolve(
            approved_orders,
            account_state.available_cash,
            held_codes,
            {},
            per_stock_budget,
        )

        log.info("cycle_complete", signals=len(signals), orders=len(final_orders))
        return final_orders
