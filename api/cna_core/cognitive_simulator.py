"""
CNA v7 — Cognitive Simulator (Counterfactual Reasoning)

"만약 이 인지축을 박으면 임상 점수가 어떻게 변할까?" 시뮬레이션.

Active Inference framework: 
  Counterfactual policy evaluation under expected free energy.

기능:
1. 단일 인지축 변화 시뮬레이션 (e.g., working_memory L8.5 → L10.0)
2. 카드 시퀀스 효과 추정 (4주/8주 후 예상)
3. 개입 후보 순위 (어느 인지축부터 훈련하는 게 가장 효과적)
4. Target Level 자동 추천

원리:
- CognitiveClinicalMapper.predict_clinical_state() 재사용
- 인지축 자료 변형 → 임상축 자료 차이 = 효과
- 카드의 target_fischer_levels → 시뮬레이션 input

Boston Neuromind LLC · 2026
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
import numpy as np

from cna_core.types import (
    CognitiveAxis, ClinicalAxis,
    COGNITIVE_AXES, CLINICAL_AXES,
    COGNITIVE_AXIS_KOREAN, CLINICAL_AXIS_KOREAN,
    Card,
)
from cna_core.cognitive_clinical_mapper import CognitiveClinicalMapper


class SingleAxisCounterfactual(BaseModel):
    """단일 인지축 변화 시뮬레이션."""
    cognitive_axis: CognitiveAxis
    cognitive_axis_ko: str
    
    current_level: float
    target_level: float
    delta_level: float
    
    # Baseline (현재 자료)
    baseline_clinical: dict[str, float]
    
    # Counterfactual (가상 자료)
    counterfactual_clinical: dict[str, float]
    
    # 차이
    clinical_deltas: dict[str, float]
    
    # 종합 효과
    total_clinical_improvement: float
    primary_beneficiary_axis: str
    interpretation_ko: str


class CardSequenceSimulation(BaseModel):
    """카드 시퀀스 (프로토콜) 효과 시뮬레이션."""
    card_ids: list[str]
    weeks: int
    
    # 시뮬레이션 결과
    starting_cognitive: dict[str, float]
    projected_cognitive: dict[str, float]
    starting_clinical: dict[str, float]
    projected_clinical: dict[str, float]
    
    # 변화
    cognitive_deltas: dict[str, float]
    clinical_deltas: dict[str, float]
    
    # 신뢰도
    uncertainty: float
    assumptions: list[str]


class InterventionRanking(BaseModel):
    """개입 후보 순위."""
    ranked_interventions: list[dict]
    optimal_intervention: dict
    expected_total_benefit: float
    rationale: str


class CognitiveSimulator:
    """
    Counterfactual 시뮬레이션 엔진.
    
    핵심: CognitiveClinicalMapper 재사용으로 일관성 보장.
    """
    
    # Card target → cognitive improvement 추정값
    # (4주 standard 자료, evidence_d 기반)
    LEVEL_CHANGE_PER_4WEEKS_BY_EVIDENCE = {
        0.8: 0.50,   # very strong evidence → +0.50 level
        0.7: 0.40,
        0.6: 0.30,
        0.5: 0.25,
        0.4: 0.20,
        0.3: 0.15,
        0.2: 0.10,
    }
    
    def __init__(self, mapper: CognitiveClinicalMapper):
        self.mapper = mapper
    
    # ========================================
    # 1. 단일 인지축 시뮬레이션
    # ========================================
    
    def simulate_single_axis_change(
        self,
        baseline_cognitive: dict[CognitiveAxis, float],
        axis: CognitiveAxis,
        target_level: float,
    ) -> SingleAxisCounterfactual:
        """
        한 인지축만 변경 → 임상 5축 차이 catch.
        
        예: working_memory L8.5 → L10.0 박으면 임상축이 얼마나 변할까?
        """
        current_level = baseline_cognitive.get(axis, 9.0)
        delta = target_level - current_level
        
        # Baseline 자료
        baseline_state = self.mapper.predict_clinical_state(baseline_cognitive)
        baseline_clinical = {a: s["score"] for a, s in baseline_state.items()}
        
        # Counterfactual: 해당 축만 변경
        counterfactual_cognitive = dict(baseline_cognitive)
        counterfactual_cognitive[axis] = target_level
        
        cf_state = self.mapper.predict_clinical_state(counterfactual_cognitive)
        cf_clinical = {a: s["score"] for a, s in cf_state.items()}
        
        # 차이
        clinical_deltas = {
            a: cf_clinical[a] - baseline_clinical[a]
            for a in CLINICAL_AXES
        }
        
        # 종합 자료
        # anxiety/depression은 점수 높을수록 좋음 (정상 자료)
        # 모든 축 합 (양의 변화 좋음)
        total_improvement = sum(clinical_deltas.values())
        
        # 가장 크게 개선되는 임상축
        primary_beneficiary = max(clinical_deltas.items(), key=lambda x: x[1])[0]
        
        # 해석
        axis_ko = COGNITIVE_AXIS_KOREAN[axis]
        prim_ko = CLINICAL_AXIS_KOREAN[primary_beneficiary]
        interpretation = (
            f"{axis_ko} L{current_level:.1f} → L{target_level:.1f} (Δ{delta:+.1f}) 박으면, "
            f"가장 큰 효과 자료: {prim_ko} {clinical_deltas[primary_beneficiary]:+.3f}. "
            f"총 임상 개선: {total_improvement:+.3f}."
        )
        
        return SingleAxisCounterfactual(
            cognitive_axis=axis,
            cognitive_axis_ko=axis_ko,
            current_level=current_level,
            target_level=target_level,
            delta_level=delta,
            baseline_clinical=baseline_clinical,
            counterfactual_clinical=cf_clinical,
            clinical_deltas=clinical_deltas,
            total_clinical_improvement=total_improvement,
            primary_beneficiary_axis=primary_beneficiary,
            interpretation_ko=interpretation,
        )
    
    # ========================================
    # 2. 모든 인지축 동시 비교 (개입 우선순위)
    # ========================================
    
    def rank_intervention_candidates(
        self,
        baseline_cognitive: dict[CognitiveAxis, float],
        target_clinical_axis: Optional[ClinicalAxis] = None,
        target_delta: float = 1.0,
    ) -> InterventionRanking:
        """
        모든 인지축을 동일 자료 (target_delta=1.0 level) 훈련했을 때 효과 비교.
        
        Args:
            target_clinical_axis: 특정 임상축에 집중 (선택)
            target_delta: 각 인지축 +1.0 Level (기본)
        
        Returns:
            가장 효과적인 인지축부터 순위
        """
        candidates = []
        
        for axis in COGNITIVE_AXES:
            current = baseline_cognitive.get(axis, 9.0)
            target = min(13.0, current + target_delta)
            
            cf = self.simulate_single_axis_change(
                baseline_cognitive, axis, target
            )
            
            # 점수 계산
            if target_clinical_axis:
                # 특정 축 우선
                score = cf.clinical_deltas[target_clinical_axis]
            else:
                # 전체 합 (모든 축 개선)
                score = cf.total_clinical_improvement
            
            candidates.append({
                "cognitive_axis": axis,
                "axis_ko": COGNITIVE_AXIS_KOREAN[axis],
                "current_level": current,
                "target_level": target,
                "expected_total_improvement": cf.total_clinical_improvement,
                "specific_target_improvement": (
                    cf.clinical_deltas[target_clinical_axis]
                    if target_clinical_axis else None
                ),
                "primary_beneficiary": cf.primary_beneficiary_axis,
                "clinical_deltas": cf.clinical_deltas,
                "ranking_score": score,
            })
        
        # 점수 순 정렬
        candidates.sort(key=lambda c: c["ranking_score"], reverse=True)
        
        # Rank 추가
        for i, c in enumerate(candidates, 1):
            c["rank"] = i
        
        optimal = candidates[0]
        
        # Rationale
        if target_clinical_axis:
            target_ko = CLINICAL_AXIS_KOREAN[target_clinical_axis]
            rationale = (
                f"{target_ko} 개선이 1순위 자료. "
                f"가장 효과적: {optimal['axis_ko']} +{target_delta:.1f} Level → "
                f"{target_ko} {optimal['specific_target_improvement']:+.3f}"
            )
        else:
            rationale = (
                f"전체 임상 5축 종합 개선 자료. "
                f"가장 효과적: {optimal['axis_ko']} +{target_delta:.1f} Level → "
                f"총 {optimal['expected_total_improvement']:+.3f}"
            )
        
        return InterventionRanking(
            ranked_interventions=candidates,
            optimal_intervention=optimal,
            expected_total_benefit=optimal["ranking_score"],
            rationale=rationale,
        )
    
    # ========================================
    # 3. 카드 시퀀스 시뮬레이션
    # ========================================
    
    def simulate_card_sequence(
        self,
        baseline_cognitive: dict[CognitiveAxis, float],
        cards: list[Card],
        weeks: int = 4,
    ) -> CardSequenceSimulation:
        """
        카드 시퀀스 (전체 프로토콜) 적용 후 예상 자료.
        
        Logic:
          각 카드의 target_fischer_levels → 인지축별 incremental 변화 자료 추정
          evidence_d × 카드 반복 횟수 × 시간이 = 누적 변화
        """
        # 각 인지축별 누적 변화 추정
        cognitive_changes = {axis: 0.0 for axis in COGNITIVE_AXES}
        
        # 카드 반복 자료 catch
        card_occurrences = {}
        for c in cards:
            card_occurrences[c.id] = card_occurrences.get(c.id, 0) + 1
        
        # 각 카드의 누적 효과
        for card in cards:
            n_uses = card_occurrences[card.id]
            
            # Evidence 기반 단위 변화 자료
            level_change_4w = self._evidence_to_level_change(card.evidence_d)
            
            # 4주 기준 → n_uses에 비례 (diminishing returns)
            # log scale: 1번 = 1x, 12번 = 2.5x, 24번 = 3x
            usage_factor = 1.0 + 0.5 * np.log1p(n_uses - 1) if n_uses > 0 else 0.0
            
            # 카드 타겟 인지축에 변화 자료 추가
            for axis, target_level in card.target_fischer_levels.items():
                current = baseline_cognitive.get(axis, 9.0)
                
                # Target보다 환자 자료가 낮으면 훈련할 영역
                if target_level > current:
                    expected_change = level_change_4w * usage_factor
                    # 카드 타겟 level 넘어가지 않게 cap
                    max_change = target_level - current
                    actual_change = min(expected_change, max_change)
                    cognitive_changes[axis] += actual_change
        
        # 4주 기준 자료를 weeks에 맞춰 조정
        time_factor = weeks / 4.0
        
        # 너무 많은 자료 = 비현실. log dampening.
        for axis in cognitive_changes:
            raw = cognitive_changes[axis]
            cognitive_changes[axis] = raw * time_factor / (1 + 0.3 * raw)
        
        # Projected cognitive
        projected_cognitive = {
            axis: min(13.0, baseline_cognitive.get(axis, 9.0) + delta)
            for axis, delta in cognitive_changes.items()
        }
        
        # 임상 5축 예측
        baseline_state = self.mapper.predict_clinical_state(baseline_cognitive)
        projected_state = self.mapper.predict_clinical_state(projected_cognitive)
        
        baseline_clinical = {a: s["score"] for a, s in baseline_state.items()}
        projected_clinical = {a: s["score"] for a, s in projected_state.items()}
        
        clinical_deltas = {
            a: projected_clinical[a] - baseline_clinical[a]
            for a in CLINICAL_AXES
        }
        
        # Uncertainty 자료
        # - 카드 evidence 낮음 → 불확실 ↑
        # - 카드 반복 적음 → 불확실 ↑
        avg_evidence = np.mean([c.evidence_d for c in cards]) if cards else 0.3
        avg_repetitions = np.mean(list(card_occurrences.values())) if card_occurrences else 1
        uncertainty = max(0.1, min(0.9, 1.0 - avg_evidence * 0.5 - 0.05 * avg_repetitions))
        
        assumptions = [
            f"Linear evidence → level change 매핑 (d={avg_evidence:.2f})",
            f"평균 카드 반복 {avg_repetitions:.1f}회",
            f"시간이: {weeks}주 (4주 기준 자료 비례)",
            "Carry-over 효과 ❌ (각 카드 독립 가정)",
            "환자 개인 반응성 ❌ (평균 effect 적용)",
        ]
        
        return CardSequenceSimulation(
            card_ids=[c.id for c in cards],
            weeks=weeks,
            starting_cognitive=dict(baseline_cognitive),
            projected_cognitive=projected_cognitive,
            starting_clinical=baseline_clinical,
            projected_clinical=projected_clinical,
            cognitive_deltas=cognitive_changes,
            clinical_deltas=clinical_deltas,
            uncertainty=uncertainty,
            assumptions=assumptions,
        )
    
    # ========================================
    # 4. Target Level 자동 추천
    # ========================================
    
    def recommend_target_levels(
        self,
        baseline_cognitive: dict[CognitiveAxis, float],
        target_clinical_axis: ClinicalAxis,
        target_clinical_score: float = 0.65,  # 도달 목표 (default = "good" tier)
    ) -> dict[str, dict]:
        """
        목표 임상 점수에 도달하기 위해 각 인지축이 도달해야 할 Level 자료.
        
        Iterative 자료: 각 인지축을 점진 ↑ 하며 목표 임상점수 도달 지점 catch.
        """
        recommendations = {}
        
        baseline_state = self.mapper.predict_clinical_state(baseline_cognitive)
        current_score = baseline_state[target_clinical_axis]["score"]
        
        if current_score >= target_clinical_score:
            return {"status": "already_at_target", "current_score": current_score}
        
        # 각 인지축 단독으로 목표 도달까지 훈련할 영역
        for axis in COGNITIVE_AXES:
            current_level = baseline_cognitive.get(axis, 9.0)
            
            # Binary search
            low = current_level
            high = 13.0
            target_level = high
            
            for _ in range(15):  # max iterations
                mid = (low + high) / 2.0
                test_cognitive = dict(baseline_cognitive)
                test_cognitive[axis] = mid
                
                test_state = self.mapper.predict_clinical_state(test_cognitive)
                test_score = test_state[target_clinical_axis]["score"]
                
                if test_score >= target_clinical_score:
                    target_level = mid
                    high = mid
                else:
                    low = mid
                
                if high - low < 0.05:
                    break
            
            # 도달 가능 여부 자료
            test_cognitive = dict(baseline_cognitive)
            test_cognitive[axis] = 13.0
            max_state = self.mapper.predict_clinical_state(test_cognitive)
            max_achievable = max_state[target_clinical_axis]["score"]
            
            recommendations[axis] = {
                "current_level": current_level,
                "target_level": target_level if target_level < 13.0 else None,
                "delta_needed": target_level - current_level if target_level < 13.0 else None,
                "feasibility": (
                    "feasible" if target_level < 13.0
                    else "infeasible_alone"
                ),
                "max_achievable_score": max_achievable,
                "axis_ko": COGNITIVE_AXIS_KOREAN[axis],
            }
        
        return {
            "status": "computed",
            "current_score": current_score,
            "target_score": target_clinical_score,
            "target_clinical_axis": target_clinical_axis,
            "per_axis_recommendations": recommendations,
        }
    
    # ========================================
    # Helpers
    # ========================================
    
    def _evidence_to_level_change(self, evidence_d: float) -> float:
        """Cochrane d → 4주 Level 변화 추정."""
        # Find closest evidence tier
        thresholds = sorted(self.LEVEL_CHANGE_PER_4WEEKS_BY_EVIDENCE.keys(), reverse=True)
        for t in thresholds:
            if evidence_d >= t:
                return self.LEVEL_CHANGE_PER_4WEEKS_BY_EVIDENCE[t]
        return 0.05  # 최저
