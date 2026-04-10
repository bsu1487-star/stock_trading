"""스케줄 작업 정의"""

from __future__ import annotations

from app.monitoring.logger import get_logger

log = get_logger("scheduler.jobs")


class TradingJobs:
    """거래 스케줄 작업"""

    def __init__(self, engine=None, health_check=None, alert_manager=None):
        self.engine = engine
        self.health_check = health_check
        self.alert_manager = alert_manager

    async def pre_market(self):
        """08:30 - 토큰 확보, 계좌 조회, 유니버스 준비"""
        log.info("job_pre_market")

    async def scan_cycle(self):
        """09:15~15:00 - 5분 주기 스캔 및 주문"""
        log.info("job_scan_cycle")
        if self.health_check:
            self.health_check.record_scan()

    async def pending_check(self):
        """장중 1분 주기 - 미체결 점검"""
        log.info("job_pending_check")

    async def market_close(self):
        """15:00~15:20 - 당일 청산 전략 포지션 정리"""
        log.info("job_market_close")

    async def post_market(self):
        """15:30 이후 - 로그 저장, 성과 리포트, 분봉 수집"""
        log.info("job_post_market")

    async def daily_review(self):
        """장 종료 후 - 일간 성과리뷰 생성"""
        log.info("job_daily_review")
