from __future__ import annotations

from app.core.types import AlertLevel
from app.monitoring.logger import get_logger

log = get_logger("monitoring.alerts")


class AlertManager:
    """알림 등급별 필터링 및 발송"""

    def __init__(self, send_fn=None, warning_enabled: bool = True, info_enabled: bool = False):
        self._send_fn = send_fn
        self._warning_enabled = warning_enabled
        self._info_enabled = info_enabled

    async def send(self, level: AlertLevel, message: str):
        should_send = False
        if level == AlertLevel.CRITICAL:
            should_send = True
        elif level == AlertLevel.WARNING and self._warning_enabled:
            should_send = True
        elif level == AlertLevel.INFO and self._info_enabled:
            should_send = True

        if should_send and self._send_fn:
            try:
                await self._send_fn(f"[{level.value}] {message}")
            except Exception as e:
                log.error("alert_send_failed", level=level.value, error=str(e))
        elif should_send:
            log.info("alert", level=level.value, message=message)
