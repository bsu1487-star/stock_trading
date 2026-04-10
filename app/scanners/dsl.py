"""YAML 조건 기반 스캐너 DSL 파서"""

from __future__ import annotations

from dataclasses import dataclass, field

import yaml

from app.scanners.builtin.bottom_rebound import BottomReboundScanner
from app.scanners.builtin.c_spot import CSpotScanner
from app.scanners.builtin.double_bottom import DoubleBottomScanner
from app.scanners.builtin.first_pullback import FirstPullbackScanner
from app.scanners.builtin.ma_recovery import MARecoveryScanner
from app.scanners.builtin.pullback_reentry import PullbackReentryScanner
from app.scanners.builtin.volume_breakout import VolumeBreakoutScanner

BUILTIN_SCANNERS = {
    "volume_breakout": VolumeBreakoutScanner,
    "bottom_rebound": BottomReboundScanner,
    "ma_recovery": MARecoveryScanner,
    "double_bottom": DoubleBottomScanner,
    "pullback_reentry": PullbackReentryScanner,
    "first_pullback": FirstPullbackScanner,
    "c_spot": CSpotScanner,
}


@dataclass
class ScannerConfig:
    scanner_name: str
    market: str = "KRX"
    timeframe: str = "5m"
    filters: dict = field(default_factory=dict)
    conditions: list = field(default_factory=list)
    ranking: list = field(default_factory=list)


class ScannerDSL:
    """YAML 조건 파서"""

    @staticmethod
    def load(path: str) -> ScannerConfig:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return ScannerConfig(
            scanner_name=data.get("scanner_name", ""),
            market=data.get("market", "KRX"),
            timeframe=data.get("timeframe", "5m"),
            filters=data.get("filters", {}),
            conditions=data.get("conditions", []),
            ranking=data.get("ranking", []),
        )

    @staticmethod
    def load_from_string(yaml_str: str) -> ScannerConfig:
        data = yaml.safe_load(yaml_str)
        return ScannerConfig(
            scanner_name=data.get("scanner_name", ""),
            market=data.get("market", "KRX"),
            timeframe=data.get("timeframe", "5m"),
            filters=data.get("filters", {}),
            conditions=data.get("conditions", []),
            ranking=data.get("ranking", []),
        )

    @staticmethod
    def get_scanner(name: str):
        cls = BUILTIN_SCANNERS.get(name)
        if cls is None:
            raise KeyError(f"스캐너 '{name}' 이 등록되어 있지 않습니다. 등록: {list(BUILTIN_SCANNERS.keys())}")
        return cls()

    @staticmethod
    def list_scanners() -> list[str]:
        return list(BUILTIN_SCANNERS.keys())
