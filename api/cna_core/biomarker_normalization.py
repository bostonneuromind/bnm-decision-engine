"""
CNA v6 — Biomarker Normalization (Round 1)

biomarker 자료 단위 표준화.
서로 다른 측정 단위 (Z-score, %, ms 등)를 cosine similarity가 작동하도록 자동 변환.

표준 자료:
  - Z-score 자료: 그대로 (-3.0 ~ +3.0)
  - 0-1 비율: 그대로
  - %: /100 → 0-1
  - ms: Z-score 변환 필요 (norm DB 자료)

Boston Neuromind LLC · 2026
"""

from typing import Optional


# ============================================================
# Biomarker 정의 자료 + norm 범위
# ============================================================

BIOMARKER_DEFINITIONS = {
    # CPT (Continuous Performance Test)
    "cpt_omissions_zscore": {
        "unit": "z_score",
        "norm_mean": 0.0,
        "norm_sd": 1.0,
        "good_direction": "high",  # 높을수록 좋음 (덜 누락)
        "expected_range": [-3.0, 3.0],
    },
    "cpt_rt_variability": {
        "unit": "z_score",
        "norm_mean": 0.0,
        "norm_sd": 1.0,
        "good_direction": "low",  # 낮을수록 좋음 (일관성)
        "expected_range": [-3.0, 3.0],
    },
    "cpt_d_prime": {
        "unit": "raw",
        "norm_mean": 3.0,
        "norm_sd": 0.8,
        "good_direction": "high",
        "expected_range": [0.0, 5.0],
    },
    
    # HRV (Heart Rate Variability)
    "hrv_rmssd": {
        "unit": "ms",
        "norm_mean": 35.0,  # 성인 평균 자료
        "norm_sd": 15.0,
        "good_direction": "high",
        "expected_range": [10.0, 100.0],
    },
    "hrv_lf_hf": {
        "unit": "ratio",
        "norm_mean": 1.5,
        "norm_sd": 0.8,
        "good_direction": "balanced",
        "expected_range": [0.3, 5.0],
    },
    "hrv_sdnn": {
        "unit": "ms",
        "norm_mean": 50.0,
        "norm_sd": 20.0,
        "good_direction": "high",
        "expected_range": [15.0, 150.0],
    },
    
    # N-back
    "nback_accuracy": {
        "unit": "proportion",
        "norm_mean": 0.75,
        "norm_sd": 0.15,
        "good_direction": "high",
        "expected_range": [0.0, 1.0],
    },
    "nback_2_accuracy": {
        "unit": "proportion",
        "norm_mean": 0.80,
        "norm_sd": 0.12,
        "good_direction": "high",
        "expected_range": [0.0, 1.0],
    },
    "nback_3_accuracy": {
        "unit": "proportion",
        "norm_mean": 0.65,
        "norm_sd": 0.15,
        "good_direction": "high",
        "expected_range": [0.0, 1.0],
    },
    "nback_d_prime": {
        "unit": "raw",
        "norm_mean": 2.5,
        "norm_sd": 0.8,
        "good_direction": "high",
        "expected_range": [0.0, 4.5],
    },
    
    # 시간추정
    "time_estimation_error_pct": {
        "unit": "percent",
        "norm_mean": 12.0,  # 12% 평균 오차
        "norm_sd": 6.0,
        "good_direction": "low",
        "expected_range": [0.0, 50.0],
    },
    
    # VSR (Vocal Stress Reading)
    "vsr_consistency": {
        "unit": "proportion",
        "norm_mean": 0.70,
        "norm_sd": 0.15,
        "good_direction": "high",
        "expected_range": [0.0, 1.0],
    },
    "vsr_cells_activated": {
        "unit": "count",
        "norm_mean": 25.0,  # 800셀 중 평균 활성
        "norm_sd": 10.0,
        "good_direction": "balanced",
        "expected_range": [0, 800],
    },
    
    # PHQ-9 (자살 검사 자료)
    "phq9_total": {
        "unit": "raw",
        "norm_mean": 5.0,
        "norm_sd": 5.0,
        "good_direction": "low",  # 낮을수록 좋음
        "expected_range": [0, 27],
    },
}


def normalize_biomarker(name: str, value: float) -> float:
    """
    Biomarker 값을 0-1 표준 자료로 변환.
    Cosine similarity가 동일 scale에서 비교 가능.
    
    변환 자료:
    - Z-score 자료: clip(-3,3) → (z+3)/6 → 0-1
    - Proportion: 그대로
    - ms / raw / percent: Z-score 계산 후 위 자료
    """
    if name not in BIOMARKER_DEFINITIONS:
        return value  # 알 수 없는 자료 그대로
    
    defn = BIOMARKER_DEFINITIONS[name]
    unit = defn["unit"]
    
    if unit == "proportion":
        return max(0.0, min(1.0, value))
    
    if unit == "z_score":
        z = max(-3.0, min(3.0, value))
        return (z + 3.0) / 6.0
    
    # Raw, ms, percent, count, ratio → Z-score 변환 후 정규화
    mean = defn["norm_mean"]
    sd = defn["norm_sd"]
    if sd == 0:
        return 0.5
    
    z = (value - mean) / sd
    z = max(-3.0, min(3.0, z))
    
    # good_direction에 따라 부호 자료
    direction = defn.get("good_direction", "high")
    if direction == "low":
        # 낮을수록 좋음 → 점수 역전
        z = -z
    elif direction == "balanced":
        # 평균에서 멀수록 나쁨 → |z| 사용
        z = -abs(z) + 1.5  # 0이 가장 좋음, ±2가 나쁨
    
    return max(0.0, min(1.0, (z + 3.0) / 6.0))


def normalize_v1_biomarkers(biomarkers: dict[str, float]) -> dict[str, float]:
    """V1State의 biomarker 자료 전체 정규화."""
    return {
        name: normalize_biomarker(name, value)
        for name, value in biomarkers.items()
    }


def normalize_card_profile(profile: dict[str, float]) -> dict[str, float]:
    """Card의 expected_biomarker_profile 자료 전체 정규화."""
    return {
        name: normalize_biomarker(name, value)
        for name, value in profile.items()
    }
