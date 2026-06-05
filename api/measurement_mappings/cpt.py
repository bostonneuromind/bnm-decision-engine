"""CPT (Continuous Performance Task) → Sustained Attention Fischer L.

미러 (변경 금지) — 원본: bnm-learning-engine/ml/mappings/cpt.py.
변환 로직은 learning repo가 원본. import 경로만 미러용으로 교체.
Reference: curator/mapping-tables/01-cpt-to-sustained-attention.md
"""

from typing import TypedDict
from measurement_mappings._fischer import FischerLevel


class CPTRawScore(TypedDict):
    accuracy: float       # 0.0-1.0 (omissions + commissions 자리 박힘)
    rt_mean: float        # ms
    rt_cv: float          # coefficient of variation (variability)
    duration_min: float   # 측정 시간


def cpt_to_sustained_attention_l(score: CPTRawScore) -> FischerLevel:
    """CPT raw → Fischer L7-L13.

    ⭐ Default 박힘. 사부 catch + 박을 자리:
    - Mitsar vs HBImed 자리 (둘 다 normative 박힘)
    - First measurement vs longitudinal 가중치
    - Age/gender adjustment 자리
    - RT_CV (variability) 가중치

    See curator/mapping-tables/01-cpt-to-sustained-attention.md
    """
    accuracy = score['accuracy']
    rt_cv = score['rt_cv']
    rt_mean = score['rt_mean']

    # Composite score 박힘
    # Accuracy 자리 (가장 큰 weight, MEDA 0.4)
    if accuracy >= 0.95:
        acc_l = 11.5
    elif accuracy >= 0.92:
        acc_l = 11.0
    elif accuracy >= 0.85:
        acc_l = 10.0
    elif accuracy >= 0.75:
        acc_l = 9.0
    elif accuracy >= 0.60:
        acc_l = 8.0
    elif accuracy >= 0.45:
        acc_l = 7.5
    else:
        acc_l = 7.0

    # RT variability 자리 (MEDA speed 0.3)
    if rt_cv <= 0.08:
        cv_adj = +0.5
    elif rt_cv <= 0.15:
        cv_adj = +0.2
    elif rt_cv <= 0.20:
        cv_adj = 0.0
    elif rt_cv <= 0.30:
        cv_adj = -0.3
    else:
        cv_adj = -0.7

    # RT mean 자리 (참고만, 너무 빠르거나 느리면 catch)
    if rt_mean < 300:  # 너무 빠름 = impulsive 자리
        rt_adj = -0.2
    elif rt_mean > 700:
        rt_adj = -0.2
    else:
        rt_adj = 0.0

    final_l = round(acc_l + cv_adj * 0.5 + rt_adj * 0.3, 1)
    final_l = max(7.0, min(13.0, final_l))  # Clamp L7-L13

    # Confidence 박힘
    if score.get('duration_min', 2) < 1.5:
        confidence = 0.5  # 짧으면 신뢰도 낮음
    elif rt_cv > 0.4:
        confidence = 0.6  # 너무 변동 크면 신뢰도 낮음
    else:
        confidence = 0.75

    # Markers
    markers = []
    if accuracy >= 0.90:
        markers.append("high_accuracy")
    if rt_cv <= 0.15:
        markers.append("consistent_responding")
    if final_l >= 10.0:
        markers.append("strong_sustained_attention")
    elif final_l <= 8.0:
        markers.append("attention_difficulty_suspected")

    return FischerLevel(
        level=final_l,
        confidence=confidence,
        markers_matched=markers,
    )
