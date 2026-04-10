"""텔레그램 봇 메인 - 명령어 등록 및 폴링"""

from __future__ import annotations

from telegram import BotCommand
from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from app.bot.handlers import BotHandlers
from app.monitoring.logger import get_logger

log = get_logger("bot.telegram")

# BotFather에 등록할 명령어 목록 (자동완성용)
BOT_COMMANDS = [
    BotCommand("status", "봇 상태 및 계좌 요약"),
    BotCommand("positions", "보유 종목 조회"),
    BotCommand("strategies", "전략 선택/변경"),
    BotCommand("scan", "종목 스캐너 실행"),
    BotCommand("review", "성과 리뷰 조회"),
    BotCommand("control", "봇 시작/정지/긴급청산"),
    BotCommand("health", "시스템 헬스체크"),
    BotCommand("help", "명령어 안내"),
]


class TelegramBot:
    """텔레그램 봇 - 명령어 + 인라인 버튼 UI"""

    def __init__(self, token: str, chat_id: str):
        self._token = token
        self._chat_id = chat_id
        self._app: Application | None = None
        self.handlers = BotHandlers()

    async def send_message(self, text: str, reply_markup=None):
        if not self._token or not self._chat_id:
            log.warning("telegram_not_configured")
            return
        try:
            from telegram import Bot
            bot = Bot(token=self._token)
            await bot.send_message(
                chat_id=self._chat_id,
                text=text,
                reply_markup=reply_markup,
            )
        except Exception as e:
            log.error("telegram_send_failed", error=str(e))

    def _build_app(self) -> Application:
        app = Application.builder().token(self._token).build()

        h = self.handlers

        # 명령어 핸들러 등록
        app.add_handler(CommandHandler("start", h.cmd_start))
        app.add_handler(CommandHandler("help", h.cmd_help))
        app.add_handler(CommandHandler("status", h.cmd_status))
        app.add_handler(CommandHandler("positions", h.cmd_positions))
        app.add_handler(CommandHandler("strategies", h.cmd_strategies))
        app.add_handler(CommandHandler("scan", h.cmd_scan))
        app.add_handler(CommandHandler("review", h.cmd_review))
        app.add_handler(CommandHandler("control", h.cmd_control))
        app.add_handler(CommandHandler("health", h.cmd_health))

        # 인라인 버튼 콜백 핸들러
        app.add_handler(CallbackQueryHandler(h.handle_callback))

        return app

    async def start(self):
        """봇 폴링 시작"""
        if not self._token:
            log.warning("telegram_bot_not_started_no_token")
            return

        try:
            self._app = self._build_app()

            await self._app.initialize()

            # BotFather 명령어 자동완성 등록
            await self._app.bot.set_my_commands(BOT_COMMANDS)
            log.info("bot_commands_registered", count=len(BOT_COMMANDS))

            await self._app.start()
            await self._app.updater.start_polling(drop_pending_updates=True)
            log.info("telegram_bot_started")
        except Exception as e:
            log.error("telegram_bot_start_failed", error=str(e))

    async def stop(self):
        if self._app:
            try:
                await self._app.updater.stop()
                await self._app.stop()
                await self._app.shutdown()
                log.info("telegram_bot_stopped")
            except Exception as e:
                log.error("telegram_bot_stop_failed", error=str(e))
