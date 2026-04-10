"""APScheduler 실행기"""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.monitoring.logger import get_logger

from .jobs import TradingJobs

log = get_logger("scheduler.runner")


class SchedulerRunner:
    """스케줄러 관리"""

    def __init__(self, jobs: TradingJobs, scan_interval_minutes: int = 5):
        self._jobs = jobs
        self._scan_interval = scan_interval_minutes
        self._scheduler = AsyncIOScheduler()
        self._running = False

    def setup(self):
        """스케줄 등록"""
        # 장전 준비
        self._scheduler.add_job(self._jobs.pre_market, "cron", hour=8, minute=30, id="pre_market")

        # 장중 스캔 (09:15~14:55, N분 주기)
        self._scheduler.add_job(
            self._jobs.scan_cycle,
            "cron",
            hour="9-14",
            minute=f"*/{self._scan_interval}",
            id="scan_cycle",
        )

        # 미체결 점검 (09:00~15:20, 1분 주기)
        self._scheduler.add_job(
            self._jobs.pending_check,
            "cron",
            hour="9-15",
            minute="*",
            id="pending_check",
        )

        # 장 마감 처리
        self._scheduler.add_job(self._jobs.market_close, "cron", hour=15, minute=0, id="market_close")

        # 장 마감 후
        self._scheduler.add_job(self._jobs.post_market, "cron", hour=15, minute=35, id="post_market")

        # 일간 리뷰
        self._scheduler.add_job(self._jobs.daily_review, "cron", hour=16, minute=0, id="daily_review")

    def start(self):
        if not self._running:
            self._scheduler.start()
            self._running = True
            log.info("scheduler_started")

    def stop(self):
        if self._running:
            self._scheduler.shutdown(wait=False)
            self._running = False
            log.info("scheduler_stopped")

    @property
    def is_running(self) -> bool:
        return self._running
