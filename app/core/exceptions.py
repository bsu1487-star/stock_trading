class TradingError(Exception):
    """자동매매 시스템 기본 예외"""


class AuthError(TradingError):
    """인증/토큰 관련 예외"""


class OrderError(TradingError):
    """주문 관련 예외"""


class RateLimitError(TradingError):
    """API 호출 제한 초과"""


class RiskLimitError(TradingError):
    """리스크 한도 초과"""


class RecoveryError(TradingError):
    """장애 복구 중 오류"""


class DataError(TradingError):
    """데이터 수집/처리 오류"""
