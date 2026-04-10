from __future__ import annotations

from app.strategies.base import Strategy


class StrategyRegistry:
    """전략 등록/조회"""

    _strategies: dict[str, type[Strategy]] = {}

    @classmethod
    def register(cls, strategy_cls: type[Strategy]):
        cls._strategies[strategy_cls.name] = strategy_cls
        return strategy_cls

    @classmethod
    def get(cls, name: str) -> type[Strategy]:
        if name not in cls._strategies:
            raise KeyError(f"전략 '{name}' 이 등록되어 있지 않습니다. 등록: {list(cls._strategies.keys())}")
        return cls._strategies[name]

    @classmethod
    def list_all(cls) -> list[str]:
        return list(cls._strategies.keys())

    @classmethod
    def create(cls, name: str, **kwargs) -> Strategy:
        return cls.get(name)(**kwargs)
