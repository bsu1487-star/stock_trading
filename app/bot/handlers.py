"""텔레그램 명령 핸들러"""

from __future__ import annotations

from app.bot.formatters import format_daily_review, format_positions, format_status
from app.monitoring.logger import get_logger

log = get_logger("bot.handlers")


class BotHandlers:
    """텔레그램 봇 명령 핸들러 (의존성은 외부에서 주입)"""

    def __init__(self):
        self.portfolio_manager = None
        self.account_state = None
        self.strategy_name = ""
        self.bot_running = False
        self.health_check = None
        self.kill_switch = None
        self.alert_manager = None
        self._send_fn = None

    def set_send_fn(self, fn):
        self._send_fn = fn

    async def _reply(self, text: str):
        if self._send_fn:
            await self._send_fn(text)

    async def cmd_status(self):
        if self.account_state:
            msg = format_status(self.account_state, self.strategy_name, self.bot_running)
        else:
            msg = "계좌 상태를 불러올 수 없습니다."
        await self._reply(msg)

    async def cmd_positions(self):
        if self.portfolio_manager:
            msg = format_positions(self.portfolio_manager.positions)
        else:
            msg = "포트폴리오 정보가 없습니다."
        await self._reply(msg)

    async def cmd_strategies(self):
        from app.strategies.registry import StrategyRegistry
        names = StrategyRegistry.list_all()
        msg = "[사용 가능한 전략]\n" + "\n".join(f"  - {n}" for n in names)
        await self._reply(msg)

    async def cmd_strategy_set(self, name: str):
        from app.strategies.registry import StrategyRegistry
        try:
            StrategyRegistry.get(name)
            self.strategy_name = name
            await self._reply(f"전략을 '{name}'(으)로 변경했습니다.")
        except KeyError as e:
            await self._reply(str(e))

    async def cmd_health(self):
        if self.health_check:
            result = await self.health_check.check()
            lines = [f"[헬스체크]"]
            for k, v in result.items():
                lines.append(f"  {k}: {v}")
            await self._reply("\n".join(lines))
        else:
            await self._reply("헬스체크를 사용할 수 없습니다.")

    async def cmd_kill_all(self):
        if self.kill_switch:
            await self._reply("긴급 청산을 실행합니다...")
            # 실제 청산은 엔진 레이어에서 수행
            log.critical("kill_all_requested_via_telegram")
            await self._reply("Kill Switch가 활성화되었습니다.")
        else:
            await self._reply("Kill Switch를 사용할 수 없습니다.")
