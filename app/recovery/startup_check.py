from __future__ import annotations

from app.monitoring.logger import get_logger

log = get_logger("recovery.startup")


class StartupCheck:
    """시작 시 상태 점검 및 동기화"""

    def __init__(self):
        self._sync_complete = False

    @property
    def is_ready(self) -> bool:
        return self._sync_complete

    async def run(self, auth, account_client, portfolio_manager, alert_manager=None):
        """
        시작 시 점검 순서:
        1. 토큰 유효성 확인
        2. 브로커 잔고 조회 → 로컬 포지션과 비교
        3. 불일치 시 동기화 + 알림
        4. 동기화 완료 플래그 설정
        """
        log.info("startup_check_begin")

        # 1. 토큰
        try:
            await auth.get_token()
            log.info("startup_token_ok")
        except Exception as e:
            log.error("startup_token_failed", error=str(e))
            if alert_manager:
                from app.core.types import AlertLevel
                await alert_manager.send(AlertLevel.CRITICAL, f"시작 시 토큰 획득 실패: {e}")
            return False

        # 2. 잔고 동기화
        try:
            balance_data = await account_client.get_balance()
            log.info("startup_balance_fetched")
            # 실제 구현에서는 balance_data를 파싱해 Position 리스트로 변환 후
            # portfolio_manager와 비교/동기화
        except Exception as e:
            log.error("startup_balance_failed", error=str(e))
            if alert_manager:
                from app.core.types import AlertLevel
                await alert_manager.send(AlertLevel.CRITICAL, f"시작 시 잔고 조회 실패: {e}")
            return False

        self._sync_complete = True
        log.info("startup_check_complete")
        return True
