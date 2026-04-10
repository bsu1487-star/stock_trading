"""Phase 1 기초 인프라 테스트"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.config import Settings
from app.core.constants import TR_BUY, TR_SELL
from app.core.exceptions import AuthError, OrderError, RateLimitError, TradingError
from app.core.types import (
    AccountState,
    AlertLevel,
    MarketPhase,
    OrderSide,
    OrderType,
    Position,
    Signal,
    SignalAction,
)
from app.main import app
from app.storage.models import Base


class TestConfig:
    def test_settings_defaults(self):
        s = Settings(
            kiwoom_app_key="test",
            kiwoom_app_secret="test",
            kiwoom_account_no="test",
        )
        assert s.kiwoom_is_mock is True
        assert s.max_positions == 5
        assert s.max_daily_loss_pct == 2.0
        assert s.api_max_calls_per_second == 5

    def test_mock_base_url(self):
        s = Settings(kiwoom_is_mock=True)
        assert s.kiwoom_base_url == "https://mockapi.kiwoom.com"

    def test_real_base_url(self):
        s = Settings(kiwoom_is_mock=False)
        assert s.kiwoom_base_url == "https://api.kiwoom.com"


class TestConstants:
    def test_tr_codes(self):
        assert TR_BUY == "kt10000"
        assert TR_SELL == "kt10001"


class TestExceptions:
    def test_hierarchy(self):
        assert issubclass(AuthError, TradingError)
        assert issubclass(OrderError, TradingError)
        assert issubclass(RateLimitError, TradingError)


class TestTypes:
    def test_signal_creation(self):
        sig = Signal(
            stock_code="005930",
            action=SignalAction.ENTRY,
            side=OrderSide.BUY,
            reason="테스트",
            score=85.0,
        )
        assert sig.stock_code == "005930"
        assert sig.action == SignalAction.ENTRY

    def test_position_pnl(self):
        pos = Position(
            stock_code="005930",
            stock_name="삼성전자",
            strategy_name="test",
            qty=10,
            avg_price=80000,
            current_price=82000,
        )
        assert pos.unrealized_pnl == 20000
        assert pos.unrealized_pnl_pct == pytest.approx(2.5)

    def test_position_zero_avg_price(self):
        pos = Position(
            stock_code="005930",
            stock_name="삼성전자",
            strategy_name="test",
            qty=0,
            avg_price=0,
            current_price=0,
        )
        assert pos.unrealized_pnl_pct == 0.0

    def test_account_state_defaults(self):
        state = AccountState()
        assert state.total_equity == 0.0
        assert state.positions == []
        assert state.consecutive_losses == 0

    def test_enums(self):
        assert OrderSide.BUY.value == "buy"
        assert OrderType.MARKET.value == "market"
        assert AlertLevel.CRITICAL.value == "CRITICAL"
        assert MarketPhase.REGULAR.value == "regular"


class TestDatabase:
    async def test_create_tables(self, test_engine):
        async with test_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            )
            tables = [row[0] for row in result.fetchall()]
        assert "accounts" in tables
        assert "orders" in tables
        assert "fills" in tables
        assert "positions" in tables
        assert "daily_bars" in tables
        assert "minute_bars" in tables
        assert "signals" in tables
        assert "strategy_selections" in tables
        assert "scanner_rules" in tables
        assert "performance_reviews" in tables
        assert "backtest_runs" in tables
        assert "trading_calendar" in tables
        assert "slippage_stats" in tables

    async def test_session_works(self, test_session):
        result = await test_session.execute(text("SELECT 1"))
        assert result.scalar() == 1


class TestHealthEndpoint:
    async def test_health(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
