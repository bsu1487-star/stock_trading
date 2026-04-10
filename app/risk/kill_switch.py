from __future__ import annotations

from app.monitoring.logger import get_logger

log = get_logger("risk.kill_switch")


class KillSwitch:
    """긴급 전체 청산"""

    def __init__(self):
        self._triggered = False

    @property
    def is_triggered(self) -> bool:
        return self._triggered

    async def execute(self, order_client, portfolio_manager, pending_orders: list | None = None):
        """
        1. 모든 미체결 주문 취소
        2. 모든 보유 포지션 시장가 매도
        3. 트리거 플래그 설정
        """
        self._triggered = True
        log.critical("kill_switch_triggered")

        # 미체결 취소
        if pending_orders:
            for order in pending_orders:
                try:
                    await order_client.cancel(order["order_no"], int(order.get("qty", 0)))
                    log.info("kill_switch_cancel", order_no=order["order_no"])
                except Exception as e:
                    log.error("kill_switch_cancel_failed", order_no=order["order_no"], error=str(e))

        # 전 포지션 매도
        for pos in portfolio_manager.positions:
            try:
                await order_client.sell(pos.stock_code, pos.qty, order_type="03")
                log.info("kill_switch_sell", stock_code=pos.stock_code, qty=pos.qty)
            except Exception as e:
                log.error("kill_switch_sell_failed", stock_code=pos.stock_code, error=str(e))

    def reset(self):
        self._triggered = False
