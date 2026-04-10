"""
텔레그램 봇 단독 실행 스크립트

사용법:
    python scripts/run_telegram.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.types import AlertLevel
from app.bot.telegram_bot import TelegramBot
from app.monitoring.alerts import AlertManager
from app.monitoring.health import HealthCheck


# 시가총액 상위 종목 (코드 → 이름)
STOCK_NAMES = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "035420": "NAVER",
    "035720": "카카오",
    "051910": "LG화학",
    "006400": "삼성SDI",
    "005380": "현대차",
    "000270": "기아",
    "068270": "셀트리온",
    "003670": "포스코퓨처엠",
    "105560": "KB금융",
    "055550": "신한지주",
    "028260": "삼성물산",
    "012330": "현대모비스",
    "066570": "LG전자",
}


async def run_scanner(scanner_name: str, progress_fn=None) -> str:
    """
    스캐너 실행 콜백.
    progress_fn: async def(text) — 중간 진행 상황을 텔레그램에 표시
    """
    from app.brokers.kiwoom.auth import KiwoomAuth
    from app.brokers.kiwoom.client import KiwoomClient
    from app.brokers.kiwoom.market_data import KiwoomMarketData
    from app.brokers.kiwoom.rate_limiter import RateLimiter
    from app.scanners.dsl import ScannerDSL
    import pandas as pd

    codes = list(STOCK_NAMES.keys())
    total = len(codes)

    auth = KiwoomAuth(settings.kiwoom_app_key, settings.kiwoom_app_secret, settings.kiwoom_base_url)
    await auth.get_token()
    rl = RateLimiter(max_calls_per_second=3)
    client = KiwoomClient(auth, rl, settings.kiwoom_base_url,
                          settings.kiwoom_app_key, settings.kiwoom_app_secret)
    md = KiwoomMarketData(client)

    bars = {}
    for i, code in enumerate(codes, 1):
        name = STOCK_NAMES.get(code, code)

        # 매 5개마다 진행 상황 업데이트
        if progress_fn and (i == 1 or i % 5 == 0 or i == total):
            await progress_fn(f"[{scanner_name}] {i}/{total} 스캔 중... ({name})")

        try:
            resp = await md.get_daily_bars(code, base_dt="20260410")
            if resp.get("return_code") == 0:
                key = "stk_dt_pole_chart_qry"
                if key in resp and resp[key]:
                    rows = []
                    for r in resp[key]:
                        rows.append({
                            "datetime": pd.to_datetime(r["dt"]),
                            "open": float(r["open_pric"]),
                            "high": float(r["high_pric"]),
                            "low": float(r["low_pric"]),
                            "close": float(r["cur_prc"]),
                            "volume": int(r["trde_qty"]),
                            "stock_code": code,
                        })
                    bars[code] = pd.DataFrame(rows).sort_values("datetime").reset_index(drop=True)
        except Exception:
            pass
        await asyncio.sleep(0.3)

    await client.close()

    scanner = ScannerDSL.get_scanner(scanner_name)
    results = scanner.scan(bars)

    if not results:
        return f"[{scanner_name}] 완료\n{len(bars)}개 종목 스캔\n\n후보 종목 없음"

    lines = [f"[{scanner_name}] 완료", f"{len(bars)}개 종목 스캔", ""]
    for i, r in enumerate(results[:10], 1):
        name = STOCK_NAMES.get(r.stock_code, "")
        reasons = ", ".join(r.reasons)
        lines.append(f"{i}. {r.stock_code} {name} ({r.score:.1f}점)")
        lines.append(f"   {reasons}")
    if len(results) > 10:
        lines.append(f"\n... 외 {len(results) - 10}개")
    return "\n".join(lines)


async def main():
    if not settings.telegram_bot_token:
        print("[ERROR] TELEGRAM_BOT_TOKEN not set in .env")
        return
    if not settings.telegram_chat_id:
        print("[ERROR] TELEGRAM_CHAT_ID not set in .env")
        return

    print(f"=== Telegram Bot ===")
    print(f"Token: {settings.telegram_bot_token[:15]}...")
    print(f"Chat ID: {settings.telegram_chat_id}")
    print()

    # 전략 import (레지스트리 자동 등록)
    import app.strategies.momentum_breakout
    import app.strategies.pullback_trend
    import app.strategies.mean_reversion
    import app.strategies.low_volatility_trend
    import app.strategies.multi_factor

    bot = TelegramBot(settings.telegram_bot_token, settings.telegram_chat_id)

    # 헬스체크 연결
    health = HealthCheck()
    health.set_strategy("multi_factor")
    health.set_scheduler_running(False)
    bot.handlers.health_check = health

    # 스캐너 콜백 연결 (progress_fn 지원)
    bot.handlers.scanner_fn = run_scanner

    # 알림 매니저 연결
    async def send_alert(text: str):
        await bot.send_message(text)

    alert_mgr = AlertManager(send_fn=send_alert,
                             warning_enabled=settings.alert_level_warning,
                             info_enabled=settings.alert_level_info)
    bot.handlers.alert_manager = alert_mgr

    # 봇 시작
    await bot.start()
    print("[OK] Bot started. Commands registered.")
    print("[OK] Listening for messages... (Ctrl+C to stop)")

    # 시작 알림
    from app.bot.keyboards import MAIN_MENU_KEYBOARD
    await bot.send_message(
        "Bot started.\n/help 로 명령어를 확인하세요.",
        reply_markup=MAIN_MENU_KEYBOARD,
    )

    # 무한 대기
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping bot...")
        await bot.stop()
        print("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
