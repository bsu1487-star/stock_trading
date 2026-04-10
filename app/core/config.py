from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 키움 API
    kiwoom_app_key: str = ""
    kiwoom_app_secret: str = ""
    kiwoom_account_no: str = ""
    kiwoom_is_mock: bool = True

    # DB
    database_url: str = "sqlite+aiosqlite:///./data/trading.db"

    # 텔레그램
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # 리스크
    max_positions: int = 5
    max_daily_loss_pct: float = 2.0
    per_stock_weight_pct: float = 15.0
    stop_loss_pct: float = 3.0
    take_profit_pct: float = 5.0
    mdd_reduce_threshold_pct: float = 1.0
    mdd_stop_threshold_pct: float = 2.0

    # 스케줄
    scan_interval_minutes: int = 5

    # 알림 등급
    alert_level_warning: bool = True
    alert_level_info: bool = False

    # Rate Limit
    api_max_calls_per_second: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def kiwoom_base_url(self) -> str:
        if self.kiwoom_is_mock:
            return "https://mockapi.kiwoom.com"
        return "https://api.kiwoom.com"


settings = Settings()
