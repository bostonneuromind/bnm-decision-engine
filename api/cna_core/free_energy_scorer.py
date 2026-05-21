"""
CNA v6 — Free Energy Decision Scoring

Active Inference framework (Friston):
  G (Expected Free Energy) = Complexity - Accuracy - Preference - Epistemic - Pragmatic
  최선의 카드 = argmin G (= argmax -G)

6-Component 분해:
  1. Accuracy (Symptom): 환자 증상 vs 카드 타겟 likelihood
  2. Accuracy (Biomarker): 측정값 vs 카드 expected profile Z-score
  3. Complexity: Fischer level 거리 (Vygotsky ZPD)
  4. Preference: V2 Desire 정합
  5. Epistemic: Information Gain (자료 잡기)
  6. Pragmatic: Evidence × Practical fit (즉시 효과)

가중치는 환자 phase에 따라 자동 조정.

Boston Neuromind LLC · 2026
"""

import math
from pathlib import Path
from typing import Optional
import yaml
import numpy as np

from cna_core.types import (
    Card, V1State, V2Desire, V3Skill, V4Trajectory,
    ScoredCard, ComponentBreakdown,
)


CONFIG_PATH = Path(__file__).parent.parent / "config" / "free_energy_weights.yaml"


def _load_config(config_path: Optional[Path] = None) -> dict:
    """가중치 설정 로드."""
    path = config_path or CONFIG_PATH
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ============================================================
# Phase-dependent weights
# ============================================================

def compute_phase_weights(
    v4: V4Trajectory,
    config: dict,
    clinical_scores: Optional[dict] = None,
) -> dict[str, float]:
    """
    환자 phase에 따라 가중치 자동 조정.
    
    Active Inference 자연 원리:
    - 자료 없음 → epistemic 우선 (탐색)
    - 자료 충분 → pragmatic 우선 (활용)
    
    Round 1 추가:
    - 위급 환자 (priority tier 임상축) → emergency phase 자동
      윤리적 자료: 위급 상황에 자료 탐색보다 즉시 효과 우선.
    """
    # Emergency phase 자동 검사
    emergency_cfg = config.get("emergency_phase", {})
    if clinical_scores and emergency_cfg:
        threshold = emergency_cfg.get("activation_threshold", 0.30)
        trigger_axes = emergency_cfg.get("triggers_on_axes", [])
        
        for axis in trigger_axes:
            score = clinical_scores.get(axis, 1.0)
            if score < threshold:
                # Emergency phase 활성
                return dict(config["phase_weights"]["emergency"])
    
    # 일반 phase 자료
    n = v4.n_sessions
    
    if n == 0:
        return dict(config["phase_weights"]["new_patient"])
    elif n < 4:
        return dict(config["phase_weights"]["early"])
    else:
        return dict(config["phase_weights"]["stable"])


# ============================================================
# 6 Component 계산
# ============================================================

def accuracy_symptom(v1: V1State, card: Card) -> float:
    """
    Component 1: 카드 타겟 증상 - 환자 증상 매칭.
    
    Likelihood P(observed_symptoms | card_targets).
    Cosine similarity. 0.0 - 1.0.
    """
    if not card.target_symptoms or not v1.symptom_vector:
        return 0.0
    
    all_keys = set(card.target_symptoms.keys()) | set(v1.symptom_vector.keys())
    a = np.array([v1.symptom_vector.get(k, 0.0) for k in all_keys])
    b = np.array([card.target_symptoms.get(k, 0.0) for k in all_keys])
    
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return float(np.dot(a, b) / (norm_a * norm_b))


def accuracy_biomarker(v1: V1State, card: Card) -> float:
    """
    Component 2: 환자 측정값 - 카드 expected profile Z-score fit.
    
    Round 1 강화: 자동 단위 정규화 (Z-score, ms, %, proportion 자료 통합).
    Precision-weighted (Friston): noise 큰 측정 = update 작게.
    """
    from cna_core.biomarker_normalization import normalize_v1_biomarkers, normalize_card_profile
    
    if not card.expected_biomarker_profile or not v1.biomarkers:
        return 0.5  # neutral
    
    # 정규화 자료 (0-1 scale로 통일)
    norm_observed = normalize_v1_biomarkers(v1.biomarkers)
    norm_expected = normalize_card_profile(card.expected_biomarker_profile)
    
    total_fit = 0.0
    total_weight = 0.0
    
    for biomarker, expected_norm in norm_expected.items():
        observed_norm = norm_observed.get(biomarker)
        if observed_norm is None:
            continue
        
        # Precision 자료 (정규화 후 사용)
        raw_variance = v1.biomarker_variance.get(biomarker, 0.3)
        precision = 1.0 / (raw_variance + 1e-6)
        
        # 정규화된 자료에서 거리 자료
        distance = abs(observed_norm - expected_norm)
        fit = math.exp(-2.0 * distance ** 2)  # gaussian, 더 강한 패널티
        
        total_fit += fit * precision
        total_weight += precision
    
    if total_weight == 0:
        return 0.5
    
    return float(total_fit / total_weight)


def complexity_penalty(v3: V3Skill, card: Card, config: dict) -> float:
    """
    Component 3: Fischer level 거리 페널티 (Vygotsky ZPD).
    
    카드가 현재 능력에서 너무 멀면 학습 비효율.
    Active Inference: KL divergence from current posterior.
    """
    if not card.target_fischer_levels or not v3.axis_levels:
        return 0.0
    
    optimal_zone = config["complexity"]["optimal_zone_levels"]
    exponent = config["complexity"]["penalty_growth_exponent"]
    
    distances = []
    for axis, target in card.target_fischer_levels.items():
        current = v3.axis_levels.get(axis)
        if current is None:
            continue
        dist = abs(target - current)
        distances.append(dist)
    
    if not distances:
        return 0.0
    
    mean_dist = np.mean(distances)
    penalty = max(0.0, mean_dist - optimal_zone) ** exponent
    return float(min(1.0, penalty))


def preference_match(v2: V2Desire, card: Card) -> float:
    """
    Component 4: V2 Desire 선호 정합.
    환자 선택 임상축이 카드 타겟에 있나?
    """
    score = 0.0
    
    if v2.primary_clinical_axis in card.target_clinical_axes:
        score += 0.7
    
    if v2.preferred_outcomes:
        overlap = 0.0
        for pref, weight in v2.preferred_outcomes.items():
            if pref in card.target_symptoms or pref in card.target_clinical_axes:
                overlap += weight
        score += 0.3 * min(1.0, overlap)
    
    # Motivation modulation
    score *= (0.5 + 0.5 * v2.motivation)
    
    return float(min(1.0, score))


def epistemic_value(card: Card, v3: V3Skill, v4: V4Trajectory) -> float:
    """
    Component 5: Information Gain (Active Inference 핵심).
    
    이 카드 적용 시 환자 모델 자료 얼마나 잡힐까?
    
    높은 자리:
    - 새 영역
    - 환자 자료 불확실
    - 카드 자체가 자료 잡기 좋게 설계됨
    """
    base = 0.5
    
    # 새 영역 보너스
    past_card_ids = {x.get("card_id") for x in v4.past_card_outcomes}
    if card.id not in past_card_ids:
        base += 0.15
    
    # Confidence 낮은 축 타겟팅
    for axis in card.target_fischer_levels.keys():
        conf = v3.confidence.get(axis, 0.5)
        if conf < 0.5:
            base += 0.1
    
    # 카드 자체 information_gain class
    class_bonus = {
        "high": 0.2,
        "standard": 0.0,
        "low": -0.1,
    }.get(card.information_gain_class, 0.0)
    base += class_bonus
    
    return float(min(1.0, max(0.0, base)))


def pragmatic_value(card: Card, v1: V1State, v4: V4Trajectory) -> float:
    """
    Component 6: 즉시 효과 가능성.
    Evidence × Practical fit × Past success rate.
    """
    # Evidence base
    evidence = min(1.0, card.evidence_d / 0.8)
    
    # Practical fit (state requirements 만족?)
    practical = 1.0
    for req_key, req_val in card.state_requirements.items():
        if req_key == "hrv_min_rmssd":
            current_hrv = v1.biomarkers.get("hrv_rmssd", 0)
            if current_hrv < req_val:
                practical *= 0.5
    
    # Past success
    similar_outcomes = [
        x.get("outcome_score", 0.0)
        for x in v4.past_card_outcomes
        if x.get("card_id", "").startswith(card.id[:6])
    ]
    past_success = np.mean(similar_outcomes) if similar_outcomes else 0.5
    past_success = max(0.0, min(1.0, (past_success + 1.0) / 2.0))
    
    return float(evidence * 0.4 + practical * 0.3 + past_success * 0.3)


# ============================================================
# Main Scorer
# ============================================================

class FreeEnergyScorer:
    """
    6-Component Free Energy Decision Scorer.
    
    Score = -G (높을수록 좋음).
    G = Complexity - Accuracy - Preference - Epistemic - Pragmatic.
    """
    
    def __init__(
        self,
        config_path: Optional[Path] = None,
        weights_override: Optional[dict[str, float]] = None,
    ):
        self.config = _load_config(config_path)
        self.weights_override = weights_override
        self.fixed_components = set(self.config.get("fixed_components", []))
    
    def score(
        self,
        filtered_cards: list[Card],
        v1: V1State,
        v2: V2Desire,
        v3: V3Skill,
        v4: V4Trajectory,
        top_n: Optional[int] = None,
        clinical_scores: Optional[dict] = None,
    ) -> list[ScoredCard]:
        """카드 점수 계산. Top N 반환.
        
        clinical_scores: emergency phase 자동 활성용 (5축 임상 점수).
        """
        
        top_n = top_n or self.config["decision"]["candidate_top_n"]
        
        # 가중치 결정 (emergency 자동 catch)
        if self.weights_override:
            weights = self.weights_override.copy()
        else:
            weights = compute_phase_weights(v4, self.config, clinical_scores)
        
        scored = []
        for card in filtered_cards:
            # 6 components
            acc_sym = accuracy_symptom(v1, card)
            acc_bio = accuracy_biomarker(v1, card)
            comp = complexity_penalty(v3, card, self.config)
            pref = preference_match(v2, card)
            epi = epistemic_value(card, v3, v4)
            prag = pragmatic_value(card, v1, v4)
            
            # Expected Free Energy
            G = (
                weights["complexity_penalty"] * comp
                - weights["accuracy_symptom"] * acc_sym
                - weights["accuracy_biomarker"] * acc_bio
                - weights["preference"] * pref
                - weights["epistemic"] * epi
                - weights["pragmatic"] * prag
            )
            
            final_score = -G
            
            breakdown = ComponentBreakdown(
                accuracy_symptom=acc_sym,
                accuracy_biomarker=acc_bio,
                complexity_penalty=comp,
                preference=pref,
                epistemic_value=epi,
                pragmatic_value=prag,
                weights_used=weights.copy(),
                final_score=final_score,
            )
            
            explanation = self._build_explanation(breakdown, card, v2)
            
            scored.append(ScoredCard(
                card=card,
                score=final_score,
                breakdown=breakdown,
                explanation=explanation,
            ))
        
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_n]
    
    def _build_explanation(
        self,
        b: ComponentBreakdown,
        card: Card,
        v2: V2Desire,
    ) -> str:
        """결정 이유 설명 (임상가 + 환자용)."""
        contributions = {
            "증상 매칭": b.accuracy_symptom * b.weights_used["accuracy_symptom"],
            "측정값 정합": b.accuracy_biomarker * b.weights_used["accuracy_biomarker"],
            "환자 목표 정합": b.preference * b.weights_used["preference"],
            "자료 탐색 가치": b.epistemic_value * b.weights_used["epistemic"],
            "근거 + 즉시 효과": b.pragmatic_value * b.weights_used["pragmatic"],
        }
        top_contrib = max(contributions.items(), key=lambda x: x[1])
        
        notes = []
        if b.complexity_penalty > 0.3:
            notes.append(f"난이도 조정 필요 ({b.complexity_penalty:.2f})")
        
        explanation = f"주요 이유: {top_contrib[0]} ({top_contrib[1]:.2f})"
        if notes:
            explanation += " | " + ", ".join(notes)
        return explanation
