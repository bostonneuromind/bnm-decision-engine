"""
CNA v7 — Adaptive Re-routing

4주 회기 끝나면 outcome 자료로 진단 자료를 재구성.

원리 (Bayesian update on diagnostic hypothesis):
  새 prior(diagnosis) = old posterior(diagnosis) × treatment_response_likelihood

핵심 자료:
  - 1차 추정 = ADHD primary였는데, 주의력 카드 적용했더니 효과 ❌, 불안만 ↓
    → "아 이건 불안이 주의력 끌고 갔구나" catch
    → diagnosis 재구성: GAD primary, ADHD secondary 자료
    
  - 1차 = GAD primary였는데, HRV 호흡 적용했더니 불안 ↓ 하지만 주의력 자료 ↑ 동반 ❌
    → "주의력은 독립 source가 있구나" → ADHD comorbid 추가 자료

Treatment Response Patterns (임상 근거):
  - ADHD primary → 자극제/CBT-ADHD → 주의력 ↑, 학습 ↑ (4주 내)
  - GAD primary → HRV/CBT-anxiety → 불안 ↓, HRV RMSSD ↑
  - MDD primary → BA → 기분 ↑, 동기 ↑

Boston Neuromind LLC · 2026
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
import numpy as np

from cna_core.types import CLINICAL_AXES, CognitiveAxis, ClinicalAxis
from cna_core.differential_diagnosis import (
    DifferentialDiagnosisEngine,
    DifferentialDiagnosisResult,
    TemporalHistory,
)


class TreatmentResponse(BaseModel):
    """한 회기 사이클의 outcome 자료."""
    episode_id: str
    primary_intervention_axis: ClinicalAxis     # 어느 임상축 적용했나
    intervention_cards: list[str]               # 카드 ID 자료
    
    # Before/After
    cognitive_before: dict[str, float]
    cognitive_after: dict[str, float]
    clinical_before: dict[str, float]
    clinical_after: dict[str, float]
    
    # 변화량
    cognitive_changes: dict[str, float]
    clinical_changes: dict[str, float]


class ReroutingDecision(BaseModel):
    """진단 자료 재구성 결정."""
    timestamp: datetime
    patient_id: str
    
    # 이전 진단 자료
    previous_primary: str
    previous_secondary: list[str]
    
    # 갱신된 진단 자료
    updated_primary: str
    updated_secondary: list[str]
    
    # 변경 자료
    diagnosis_changed: bool
    change_type: str           # "no_change" | "secondary_added" | "primary_swap" | "diagnosis_dropped"
    
    # 임상 자료
    treatment_response_pattern: str
    rationale_ko: str
    
    # 신뢰도
    posterior_update_magnitude: float
    flagged_for_review: bool = False


class AdaptiveRerouter:
    """
    4주 outcome 자료 → diagnosis 재구성.
    """
    
    # Expected treatment response patterns by diagnosis
    EXPECTED_RESPONSES = {
        "adhd_inattentive": {
            "primary_treatment_targets": ["attention", "learning"],
            "expected_improvements": {
                "attention": 0.15,        # ↑
                "learning": 0.10,
                "peak_performance": 0.08,
                "anxiety": 0.05,
                "depression": 0.03,
            },
            "expected_cognitive_changes": {
                "sustained_attention": 0.30,    # +0.30 level
                "working_memory": 0.20,
                "emotional_regulation": 0.05,
                "time_awareness": 0.10,
                "self_awareness": 0.05,
            },
        },
        "gad": {
            "primary_treatment_targets": ["anxiety"],
            "expected_improvements": {
                "anxiety": 0.20,
                "attention": 0.08,        # 2차 개선
                "learning": 0.05,
                "peak_performance": 0.05,
                "depression": 0.10,
            },
            "expected_cognitive_changes": {
                "emotional_regulation": 0.35,
                "self_awareness": 0.15,
                "sustained_attention": 0.10,    # 불안 ↓ 인한 2차
                "working_memory": 0.10,
                "time_awareness": 0.05,
            },
        },
        "mdd": {
            "primary_treatment_targets": ["depression"],
            "expected_improvements": {
                "depression": 0.20,
                "attention": 0.08,
                "learning": 0.05,
                "peak_performance": 0.05,
                "anxiety": 0.12,
            },
            "expected_cognitive_changes": {
                "self_awareness": 0.25,
                "emotional_regulation": 0.20,
                "sustained_attention": 0.05,
                "working_memory": 0.05,
                "time_awareness": 0.10,
            },
        },
    }
    
    def __init__(self, dde_engine: DifferentialDiagnosisEngine):
        self.dde = dde_engine
    
    # ========================================
    # 메인 자료
    # ========================================
    
    def reroute(
        self,
        patient_id: str,
        previous_diagnosis: DifferentialDiagnosisResult,
        treatment_response: TreatmentResponse,
        temporal_history: Optional[TemporalHistory] = None,
    ) -> ReroutingDecision:
        """
        Outcome 자료 → diagnosis 재구성.
        """
        # 1. 이전 진단의 expected response 자료
        prev_primary = previous_diagnosis.primary_diagnosis
        if not prev_primary or prev_primary not in self.EXPECTED_RESPONSES:
            return self._no_change_decision(
                patient_id, previous_diagnosis, "previous_primary_unknown"
            )
        
        expected = self.EXPECTED_RESPONSES[prev_primary]
        
        # 2. 실제 반응 자료 분석
        actual_clinical_changes = treatment_response.clinical_changes
        actual_cognitive_changes = treatment_response.cognitive_changes
        
        # 3. 임상 fit 평가
        response_fit = self._compute_response_fit(
            expected=expected,
            actual_clinical=actual_clinical_changes,
            actual_cognitive=actual_cognitive_changes,
        )
        
        # 4. 진단 update 자료
        if response_fit >= 0.60:
            # 좋은 fit → primary 진단 자료 유지
            return self._no_change_decision(
                patient_id, previous_diagnosis,
                "treatment_response_confirms_diagnosis"
            )
        
        # Fit 자료 안 좋음 → 재진단 자료
        return self._rediagnose(
            patient_id=patient_id,
            previous_diagnosis=previous_diagnosis,
            treatment_response=treatment_response,
            response_fit=response_fit,
            temporal_history=temporal_history,
        )
    
    # ========================================
    # Helper functions
    # ========================================
    
    def _compute_response_fit(
        self,
        expected: dict,
        actual_clinical: dict[str, float],
        actual_cognitive: dict[str, float],
    ) -> float:
        """
        예상 vs 실제 반응 자료 매칭 자료.
        
        Cosine similarity on expected/actual change vectors.
        """
        # Clinical 자료
        exp_clin = expected["expected_improvements"]
        clin_axes = list(exp_clin.keys())
        exp_clin_vec = np.array([exp_clin[a] for a in clin_axes])
        act_clin_vec = np.array([actual_clinical.get(a, 0.0) for a in clin_axes])
        
        clin_fit = self._cosine_similarity(exp_clin_vec, act_clin_vec)
        
        # Cognitive 자료
        exp_cog = expected["expected_cognitive_changes"]
        cog_axes = list(exp_cog.keys())
        exp_cog_vec = np.array([exp_cog[a] for a in cog_axes])
        act_cog_vec = np.array([actual_cognitive.get(a, 0.0) for a in cog_axes])
        
        cog_fit = self._cosine_similarity(exp_cog_vec, act_cog_vec)
        
        # 결합
        return 0.6 * clin_fit + 0.4 * cog_fit
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """양수 부분 강조 cosine 자료."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.5
        cosine = float(np.dot(a, b) / (norm_a * norm_b))
        return (cosine + 1.0) / 2.0
    
    def _no_change_decision(
        self,
        patient_id: str,
        prev: DifferentialDiagnosisResult,
        reason: str,
    ) -> ReroutingDecision:
        """변경 없음 자료."""
        return ReroutingDecision(
            timestamp=datetime.utcnow(),
            patient_id=patient_id,
            previous_primary=prev.primary_diagnosis or "unknown",
            previous_secondary=prev.secondary_diagnoses,
            updated_primary=prev.primary_diagnosis or "unknown",
            updated_secondary=prev.secondary_diagnoses,
            diagnosis_changed=False,
            change_type="no_change",
            treatment_response_pattern=reason,
            rationale_ko=f"진단 자료 유지 — {reason}",
            posterior_update_magnitude=0.0,
        )
    
    def _rediagnose(
        self,
        patient_id: str,
        previous_diagnosis: DifferentialDiagnosisResult,
        treatment_response: TreatmentResponse,
        response_fit: float,
        temporal_history: Optional[TemporalHistory],
    ) -> ReroutingDecision:
        """
        예상 자료와 다른 자료 → 재진단.
        
        후 상태로 DDE 재실행 + 이전 자료를 prior 자료로 가중.
        """
        # 새 상태 (treatment_response.cognitive_after) 자료로 DDE 자료 재실행
        new_cognitive = treatment_response.cognitive_after
        new_clinical_scores = treatment_response.clinical_after
        
        # Cohort prior: 이전 진단을 약간 덜 가중치 자료 (response 안 좋았으므로)
        weakened_prior = {
            h.diagnosis_id: h.posterior_probability * 0.5  # 절반 자료
            for h in previous_diagnosis.hypotheses
        }
        # 다른 진단 자료들 가능성 자료 ↑
        n_diagnoses = len(self.dde.primary_patterns)
        remaining_prob = 1.0 - sum(weakened_prior.values())
        boost_per_diag = remaining_prob / max(1, n_diagnoses - len(weakened_prior))
        for diag_id in self.dde.primary_patterns:
            if diag_id not in weakened_prior:
                weakened_prior[diag_id] = boost_per_diag
        
        # 정규화
        total = sum(weakened_prior.values())
        if total > 0:
            weakened_prior = {k: v/total for k, v in weakened_prior.items()}
        
        # DDE 재실행
        new_diagnosis = self.dde.diagnose(
            patient_id=patient_id,
            cognitive_levels=new_cognitive,
            clinical_scores=new_clinical_scores,
            symptom_vector=treatment_response.symptom_vector_after if hasattr(treatment_response, 'symptom_vector_after') else {},
            biomarkers=treatment_response.biomarkers_after if hasattr(treatment_response, 'biomarkers_after') else {},
            temporal_history=temporal_history,
            use_cohort_prior=True,
            cohort_prior=weakened_prior,
        )
        
        # 변경 자료 catch
        old_primary = previous_diagnosis.primary_diagnosis
        new_primary = new_diagnosis.primary_diagnosis
        
        if old_primary == new_primary and set(previous_diagnosis.secondary_diagnoses) == set(new_diagnosis.secondary_diagnoses):
            change_type = "no_change"
            diagnosis_changed = False
        elif old_primary != new_primary:
            change_type = "primary_swap"
            diagnosis_changed = True
        elif set(new_diagnosis.secondary_diagnoses) - set(previous_diagnosis.secondary_diagnoses):
            change_type = "secondary_added"
            diagnosis_changed = True
        else:
            change_type = "diagnosis_dropped"
            diagnosis_changed = True
        
        # Treatment response pattern 분석
        response_pattern = self._classify_response_pattern(
            treatment_response, old_primary, new_primary
        )
        
        # Rationale
        rationale = self._build_rationale(
            old_primary, new_primary,
            new_diagnosis.secondary_diagnoses,
            response_pattern, response_fit,
        )
        
        # Posterior 변화 magnitude
        old_top_post = previous_diagnosis.hypotheses[0].posterior_probability if previous_diagnosis.hypotheses else 0.0
        new_top_post = new_diagnosis.hypotheses[0].posterior_probability if new_diagnosis.hypotheses else 0.0
        posterior_change = abs(new_top_post - old_top_post)
        
        # Flag for review
        flag = (
            diagnosis_changed and posterior_change > 0.20
        ) or response_fit < 0.30
        
        return ReroutingDecision(
            timestamp=datetime.utcnow(),
            patient_id=patient_id,
            previous_primary=old_primary or "unknown",
            previous_secondary=previous_diagnosis.secondary_diagnoses,
            updated_primary=new_primary or "unknown",
            updated_secondary=new_diagnosis.secondary_diagnoses,
            diagnosis_changed=diagnosis_changed,
            change_type=change_type,
            treatment_response_pattern=response_pattern,
            rationale_ko=rationale,
            posterior_update_magnitude=posterior_change,
            flagged_for_review=flag,
        )
    
    def _classify_response_pattern(
        self,
        response: TreatmentResponse,
        old_primary: str,
        new_primary: str,
    ) -> str:
        """반응 패턴 자료 분류."""
        # 무효 자료
        primary_target = response.primary_intervention_axis
        primary_change = response.clinical_changes.get(primary_target, 0.0)
        
        if primary_change < 0.05:
            # Primary target 변화 ❌
            # 다른 축에서 변화 컸나?
            other_changes = {
                a: c for a, c in response.clinical_changes.items()
                if a != primary_target
            }
            if other_changes:
                top_other = max(other_changes.items(), key=lambda x: x[1])
                if top_other[1] > 0.10:
                    return f"primary_no_response_secondary_improved_{top_other[0]}"
            return "treatment_no_response"
        
        elif primary_change > 0.15:
            # Primary 자료 잘 반응
            return "expected_response_strong"
        
        elif old_primary != new_primary:
            return "diagnosis_revision_from_response"
        
        return "partial_response"
    
    def _build_rationale(
        self,
        old_primary: str,
        new_primary: str,
        new_secondary: list[str],
        pattern: str,
        fit: float,
    ) -> str:
        """한국어 rationale."""
        parts = []
        
        if old_primary == new_primary:
            parts.append(f"Primary 진단 유지: {old_primary}")
        else:
            parts.append(f"Primary 진단 변경: {old_primary} → {new_primary}")
        
        if new_secondary:
            parts.append(f"공존 자료: {', '.join(new_secondary)}")
        
        parts.append(f"반응 자료 매칭: {fit:.2f}")
        parts.append(f"패턴: {pattern}")
        
        return " | ".join(parts)


def format_rerouting_decision_table(decision: ReroutingDecision) -> str:
    """ReroutingDecision → 한국어 표 출력."""
    lines = []
    lines.append("=" * 72)
    lines.append(f"진단 자료 재구성 결정 — 환자 {decision.patient_id}")
    lines.append(f"시점: {decision.timestamp.strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 72)
    lines.append("")
    
    lines.append("【 이전 진단 → 갱신 진단 】")
    lines.append("-" * 72)
    lines.append(f"  Primary: {decision.previous_primary} → {decision.updated_primary}")
    if decision.previous_secondary or decision.updated_secondary:
        lines.append(f"  Secondary: {decision.previous_secondary} → {decision.updated_secondary}")
    lines.append("")
    
    lines.append("【 변경 자료 】")
    lines.append("-" * 72)
    lines.append(f"  변경 여부: {'예' if decision.diagnosis_changed else '아니오'}")
    lines.append(f"  변경 유형: {decision.change_type}")
    lines.append(f"  반응 패턴: {decision.treatment_response_pattern}")
    lines.append(f"  Posterior 변화: {decision.posterior_update_magnitude:.3f}")
    lines.append("")
    
    lines.append("【 임상 자료 】")
    lines.append("-" * 72)
    lines.append(f"  근거: {decision.rationale_ko}")
    if decision.flagged_for_review:
        lines.append(f"  ⚠ 임상가 검토 필요")
    lines.append("")
    lines.append("=" * 72)
    return "\n".join(lines)
