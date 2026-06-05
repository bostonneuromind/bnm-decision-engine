"""N-back → Working Memory Fischer L.

미러 (변경 금지) — 원본: bnm-learning-engine/ml/mappings/nback.py.
"""

from typing import TypedDict, Optional
from measurement_mappings._fischer import FischerLevel


class NBackRawScore(TypedDict):
    n_level: int           # 1, 2, 3
    accuracy: float        # 0.0-1.0
    false_alarm_rate: float
    rt_mean: float


def nback_to_working_memory_l(score: NBackRawScore) -> FischerLevel:
    """N-back → WM L7-L13.

    ⭐ Default 박힘. 사부 catch 자리:
    - Digit Span 통합 (forward + backward)
    - Reading Span 통합
    - n_level 별 weighting 자리
    """
    n = score['n_level']
    acc = score['accuracy']
    fa = score['false_alarm_rate']

    # Composite d-prime 박힘 (signal detection 자리)
    # d' = z(hit_rate) - z(false_alarm_rate)
    # 간소화: acc - fa

    signal = acc - fa

    # n_level + signal 박힘
    if n == 1:
        if signal >= 0.85:
            base_l = 8.5
        elif signal >= 0.70:
            base_l = 8.0
        elif signal >= 0.50:
            base_l = 7.5
        else:
            base_l = 7.0
    elif n == 2:
        if signal >= 0.85:
            base_l = 10.5
        elif signal >= 0.70:
            base_l = 9.5
        elif signal >= 0.50:
            base_l = 9.0
        elif signal >= 0.30:
            base_l = 8.0
        else:
            base_l = 7.5
    elif n == 3:
        if signal >= 0.80:
            base_l = 12.0
        elif signal >= 0.60:
            base_l = 11.0
        elif signal >= 0.40:
            base_l = 10.0
        else:
            base_l = 9.0
    else:
        base_l = 9.0  # default

    final_l = max(7.0, min(13.0, round(base_l, 1)))

    # Confidence 박힘
    confidence = 0.75 if n >= 2 else 0.65

    markers = []
    if signal >= 0.80:
        markers.append("strong_wm")
    if n >= 2 and acc >= 0.75:
        markers.append("dual_back_competent")
    if fa > 0.30:
        markers.append("high_false_alarm")

    return FischerLevel(
        level=final_l,
        confidence=confidence,
        markers_matched=markers,
    )


def digit_span_to_wm_l(
    forward: int,
    backward: int
) -> FischerLevel:
    """Digit Span → WM L. Secondary 자리."""
    # Forward weight 0.4, backward weight 0.6 (backward = 더 어려움)
    weighted = forward * 0.4 + backward * 0.6

    if weighted >= 8.5:
        l = 12.0
    elif weighted >= 7.5:
        l = 11.0
    elif weighted >= 6.5:
        l = 10.0
    elif weighted >= 5.5:
        l = 9.0
    elif weighted >= 4.5:
        l = 8.5
    elif weighted >= 3.5:
        l = 8.0
    else:
        l = 7.0

    return FischerLevel(
        level=l,
        confidence=0.65,
        markers_matched=["digit_span_measured"],
    )


def combine_wm_measures(
    nback_l: Optional[FischerLevel] = None,
    digit_span_l: Optional[FischerLevel] = None,
) -> FischerLevel:
    """N-back + Digit Span 통합."""
    if nback_l and digit_span_l:
        # N-back weight 0.7 (more reliable for adults)
        combined_level = nback_l.level * 0.7 + digit_span_l.level * 0.3
        combined_conf = (nback_l.confidence + digit_span_l.confidence) / 2 + 0.1
        return FischerLevel(
            level=round(combined_level, 1),
            confidence=min(0.9, combined_conf),
            markers_matched=list(set(nback_l.markers_matched + digit_span_l.markers_matched)),
        )
    elif nback_l:
        return nback_l
    elif digit_span_l:
        return digit_span_l
    else:
        return FischerLevel(level=9.0, confidence=0.3)  # 측정 없음
