"""Phase 6 운영 보조 테스트"""

import pytest

from app.bot.formatters import format_daily_review, format_order_alert, format_positions, format_status
from app.core.types import AccountState, AlertLevel, Position
from app.monitoring.alerts import AlertManager
from app.monitoring.health import HealthCheck
from app.recovery.startup_check import StartupCheck


class TestFormatters:
    def test_format_status(self):
        state = AccountState(total_equity=10_000_000, available_cash=5_000_000, daily_realized_pnl=50000)
        msg = format_status(state, "multi_factor", True)
        assert "multi_factor" in msg
        assert "실행 중" in msg
        assert "10,000,000" in msg

    def test_format_positions_empty(self):
        msg = format_positions([])
        assert "없습니다" in msg

    def test_format_positions(self):
        positions = [
            Position("005930", "삼성전자", "test", 10, 80000, 82000),
        ]
        msg = format_positions(positions)
        assert "삼성전자" in msg
        assert "005930" in msg

    def test_format_order_alert(self):
        msg = format_order_alert("buy", "multi_factor", "005930", "삼성전자", 10, 81500, "상위 랭킹")
        assert "매수 체결" in msg
        assert "삼성전자" in msg

    def test_format_daily_review(self):
        msg = format_daily_review(
            "2026-04-10", "multi_factor", 124000, 38000, 0.81, 4, 75, 0.3
        )
        assert "일간 성과리뷰" in msg
        assert "KOSPI 대비" in msg


class TestAlertManager:
    async def test_critical_always_sent(self):
        sent = []
        async def mock_send(msg):
            sent.append(msg)

        am = AlertManager(send_fn=mock_send, warning_enabled=False, info_enabled=False)
        await am.send(AlertLevel.CRITICAL, "테스트 긴급")
        assert len(sent) == 1
        assert "CRITICAL" in sent[0]

    async def test_warning_filtered(self):
        sent = []
        async def mock_send(msg):
            sent.append(msg)

        am = AlertManager(send_fn=mock_send, warning_enabled=False, info_enabled=False)
        await am.send(AlertLevel.WARNING, "경고")
        assert len(sent) == 0

    async def test_warning_enabled(self):
        sent = []
        async def mock_send(msg):
            sent.append(msg)

        am = AlertManager(send_fn=mock_send, warning_enabled=True)
        await am.send(AlertLevel.WARNING, "경고")
        assert len(sent) == 1

    async def test_info_default_off(self):
        sent = []
        async def mock_send(msg):
            sent.append(msg)

        am = AlertManager(send_fn=mock_send, info_enabled=False)
        await am.send(AlertLevel.INFO, "정보")
        assert len(sent) == 0


class TestHealthCheck:
    async def test_basic_check(self):
        hc = HealthCheck()
        hc.set_strategy("multi_factor")
        hc.set_scheduler_running(True)
        result = await hc.check()
        assert result["active_strategy"] == "multi_factor"
        assert result["scheduler_running"] is True

    def test_record_scan(self):
        hc = HealthCheck()
        hc.record_scan()
        assert hc._last_scan_at is not None


class TestStartupCheck:
    def test_initial_state(self):
        sc = StartupCheck()
        assert sc.is_ready is False
