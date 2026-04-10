"""
통합 검증 스크립트
실제 키움 모의투자 API + 텔레그램 봇 연동을 단계별로 검증한다.
"""

import asyncio
import sys
import os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings


# ── 유틸 ──

def header(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def ok(msg: str):
    print(f"  [OK] {msg}")


def fail(msg: str):
    print(f"  [FAIL] {msg}")


def info(msg: str):
    print(f"  [INFO] {msg}")


# ── Step 1: 설정 확인 ──

def step1_check_config():
    header("Step 1. 환경 설정 확인")
    errors = []

    if not settings.kiwoom_app_key:
        errors.append("KIWOOM_APP_KEY 미설정")
    else:
        ok(f"KIWOOM_APP_KEY: {settings.kiwoom_app_key[:8]}...")

    if not settings.kiwoom_app_secret:
        errors.append("KIWOOM_APP_SECRET 미설정")
    else:
        ok(f"KIWOOM_APP_SECRET: {settings.kiwoom_app_secret[:8]}...")

    if not settings.kiwoom_account_no:
        errors.append("KIWOOM_ACCOUNT_NO 미설정")
    else:
        ok(f"KIWOOM_ACCOUNT_NO: {settings.kiwoom_account_no}")

    ok(f"KIWOOM_IS_MOCK: {settings.kiwoom_is_mock}")
    ok(f"BASE_URL: {settings.kiwoom_base_url}")

    if settings.telegram_bot_token:
        ok(f"TELEGRAM_BOT_TOKEN: {settings.telegram_bot_token[:15]}...")
    else:
        info("TELEGRAM_BOT_TOKEN 미설정 (봇 비활성)")

    if settings.telegram_chat_id:
        ok(f"TELEGRAM_CHAT_ID: {settings.telegram_chat_id}")
    else:
        info("TELEGRAM_CHAT_ID 미설정 (알림 비활성)")

    if errors:
        for e in errors:
            fail(e)
        return False
    return True


# ── Step 2: 토큰 발급 ──

async def step2_token():
    header("Step 2. 키움 API 토큰 발급")
    from app.brokers.kiwoom.auth import KiwoomAuth

    auth = KiwoomAuth(
        app_key=settings.kiwoom_app_key,
        app_secret=settings.kiwoom_app_secret,
        base_url=settings.kiwoom_base_url,
    )

    try:
        token = await auth.get_token()
        ok(f"토큰 발급 성공: {token[:20]}...")
        ok(f"만료 예정: {auth._expires_at}")
        return auth
    except Exception as e:
        fail(f"토큰 발급 실패: {e}")
        return None


# ── Step 3: 계좌 조회 ──

async def step3_account(auth):
    header("Step 3. 계좌 조회 (예수금 + 잔고 + 미체결)")
    from app.brokers.kiwoom.client import KiwoomClient
    from app.brokers.kiwoom.account import KiwoomAccount
    from app.brokers.kiwoom.rate_limiter import RateLimiter

    rl = RateLimiter(max_calls_per_second=settings.api_max_calls_per_second)
    client = KiwoomClient(auth, rl, settings.kiwoom_base_url,
                          app_key=settings.kiwoom_app_key, app_secret=settings.kiwoom_app_secret)
    account = KiwoomAccount(client, settings.kiwoom_account_no)

    # 예수금
    try:
        deposit = await account.get_deposit()
        ok(f"예수금 조회 성공")
        info(f"응답 키: {list(deposit.keys()) if isinstance(deposit, dict) else type(deposit)}")
        if isinstance(deposit, dict):
            # 응답 구조 출력 (일부)
            for k, v in list(deposit.items())[:5]:
                info(f"  {k}: {str(v)[:100]}")
    except Exception as e:
        fail(f"예수금 조회 실패: {e}")

    # 잔고
    try:
        balance = await account.get_balance()
        ok(f"잔고 조회 성공")
        if isinstance(balance, dict):
            for k, v in list(balance.items())[:5]:
                info(f"  {k}: {str(v)[:100]}")
    except Exception as e:
        fail(f"잔고 조회 실패: {e}")

    # 미체결
    try:
        pending = await account.get_pending_orders()
        ok(f"미체결 조회 성공")
        if isinstance(pending, dict):
            for k, v in list(pending.items())[:5]:
                info(f"  {k}: {str(v)[:100]}")
    except Exception as e:
        fail(f"미체결 조회 실패: {e}")

    await client.close()
    return client, account


# ── Step 4: 차트 데이터 조회 ──

async def step4_market_data(auth):
    header("Step 4. 시장 데이터 조회 (삼성전자 일봉/분봉)")
    from app.brokers.kiwoom.client import KiwoomClient
    from app.brokers.kiwoom.market_data import KiwoomMarketData
    from app.brokers.kiwoom.rate_limiter import RateLimiter

    rl = RateLimiter(max_calls_per_second=settings.api_max_calls_per_second)
    client = KiwoomClient(auth, rl, settings.kiwoom_base_url,
                          app_key=settings.kiwoom_app_key, app_secret=settings.kiwoom_app_secret)
    md = KiwoomMarketData(client)

    # 일봉
    try:
        daily = await md.get_daily_bars("005930", base_dt="20260410")
        ok(f"삼성전자 일봉 조회 성공")
        if isinstance(daily, dict):
            for k, v in list(daily.items())[:5]:
                info(f"  {k}: {str(v)[:120]}")
    except Exception as e:
        fail(f"일봉 조회 실패: {e}")

    # 분봉
    try:
        minute = await md.get_minute_bars("005930", interval=5, count=5)
        ok(f"삼성전자 5분봉 조회 성공")
        if isinstance(minute, dict):
            for k, v in list(minute.items())[:5]:
                info(f"  {k}: {str(v)[:120]}")
    except Exception as e:
        fail(f"분봉 조회 실패: {e}")

    await client.close()


# ── Step 5: 텔레그램 봇 검증 ──

async def step5_telegram():
    header("Step 5. 텔레그램 봇 검증")

    if not settings.telegram_bot_token:
        info("TELEGRAM_BOT_TOKEN 미설정 - 건너뜀")
        return

    import httpx

    # 5-1. getMe로 봇 정보 확인
    try:
        async with httpx.AsyncClient() as http:
            resp = await http.get(f"https://api.telegram.org/bot{settings.telegram_bot_token}/getMe")
            data = resp.json()
        if data.get("ok"):
            bot_info = data["result"]
            ok(f"봇 이름: {bot_info.get('first_name')}")
            ok(f"봇 username: @{bot_info.get('username')}")
        else:
            fail(f"봇 정보 조회 실패: {data}")
            return
    except Exception as e:
        fail(f"봇 정보 조회 실패: {e}")
        return

    # 5-2. chat_id가 숫자인지 확인, 아니면 getUpdates로 찾기
    chat_id = settings.telegram_chat_id
    if not chat_id.lstrip("-").isdigit():
        info(f"TELEGRAM_CHAT_ID '{chat_id}'가 숫자가 아닙니다. getUpdates로 실제 chat_id를 찾습니다...")
        try:
            async with httpx.AsyncClient() as http:
                resp = await http.get(f"https://api.telegram.org/bot{settings.telegram_bot_token}/getUpdates")
                data = resp.json()
            if data.get("ok") and data.get("result"):
                for update in data["result"]:
                    msg = update.get("message", {})
                    chat = msg.get("chat", {})
                    if chat.get("id"):
                        chat_id = str(chat["id"])
                        ok(f"실제 chat_id 발견: {chat_id}")
                        info(f"채팅 유형: {chat.get('type')}, 이름: {chat.get('first_name', chat.get('title', ''))}")
                        info(f".env의 TELEGRAM_CHAT_ID를 '{chat_id}'로 변경하세요.")
                        break
                else:
                    fail("getUpdates에서 메시지를 찾을 수 없습니다.")
                    info("봇에게 먼저 아무 메시지를 보낸 뒤 다시 실행하세요.")
                    return
            else:
                fail(f"getUpdates 실패: {data}")
                return
        except Exception as e:
            fail(f"getUpdates 실패: {e}")
            return

    # 5-3. 테스트 메시지 발송
    try:
        async with httpx.AsyncClient() as http:
            resp = await http.post(
                f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": "[kiwoom autotrading] integration verify test message.\nsystem is connected to telegram successfully.",
                },
            )
            data = resp.json()
        if data.get("ok"):
            ok(f"테스트 메시지 발송 성공 (chat_id: {chat_id})")
        else:
            fail(f"메시지 발송 실패: {data.get('description', data)}")
    except Exception as e:
        fail(f"메시지 발송 실패: {e}")


# ── Step 6: DB 초기화 확인 ──

async def step6_db():
    header("Step 6. DB 초기화 확인")
    from app.storage.database import init_db, engine
    from sqlalchemy import text

    try:
        await init_db()
        ok("DB 테이블 생성 완료")

        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            )
            tables = [row[0] for row in result.fetchall()]
        ok(f"생성된 테이블 수: {len(tables)}")
        info(f"테이블 목록: {', '.join(tables[:10])}{'...' if len(tables) > 10 else ''}")
    except Exception as e:
        fail(f"DB 초기화 실패: {e}")


# ── 메인 ──

async def main():
    print("\n" + ">>> kiwoom autotrading integration verify start")
    print(f"   환경: {'모의투자' if settings.kiwoom_is_mock else '실거래'}")

    # Step 1
    if not step1_check_config():
        print("\n[STOP] config error. verify aborted.")
        return

    # Step 2
    auth = await step2_token()
    if not auth:
        print("\n[STOP] token failed. skipping kiwoom api steps.")
        # 텔레그램/DB는 계속 검증
        await step5_telegram()
        await step6_db()
        header("검증 결과 요약")
        fail("키움 API 연동 실패 - 토큰 발급 단계에서 중단")
        return

    # Step 3
    await step3_account(auth)

    # Step 4
    await step4_market_data(auth)

    # Step 5
    await step5_telegram()

    # Step 6
    await step6_db()

    header("검증 완료")
    print("  check results above. fix [FAIL] items.\n")


if __name__ == "__main__":
    asyncio.run(main())
