"""OMR response history → Self-Cognition Fischer L.

미러 (변경 금지) — 원본: bnm-learning-engine/ml/mappings/omr.py.

Self-Cognition 측정 = 정성 자리. OMR 응답 패턴이 main signal.
"""

from typing import TypedDict, Optional
from measurement_mappings._fischer import FischerLevel


class OMRResponseHistory(TypedDict):
    total_hypotheses_thrown: int
    yes_count: int           # ✓ 응답
    no_count: int            # ✗ 응답
    sort_of_count: int       # ~ 응답 (nuance catch)
    no_response_count: int

    # 정성 자리
    self_correction_count: int   # "아 근데 사실은..." 박힌 자리
    contradiction_acknowledge_count: int  # 모순 catch
    meta_observation_count: int  # "내가 나를 X로 본다" 박힘
    multi_self_observation_count: int  # 다중 자기 (직장 vs 가족) catch


def omr_to_self_cognition_l(history: OMRResponseHistory) -> FischerLevel:
    """OMR 응답 누적 → Self-Cognition L7-L13.

    ⭐ Default 박힘. 사부 catch 자리:
    - 자유 발화 분석 통합 (NLP)
    - Time-weighted (최근 응답 weight ↑)
    - 임상가 검증 자리
    """
    total = history['total_hypotheses_thrown']
    if total < 3:
        # 너무 적은 자리 — baseline
        return FischerLevel(
            level=8.5,
            confidence=0.3,
            markers_matched=["insufficient_omr_data"],
        )

    yes = history['yes_count']
    no = history['no_count']
    sort_of = history['sort_of_count']

    # 응답률 자리 (engagement)
    response_rate = (yes + no + sort_of) / total

    # Nuance ratio (sort_of / total) = 자기 인지 깊이 박힘
    nuance_ratio = sort_of / max(1, yes + no + sort_of)

    # Self-reflection markers
    self_correct = history.get('self_correction_count', 0)
    contradiction = history.get('contradiction_acknowledge_count', 0)
    meta = history.get('meta_observation_count', 0)
    multi_self = history.get('multi_self_observation_count', 0)

    # L 박음 자리
    # L7: 단순 라벨 — 모두 ✓ 또는 모두 ✗
    # L8: 패턴 인식 — ✓/✗ 박힘 + 일부 응답 박힘
    # L9: 모순 catch — sort_of ↑ + self_correction
    # L10: 다중 자기 — multi_self ↑
    # L11: 메타 자기 — meta ↑
    # L12+: 통합 자리

    base_l = 7.0

    # 응답 자리 박힘
    if response_rate > 0.6:
        base_l += 1.0  # → L8

    # Nuance 박힘 (sort_of 응답 = 자기 인식 깊이)
    if nuance_ratio > 0.1:
        base_l += 0.5
    if nuance_ratio > 0.25:
        base_l += 0.5  # → L9

    # Self-reflection 박힘
    if self_correct > 0 or contradiction > 0:
        base_l += 0.5
    if self_correct >= 3 or contradiction >= 3:
        base_l += 0.5  # → L9-L10

    # 다중 자기
    if multi_self > 0:
        base_l += 0.5  # → L10
    if multi_self >= 3:
        base_l += 0.5  # → L10.5

    # Meta 자리
    if meta > 0:
        base_l += 0.5  # → L11
    if meta >= 3:
        base_l += 0.5  # → L11.5+

    final_l = max(7.0, min(13.0, round(base_l, 1)))

    # Confidence
    if total >= 20:
        confidence = 0.85
    elif total >= 10:
        confidence = 0.75
    elif total >= 5:
        confidence = 0.6
    else:
        confidence = 0.45

    markers = []
    if nuance_ratio > 0.25:
        markers.append("nuanced_self_responses")
    if multi_self >= 2:
        markers.append("multi_self_representation")
    if meta >= 2:
        markers.append("meta_self_observation")
    if self_correct >= 3:
        markers.append("active_self_correction")
    if response_rate < 0.3:
        markers.append("low_omr_engagement")

    return FischerLevel(
        level=final_l,
        confidence=confidence,
        markers_matched=markers,
    )
