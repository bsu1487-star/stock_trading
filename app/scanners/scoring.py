"""패턴 점수화 유틸"""

from __future__ import annotations


def normalize_score(value: float, min_val: float, max_val: float) -> float:
    """0~100 범위로 정규화"""
    if max_val <= min_val:
        return 0.0
    return max(0.0, min(100.0, (value - min_val) / (max_val - min_val) * 100))


def weighted_sum(scores: dict[str, float], weights: dict[str, float]) -> float:
    """가중 합산"""
    total = 0.0
    for key, score in scores.items():
        total += score * weights.get(key, 1.0)
    return total
