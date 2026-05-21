"""
CNA v7 — Comorbidity Decomposition

한 임상 점수를 source별로 분해.
예: Attention 0.39 = ADHD primary 0.25 + 불안 secondary 0.10 + 우울 secondary 0.04

원리:
1. 각 진단의 cognitive_signature × patient_cognitive_weakness
2. 진단별 cognitive→clinical 영향 (W_pos / W_neg 행렬)
3. 각 진단의 posterior probability × 영향 = source contribution

Mediation logic (Hayes PROCESS 자료):
  Total effect = Direct (primary) + Indirect (secondary via primary)
  
임상적 의미: 같은 임상 점수, 다른 source → 다른 치료 자료

Boston Neuromind LLC · 2026
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from cna_core.types import CognitiveAxis, ClinicalAxis, CLINICAL_AXES, COGNITIVE_AXES, CLINICAL_AXIS_KOREAN
from cna_core.cognitive_clinical_mapper import CognitiveClinicalMapper
from cna_core.differential_diagnosis import (
    DifferentialDiagnosisResult,
    DiagnosticHypothesis,
)


class SourceContribution(BaseModel):
    """한 source가 한 임상 점수에 기여하는 자료."""
    source_id: str              # diagnosis id (e.g., "adhd_inattentive")
    source_name_ko: str
    contribution: float         # 0.0-1.0 (이 source가 임상 점수 약화에 기여)
    posterior_prob: float       # 이 진단의 사후 확률
    primary_pathway: bool       # primary 진단 자료?
    cognitive_axes_involved: list[str]
    interpretation_ko: str


class DecomposedClinicalScore(BaseModel):
    """한 임상축 점수의 source별 분해."""
    clinical_axis: ClinicalAxis
    clinical_axis_ko: str
    total_score: float                          # 원래 점수
    total_impairment: float                     # 1.0 - score (약화 정도)
    
    sources: list[SourceContribution]
    sources_explanation: float                  # 분해 자료로 설명 가능한 % (남은 자료 = 잔차)
    residual: float                             # 설명 안 되는 자료
    
    # 임상 자료
    dominant_source: Optional[str] = None
    treatment_target: str = ""                  # "primary_first" | "concurrent" | "monitor"


class ComorbidityProfile(BaseModel):
    """전체 환자의 comorbidity 분해 프로필."""
    patient_id: str
    timestamp: datetime
    
    decomposed_axes: dict[str, DecomposedClinicalScore]
    
    # 종합 자료
    primary_source: str
    secondary_sources: list[str]
    
    # 치료 권고
    intervention_priority: list[dict]   # [{source, priority, rationale}]


class ComorbidityDecomposer:
    """공존 진단 분해 엔진."""
    
    def __init__(
        self,
        mapper: CognitiveClinicalMapper,
        dde_engine,  # DifferentialDiagnosisEngine (순환 import 방지)
    ):
        self.mapper = mapper
        self.dde = dde_engine
    
    def decompose(
        self,
        patient_id: str,
        cognitive_levels: dict[CognitiveAxis, float],
        clinical_scores: dict[ClinicalAxis, dict],
        dde_result: DifferentialDiagnosisResult,
    ) -> ComorbidityProfile:
        """
        환자 임상 5축 점수 → source별 분해.
        
        Args:
            cognitive_levels: Fischer 5축 자료
            clinical_scores: ClinicalAxisReport.dict() (score 키 포함)
            dde_result: DDE 결과 (posterior + primary/secondary)
        """
        # 각 임상축 분해
        decomposed_axes = {}
        
        for clin_axis in CLINICAL_AXES:
            # clinical_scores에서 점수 추출
            if isinstance(clinical_scores.get(clin_axis), dict):
                total_score = clinical_scores[clin_axis].get("score", 0.5)
            else:
                total_score = clinical_scores.get(clin_axis, 0.5)
            
            total_impairment = 1.0 - total_score
            
            # 각 진단 가설이 이 임상축에 기여하는 자료 계산
            sources = []
            
            for hyp in dde_result.hypotheses:
                if hyp.posterior_probability < 0.05:
                    continue  # 무시
                
                contribution = self._compute_source_contribution(
                    hyp=hyp,
                    cognitive_levels=cognitive_levels,
                    target_clinical_axis=clin_axis,
                )
                
                if contribution > 0.02:  # 유의미한 기여만
                    sources.append(SourceContribution(
                        source_id=hyp.diagnosis_id,
                        source_name_ko=hyp.name_ko,
                        contribution=contribution,
                        posterior_prob=hyp.posterior_probability,
                        primary_pathway=hyp.is_primary,
                        cognitive_axes_involved=self._get_involved_cog_axes(
                            hyp.diagnosis_id, cognitive_levels
                        ),
                        interpretation_ko=self._interpret_source(
                            hyp, clin_axis, contribution
                        ),
                    ))
            
            # 기여 순 정렬
            sources.sort(key=lambda s: s.contribution, reverse=True)
            
            # 설명 % 계산
            total_contribution = sum(s.contribution for s in sources)
            sources_explanation = (
                total_contribution / total_impairment
                if total_impairment > 0.01 else 0.0
            )
            sources_explanation = min(1.0, sources_explanation)
            
            residual = max(0.0, total_impairment - total_contribution)
            
            # Dominant source
            dominant = sources[0].source_id if sources else None
            
            # 치료 target
            treatment_target = self._determine_treatment_target(
                sources, dde_result
            )
            
            decomposed_axes[clin_axis] = DecomposedClinicalScore(
                clinical_axis=clin_axis,
                clinical_axis_ko=CLINICAL_AXIS_KOREAN[clin_axis],
                total_score=total_score,
                total_impairment=total_impairment,
                sources=sources,
                sources_explanation=sources_explanation,
                residual=residual,
                dominant_source=dominant,
                treatment_target=treatment_target,
            )
        
        # 종합 자료
        primary_source = dde_result.primary_diagnosis or "unknown"
        secondary_sources = dde_result.secondary_diagnoses
        
        # 개입 우선순위
        intervention_priority = self._compute_intervention_priority(
            decomposed_axes, dde_result
        )
        
        return ComorbidityProfile(
            patient_id=patient_id,
            timestamp=datetime.utcnow(),
            decomposed_axes=decomposed_axes,
            primary_source=primary_source,
            secondary_sources=secondary_sources,
            intervention_priority=intervention_priority,
        )
    
    # ========================================
    # Helper functions
    # ========================================
    
    def _compute_source_contribution(
        self,
        hyp: DiagnosticHypothesis,
        cognitive_levels: dict[str, float],
        target_clinical_axis: str,
    ) -> float:
        """
        한 진단이 한 임상축 약화에 기여하는 정도.
        
        Formula:
          contribution = P(diagnosis) × signature_alignment × clinical_pathway_strength
        
        signature_alignment: 이 환자 인지 자료가 이 진단의 패턴과 얼마나 일치
        clinical_pathway_strength: 이 진단이 이 임상축에 미치는 영향 (canonical)
        """
        # Posterior 자료
        posterior = hyp.posterior_probability
        
        # 진단의 canonical clinical signature
        pattern = self.dde.primary_patterns[hyp.diagnosis_id]
        canonical_clinical_impact = pattern["clinical_signature"].get(target_clinical_axis, 0.0)
        
        # 환자의 인지 약점이 이 진단 패턴과 매칭하는 정도
        signature_alignment = hyp.cognitive_match
        
        # 기여도 = posterior × alignment × canonical_impact
        contribution = posterior * signature_alignment * canonical_clinical_impact
        
        return min(1.0, contribution)
    
    def _get_involved_cog_axes(
        self,
        diagnosis_id: str,
        cognitive_levels: dict[str, float],
    ) -> list[str]:
        """이 진단이 영향 미치는 주요 인지축 자료."""
        pattern = self.dde.primary_patterns[diagnosis_id]
        signature = pattern["cognitive_signature"]
        
        # 약화 큰 인지축 (signature > 0.50)
        involved = [
            axis for axis, weakness in signature.items()
            if weakness > 0.50
        ]
        return involved
    
    def _interpret_source(
        self,
        hyp: DiagnosticHypothesis,
        clinical_axis: str,
        contribution: float,
    ) -> str:
        """source 기여 임상적 해석."""
        clin_kr = CLINICAL_AXIS_KOREAN[clinical_axis]
        
        if hyp.is_primary:
            role = "1차"
        elif hyp.is_comorbid:
            role = "공존"
        else:
            role = "가능"
        
        return (
            f"{hyp.name_ko} ({role}, 사후확률 {hyp.posterior_probability:.0%}) → "
            f"{clin_kr} 약화의 {contribution:.2f} 기여"
        )
    
    def _determine_treatment_target(
        self,
        sources: list[SourceContribution],
        dde_result: DifferentialDiagnosisResult,
    ) -> str:
        """이 임상축에 대한 치료 자료."""
        if not sources:
            return "monitor"  # 분해 안 됨, 관찰
        
        dominant = sources[0]
        
        # Primary가 dominant
        if dominant.primary_pathway:
            return "primary_first"
        
        # Comorbidity 패턴
        if dde_result.comorbidity_pattern:
            return "concurrent"
        
        # 단일 source
        if len(sources) == 1:
            return "primary_first"
        
        return "concurrent"
    
    def _compute_intervention_priority(
        self,
        decomposed: dict[str, DecomposedClinicalScore],
        dde_result: DifferentialDiagnosisResult,
    ) -> list[dict]:
        """개입 우선순위."""
        priorities = []
        
        # Primary diagnosis 1순위
        if dde_result.primary_diagnosis:
            primary = dde_result.primary_diagnosis
            
            # Primary 진단이 가장 큰 영향 미치는 임상축
            affected_axes = []
            for axis, decomp in decomposed.items():
                for src in decomp.sources:
                    if src.source_id == primary:
                        affected_axes.append((axis, src.contribution))
                        break
            
            affected_axes.sort(key=lambda x: x[1], reverse=True)
            top_axis = affected_axes[0][0] if affected_axes else "attention"
            
            priorities.append({
                "rank": 1,
                "source": primary,
                "target_clinical_axis": top_axis,
                "rationale": f"Primary 진단 자료 1순위 — {dde_result.treatment_rationale}",
            })
        
        # Secondary 진단
        for i, secondary in enumerate(dde_result.secondary_diagnoses, 2):
            affected = []
            for axis, decomp in decomposed.items():
                for src in decomp.sources:
                    if src.source_id == secondary:
                        affected.append((axis, src.contribution))
                        break
            affected.sort(key=lambda x: x[1], reverse=True)
            top = affected[0][0] if affected else "anxiety"
            
            priorities.append({
                "rank": i,
                "source": secondary,
                "target_clinical_axis": top,
                "rationale": f"공존 자료 {i}순위 — primary 치료 후 잔존 증상 평가",
            })
        
        return priorities


def format_comorbidity_profile_table(profile: ComorbidityProfile) -> str:
    """ComorbidityProfile → 한국어 표 출력."""
    lines = []
    lines.append("=" * 76)
    lines.append(f"공존 진단 분해 자료 — 환자 {profile.patient_id}")
    lines.append("=" * 76)
    lines.append("")
    
    lines.append(f"【 종합 자료 】")
    lines.append("-" * 76)
    lines.append(f"  Primary source: {profile.primary_source}")
    if profile.secondary_sources:
        lines.append(f"  Secondary sources: {', '.join(profile.secondary_sources)}")
    lines.append("")
    
    lines.append(f"【 임상 5축 source 분해 】")
    lines.append("-" * 76)
    
    for axis in CLINICAL_AXES:
        decomp = profile.decomposed_axes.get(axis)
        if not decomp:
            continue
        
        lines.append(f"\n  ▶ {decomp.clinical_axis_ko}")
        lines.append(f"     원 점수: {decomp.total_score:.2f} (약화 {decomp.total_impairment:.2f})")
        lines.append(f"     설명력: {decomp.sources_explanation:.0%}")
        
        if decomp.sources:
            for src in decomp.sources:
                marker = "★" if src.primary_pathway else "•"
                lines.append(
                    f"     {marker} {src.source_name_ko:25s} "
                    f"기여 {src.contribution:.3f} "
                    f"(posterior {src.posterior_prob:.0%})"
                )
        
        if decomp.residual > 0.05:
            lines.append(f"     잔차 (미설명): {decomp.residual:.3f}")
        
        lines.append(f"     치료 target: {decomp.treatment_target}")
    
    lines.append("")
    lines.append(f"【 개입 우선순위 】")
    lines.append("-" * 76)
    for p in profile.intervention_priority:
        lines.append(f"  {p['rank']}순위: {p['source']}")
        lines.append(f"     주 영향 임상축: {p['target_clinical_axis']}")
        lines.append(f"     이유: {p['rationale']}")
    
    lines.append("")
    lines.append("=" * 76)
    return "\n".join(lines)
