"""Time estimation → Time Awareness Fischer L.

미러 (변경 금지) — 원본: bnm-learning-engine/ml/mappings/time_est.py.
"""

from typing import TypedDict, Optional
from measurement_mappings._fischer import FischerLevel


class TimeEstimationRawScore(TypedDict):
    one_min_error_pct: float  # % error (1분 추정)
    five_min_error_pct: Optional[float]  # 5분 추정 (선택)
    fifteen_min_error_pct: Optional[float]
    schedule_accuracy_pct: Optional[float]  # 일정 vs 실제 (지난 주)


def time_estimation_to_time_awareness_l(score: TimeEstimationRawScore) -> FischerLevel:
    """시간 추정 → Time Awareness L7-L13.

    ⭐ Default 박힘.
    """
    one_min = score['one_min_error_pct']
    five_min = score.get('five_min_error_pct')
    fifteen_min = score.get('fifteen_min_error_pct')
    schedule = score.get('schedule_accuracy_pct')

    # 1분 추정 자리 (short timescale)
    if one_min < 5:
        short_l = 11.0
    elif one_min < 10:
        short_l = 10.0
    elif one_min < 15:
        short_l = 9.0
    elif one_min < 25:
        short_l = 8.0
    elif one_min < 40:
        short_l = 7.5
    else:
        short_l = 7.0

    # 5분 추정 자리 (mid timescale)
    if five_min is not None:
        if five_min < 8:
            mid_l = 10.0
        elif five_min < 15:
            mid_l = 9.0
        elif five_min < 25:
            mid_l = 8.5
        elif five_min < 40:
            mid_l = 8.0
        else:
            mid_l = 7.5
    else:
        mid_l = None

    # Schedule accuracy 자리 (long timescale, real-world)
    if schedule is not None:
        if schedule > 90:
            long_l = 11.0
        elif schedule > 80:
            long_l = 10.0
        elif schedule > 70:
            long_l = 9.0
        elif schedule > 60:
            long_l = 8.5
        elif schedule > 50:
            long_l = 8.0
        else:
            long_l = 7.5
    else:
        long_l = None

    # Composite 박힘
    levels = [short_l]
    weights = [0.4]
    if mid_l is not None:
        levels.append(mid_l)
        weights.append(0.3)
    if long_l is not None:
        levels.append(long_l)
        weights.append(0.4)

    weight_sum = sum(weights)
    weighted_l = sum(l * w for l, w in zip(levels, weights)) / weight_sum

    final_l = max(7.0, min(13.0, round(weighted_l, 1)))

    # Confidence 박힘
    n_measures = sum([1 for x in [one_min, five_min, fifteen_min, schedule] if x is not None])
    if n_measures >= 3:
        confidence = 0.85
    elif n_measures >= 2:
        confidence = 0.75
    else:
        confidence = 0.6

    markers = []
    if one_min < 10:
        markers.append("excellent_short_time_estimation")
    if schedule is not None and schedule > 85:
        markers.append("strong_schedule_adherence")
    if one_min > 30:
        markers.append("time_awareness_difficulty_suspected")

    return FischerLevel(
        level=final_l,
        confidence=confidence,
        markers_matched=markers,
    )
