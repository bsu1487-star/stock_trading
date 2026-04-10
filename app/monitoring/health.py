from __future__ import annotations

from datetime import datetime

from app.monitoring.logger import get_logger

log = get_logger("monitoring.health")


class HealthCheck:
    """시스템 헬스체크"""

    def __init__(self):
        self._last_scan_at: datetime | None = None
        self._last_order_at: datetime | None = None
        self._active_strategy: str = ""
        self._scheduler_running: bool = False

    def record_scan(self):
        self._last_scan_at = datetime.now()

    def record_order(self):
        self._last_order_at = datetime.now()

    def set_strategy(self, name: str):
        self._active_strategy = name

    def set_scheduler_running(self, running: bool):
        self._scheduler_running = running

    async def check(
        self,
        auth=None,
        portfolio_manager=None,
        daily_pnl_pct: float = 0.0,
    ) -> dict:
        token_valid = False
        token_expires_in = 0.0

        if auth:
            token_valid = auth.is_valid
            if auth._expires_at:
                delta = (auth._expires_at - datetime.now()).total_seconds() / 60
                token_expires_in = max(delta, 0)

        open_positions = 0
        if portfolio_manager:
            open_positions = portfolio_manager.count

        status = "ok"
        if not token_valid:
            status = "degraded"
        if not self._scheduler_running:
            status = "degraded"

        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "api_connection": token_valid,
            "token_valid": token_valid,
            "token_expires_in_minutes": round(token_expires_in, 1),
            "scheduler_running": self._scheduler_running,
            "last_scan_at": self._last_scan_at.isoformat() if self._last_scan_at else None,
            "last_order_at": self._last_order_at.isoformat() if self._last_order_at else None,
            "active_strategy": self._active_strategy,
            "open_positions": open_positions,
            "daily_pnl_pct": round(daily_pnl_pct, 2),
        }
