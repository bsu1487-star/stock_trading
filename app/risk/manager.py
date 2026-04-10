from __future__ import annotations

from datetime import time

from app.core.types import AccountState


class RiskManager:
    """리스크 통합 관리"""

    def __init__(
        self,
        max_daily_loss_pct: float = 2.0,
        max_positions: int = 5,
        max_consecutive_losses: int = 3,
        stop_loss_pct: float = 3.0,
        take_profit_pct: float = 5.0,
        no_entry_after: time = time(15, 0),
    ):
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_positions = max_positions
        self.max_consecutive_losses = max_consecutive_losses
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.no_entry_after = no_entry_after

    def check_entry_allowed(
        self,
        account_state: AccountState,
        current_positions: int,
        current_time: time | None = None,
    ) -> tuple[bool, str]:
        # 일일 손실 한도
        if account_state.total_equity > 0:
            daily_loss_pct = abs(account_state.daily_realized_pnl) / account_state.total_equity * 100
            if account_state.daily_realized_pnl < 0 and daily_loss_pct >= self.max_daily_loss_pct:
                return False, f"일일 손실 한도 초과 ({daily_loss_pct:.1f}%)"

        # 연속 손실
        if account_state.consecutive_losses >= self.max_consecutive_losses:
            return False, f"연속 손실 {account_state.consecutive_losses}회 (한도 {self.max_consecutive_losses})"

        # 최대 포지션 수
        if current_positions >= self.max_positions:
            return False, f"최대 포지션 수 도달 ({current_positions}/{self.max_positions})"

        # 장 마감 전 진입 제한
        if current_time and current_time >= self.no_entry_after:
            return False, f"장 마감 전 진입 제한 ({self.no_entry_after} 이후)"

        return True, ""

    def check_stop_loss(self, unrealized_pnl_pct: float) -> bool:
        return unrealized_pnl_pct <= -self.stop_loss_pct

    def check_take_profit(self, unrealized_pnl_pct: float) -> bool:
        return unrealized_pnl_pct >= self.take_profit_pct
