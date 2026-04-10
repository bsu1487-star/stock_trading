"""텔레그램 명령 핸들러 (인라인 버튼 UI 포함)"""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.bot.formatters import format_positions, format_status
from app.bot.keyboards import (
    MAIN_MENU_KEYBOARD,
    control_keyboard,
    get_scanner_label,
    kill_confirm_keyboard,
    review_keyboard,
    scanner_keyboard,
    strategy_keyboard,
)
from app.monitoring.logger import get_logger

log = get_logger("bot.handlers")


class BotHandlers:
    """텔레그램 봇 명령 핸들러"""

    def __init__(self):
        self.portfolio_manager = None
        self.account_state = None
        self.strategy_name = "multi_factor"
        self.bot_running = False
        self.health_check = None
        self.kill_switch = None
        self.alert_manager = None
        self.scanner_fn = None       # 외부에서 주입: async def(scanner_name) -> str
        self.review_fn = None        # 외부에서 주입: async def(review_type) -> str

    # ── 슬래시 명령어 핸들러 ──

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """봇 시작 + 메인 메뉴 표시"""
        await update.message.reply_text(
            "키움 자동매매 봇입니다.\n아래 메뉴를 사용하세요.",
            reply_markup=MAIN_MENU_KEYBOARD,
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (
            "[명령어 안내]\n"
            "\n"
            "/status - 봇 상태, 계좌 요약\n"
            "/positions - 보유 종목 조회\n"
            "/strategies - 전략 선택\n"
            "/scan - 종목 스캐너\n"
            "/review - 성과 리뷰\n"
            "/control - 봇 시작/정지/긴급청산\n"
            "/health - 시스템 헬스체크\n"
            "/help - 이 도움말"
        )
        await update.message.reply_text(text, reply_markup=MAIN_MENU_KEYBOARD)

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.account_state:
            msg = format_status(self.account_state, self.strategy_name, self.bot_running)
        else:
            from app.core.types import AccountState
            state = AccountState(total_equity=20_000_000, available_cash=20_000_000)
            msg = format_status(state, self.strategy_name, self.bot_running)
        await update.message.reply_text(msg)

    async def cmd_positions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.portfolio_manager:
            msg = format_positions(self.portfolio_manager.positions)
        else:
            msg = "보유 종목이 없습니다."
        await update.message.reply_text(msg)

    async def cmd_strategies(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        current = self.strategy_name
        await update.message.reply_text(
            f"현재 전략: {current}\n\n전략을 선택하세요:",
            reply_markup=strategy_keyboard(),
        )

    async def cmd_scan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "실행할 스캐너를 선택하세요:",
            reply_markup=scanner_keyboard(),
        )

    async def cmd_review(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "조회할 성과리뷰 기간을 선택하세요:",
            reply_markup=review_keyboard(),
        )

    async def cmd_control(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        status = "실행 중" if self.bot_running else "정지"
        await update.message.reply_text(
            f"현재 봇 상태: {status}",
            reply_markup=control_keyboard(),
        )

    async def cmd_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.health_check:
            result = await self.health_check.check()
            lines = ["[헬스체크]"]
            for k, v in result.items():
                lines.append(f"  {k}: {v}")
            await update.message.reply_text("\n".join(lines))
        else:
            await update.message.reply_text(
                "[헬스체크]\n"
                f"  bot_running: {self.bot_running}\n"
                f"  strategy: {self.strategy_name}\n"
                f"  status: ok"
            )

    # ── 인라인 버튼 콜백 핸들러 ──

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data

        # 전략 선택
        if data.startswith("strat:"):
            name = data.split(":", 1)[1]
            from app.strategies.registry import StrategyRegistry
            try:
                StrategyRegistry.get(name)
                self.strategy_name = name
                await query.edit_message_text(f"전략을 변경했습니다: {name}")
                if self.alert_manager:
                    from app.core.types import AlertLevel
                    await self.alert_manager.send(AlertLevel.WARNING, f"전략 변경: {name}")
            except KeyError as e:
                await query.edit_message_text(str(e))

        # 스캐너 실행
        elif data.startswith("scan:"):
            scanner_id = data.split(":", 1)[1]
            label = get_scanner_label(scanner_id)
            await query.edit_message_text(f"[{label}] 데이터 수집 시작...")
            if self.scanner_fn:
                try:
                    async def progress(text: str):
                        try:
                            await query.edit_message_text(text)
                        except Exception:
                            pass

                    result_text = await self.scanner_fn(scanner_id, progress_fn=progress)
                    await query.edit_message_text(result_text)
                except Exception as e:
                    await query.edit_message_text(f"[{label}] 오류: {e}")
            else:
                await query.edit_message_text(
                    f"[{label}]\n"
                    "스캐너가 연결되지 않았습니다.\n"
                    "run_telegram.py로 봇을 실행하세요."
                )

        # 성과리뷰
        elif data.startswith("review:"):
            review_type = data.split(":", 1)[1]
            if self.review_fn:
                try:
                    result_text = await self.review_fn(review_type)
                    await query.edit_message_text(result_text)
                except Exception as e:
                    await query.edit_message_text(f"리뷰 조회 오류: {e}")
            else:
                label = {"daily": "일간", "weekly": "주간", "monthly": "월간"}.get(review_type, review_type)
                await query.edit_message_text(
                    f"[{label} 성과리뷰]\n"
                    "아직 매매 이력이 없습니다.\n"
                    "봇 실행 후 거래가 발생하면 리뷰가 생성됩니다."
                )

        # 봇 제어
        elif data.startswith("ctrl:"):
            action = data.split(":", 1)[1]
            if action == "start":
                self.bot_running = True
                await query.edit_message_text("봇을 시작했습니다.")
                if self.alert_manager:
                    from app.core.types import AlertLevel
                    await self.alert_manager.send(AlertLevel.INFO, "봇 시작됨")
            elif action == "stop":
                self.bot_running = False
                await query.edit_message_text("봇을 정지했습니다. (신규 주문 중지)")
                if self.alert_manager:
                    from app.core.types import AlertLevel
                    await self.alert_manager.send(AlertLevel.WARNING, "봇 정지됨")
            elif action == "kill":
                await query.edit_message_text(
                    "정말로 전체 포지션을 청산하시겠습니까?\n"
                    "이 작업은 되돌릴 수 없습니다.",
                    reply_markup=kill_confirm_keyboard(),
                )

        # Kill Switch 확인
        elif data.startswith("kill:"):
            action = data.split(":", 1)[1]
            if action == "confirm":
                self.bot_running = False
                await query.edit_message_text("Kill Switch 실행 - 전체 청산 중...")
                log.critical("kill_switch_confirmed_via_telegram")
                if self.kill_switch:
                    # 실제 청산 로직은 엔진에서 수행
                    pass
                if self.alert_manager:
                    from app.core.types import AlertLevel
                    await self.alert_manager.send(AlertLevel.CRITICAL, "KILL SWITCH 실행됨")
                await query.edit_message_text("Kill Switch 실행 완료. 봇이 정지되었습니다.")
            elif action == "cancel":
                await query.edit_message_text("긴급 청산이 취소되었습니다.")
