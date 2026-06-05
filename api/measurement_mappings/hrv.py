"""HRV → Emotional Regulation Fischer L.

미러 (변경 금지) — 원본: bnm-learning-engine/ml/mappings/hrv.py.

NOTE: HRV 는 자율신경 balance 자리. ER 능력 ≠ HRV 만.
이 매핑은 ER 의 'physiological substrate' 박힘. 자기 보고 + VSR 통합 필요.
"""

from typing import TypedDict, Optional
from measurement_mappings._fischer import FischerLevel


class HRVRawScore(TypedDict):
    rmssd: float          # ms (most reliable parasympathetic 자리)
    sdnn: float           # ms (overall variability)
    lf_hf_ratio: float
    baseline_rmssd: Optional[float]  # 사용자 baseline 자리


def hrv_to_emotional_regulation_l(score: HRVRawScore) -> FischerLevel:
    """HRV → ER L7-L13.

    ⭐ Default 박힘. 사부 catch 자리:
    - Age-adjusted norms (RMSSD 평균이 나이별 다름)
    - 자기 보고 통합
    - VSR valence 통합
    """
    rmssd = score['rmssd']
    lf_hf = score.get('lf_hf_ratio', 1.5)
    baseline = score.get('baseline_rmssd')

    # RMSSD 자리 (가장 reliable)
    # 성인 일반 RMSSD: 20-60ms
    if rmssd < 10:
        physio_l = 6.5  # 위험 자리
    elif rmssd < 15:
        physio_l = 7.0
    elif rmssd < 25:
        physio_l = 8.0
    elif rmssd < 40:
        physio_l = 9.0
    elif rmssd < 60:
        physio_l = 10.0
    elif rmssd < 80:
        physio_l = 11.0
    else:
        physio_l = 12.0

    # LF/HF ratio 자리 (balance indicator)
    if 0.5 <= lf_hf <= 2.0:
        balance_adj = +0.3
    elif lf_hf > 4.0:
        balance_adj = -0.5  # Sympathetic 우세
    elif lf_hf < 0.3:
        balance_adj = -0.3
    else:
        balance_adj = 0.0

    final_l = physio_l + balance_adj * 0.5

    # Baseline 박힘 자리
    confidence = 0.65
    markers = []
    if baseline:
        diff = rmssd - baseline
        if abs(diff) > baseline * 0.4:
            # Baseline 대비 큰 자리 catch
            markers.append("hrv_significant_deviation")
            if diff < 0:
                markers.append("hrv_decreased_below_baseline")
                # 자기 catch 자리 - stress event 가능
            else:
                markers.append("hrv_elevated_above_baseline")
        confidence = 0.8  # Baseline 박힘 자리 = 신뢰도 ↑

    final_l = max(6.0, min(13.0, round(final_l, 1)))

    # Markers
    if rmssd < 15:
        markers.append("hrv_extreme_low")
    if rmssd >= 50:
        markers.append("hrv_strong")
    if 0.8 <= lf_hf <= 1.5:
        markers.append("balanced_autonomic")

    return FischerLevel(
        level=final_l,
        confidence=confidence,
        markers_matched=markers,
    )


def combine_er_measures(
    hrv_l: FischerLevel,
    vsr_valence: Optional[float] = None,
    vsr_intensity: Optional[float] = None,
    self_report: Optional[int] = None,  # 1-7 scale
) -> FischerLevel:
    """HRV + VSR + Self-report 통합.

    ER 능력의 multi-modal 측정 자리.
    """
    # HRV weight 0.5, VSR weight 0.3, self-report weight 0.2

    combined_l = hrv_l.level
    weight_sum = 0.5
    confidence = hrv_l.confidence

    if vsr_valence is not None and vsr_intensity is not None:
        # VSR valence + intensity → ER L 박음
        # High valence + low intensity = better regulation
        vsr_score = (1 + vsr_valence) * 0.5 + (1 - vsr_intensity) * 0.5
        vsr_l = 7.0 + vsr_score * 6.0  # Scale to L7-L13
        combined_l = combined_l * 0.5 / (weight_sum + 0.3) + vsr_l * 0.3 / (weight_sum + 0.3) * (weight_sum + 0.3)
        # 간소화:
        combined_l = (hrv_l.level * 0.5 + vsr_l * 0.3) / 0.8
        weight_sum = 0.8
        confidence += 0.05

    if self_report is not None:
        # 1-7 scale → L7-L13
        sr_l = 7.0 + (self_report - 1) * 1.0
        if weight_sum < 0.8:
            combined_l = (hrv_l.level * 0.5 + sr_l * 0.2) / 0.7
        else:
            combined_l = (combined_l * weight_sum + sr_l * 0.2) / (weight_sum + 0.2)
        confidence += 0.05

    return FischerLevel(
        level=round(combined_l, 1),
        confidence=min(0.9, confidence),
        markers_matched=hrv_l.markers_matched,
    )
