"""텔레그램 봇 메인"""

from __future__ import annotations

from app.monitoring.logger import get_logger

log = get_logger("bot.telegram")


class TelegramBot:
    """텔레그램 봇 래퍼"""

    def __init__(self, token: str, chat_id: str):
        self._token = token
        self._chat_id = chat_id
        self._app = None

    async def send_message(self, text: str):
        """메시지 발송"""
        if not self._token or not self._chat_id:
            log.warning("telegram_not_configured")
            return

        try:
            from telegram import Bot
            bot = Bot(token=self._token)
            await bot.send_message(chat_id=self._chat_id, text=text)
            log.debug("telegram_sent", length=len(text))
        except Exception as e:
            log.error("telegram_send_failed", error=str(e))

    async def start(self):
        """봇 폴링 시작 (별도 태스크로 실행)"""
        if not self._token:
            log.warning("telegram_bot_not_started_no_token")
            return

        try:
            from telegram.ext import Application, CommandHandler

            self._app = Application.builder().token(self._token).build()

            # 핸들러는 handlers.py에서 등록
            log.info("telegram_bot_starting")
            await self._app.initialize()
            await self._app.start()
            await self._app.updater.start_polling()
        except Exception as e:
            log.error("telegram_bot_start_failed", error=str(e))

    async def stop(self):
        if self._app:
            try:
                await self._app.updater.stop()
                await self._app.stop()
                await self._app.shutdown()
            except Exception as e:
                log.error("telegram_bot_stop_failed", error=str(e))
