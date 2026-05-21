"""
CNA v6 — Clinical Report Generator

5축 임상 예측 + 관계표 + 환자 선택 옵션.

할비 catch:
"이 다섯개 지표내에서의 관계 및 정도를 표시해줘야해 그래서 만일 이 개인이
이중 하나를 채택해 치료나 훈련을 하고 싶어한다면 이를 기반으로 훈련하는
프로토콜을 짜는 단계로 사용하는거야"

Boston Neuromind LLC · 2026
"""

from datetime import datetime
from typing import Optional

from cna_core.types import (
    CognitiveAxis, ClinicalAxis,
    COGNITIVE_AXES, CLINICAL_AXES,
    COGNITIVE_AXIS_KOREAN, CLINICAL_AXIS_KOREAN,
    ClinicalAxisReport, AxisRelationship, AlternativePath, ClinicalReport,
)
from cna_core.cognitive_clinical_mapper import CognitiveClinicalMapper


# ============================================================
# 추천 우선순위 계산
# ============================================================

def compute_recommendation_priority(
    axis: ClinicalAxis,
    score: float,
    severity_tier: str,
    patient_choice: Optional[ClinicalAxis] = None,
    impact_on_others: Optional[dict] = None,
) -> int:
    """
    축 우선순위 (1=가장 우선, 5=가장 마지막).
    
    순위:
    1. 환자 선택 = 1순위 (autonomy)
    2. Crisis-level (priority tier) = 2순위
    3. Leverage 큰 자리 (다른 축에 영향) = 3순위
    4. 약화 자리 (needs_attention) = 4순위
    5. 안정 자리 (good/strong) = 5순위
    """
    impact_on_others = impact_on_others or {}
    
    if patient_choice == axis:
        return 1
    
    if severity_tier == "priority":
        return 2
    
    total_leverage = sum(abs(v) for v in impact_on_others.values())
    if total_leverage > 1.5 and severity_tier in ("needs_attention", "moderate"):
        return 3
    
    if severity_tier == "needs_attention":
        return 4
    
    return 5


# ============================================================
# 부수 효과 계산
# ============================================================

def compute_collateral_benefit(
    axis: ClinicalAxis,
    axes_reports: dict,
    relationships: list,
) -> float:
    """이 축 개선 시 다른 축에 미치는 부수 효과 합."""
    total = 0.0
    for r in relationships:
        if r["axis_a"] == axis or r["axis_b"] == axis:
            other = r["axis_b"] if r["axis_a"] == axis else r["axis_a"]
            other_score = axes_reports[other].score
            total += abs(r["strength"]) * (1.0 - other_score) * 0.5
    return round(total, 3)


def build_alternative_preview(
    axis: ClinicalAxis,
    axes_reports: dict,
    relationships: list,
) -> str:
    """대안 축 선택 시 미리보기."""
    axis_report = axes_reports[axis]
    collateral_summary = []
    
    for r in relationships[:3]:
        if r["axis_a"] == axis or r["axis_b"] == axis:
            other = r["axis_b"] if r["axis_a"] == axis else r["axis_a"]
            other_kr = CLINICAL_AXIS_KOREAN[other]
            if r["strength"] > 0:
                collateral_summary.append(f"{other_kr} 동반 개선")
            else:
                collateral_summary.append(f"{other_kr} 부수 안정")
    
    return (
        f"{CLINICAL_AXIS_KOREAN[axis]} 선택 시: "
        f"현재 {axis_report.interpretation}, "
        f"부수 효과 — {', '.join(collateral_summary[:2])}"
    )


def build_rationale(
    primary: ClinicalAxis,
    axes_reports: dict,
    relationships: list,
) -> str:
    """시스템 추천 이유."""
    primary_report = axes_reports[primary]
    parts = [
        f"1순위 추천: {primary_report.axis_korean}",
        f"현재 상태: {primary_report.interpretation}",
    ]
    
    if primary_report.contributing_cognitive_axes:
        top_cog = max(
            primary_report.contributing_cognitive_axes.items(),
            key=lambda x: abs(x[1]),
        )
        cog_kr = COGNITIVE_AXIS_KOREAN.get(top_cog[0], top_cog[0])
        parts.append(f"주요 인지 영향: {cog_kr} (기여도 {top_cog[1]:+.2f})")
    
    primary_relationships = [
        r for r in relationships
        if r["axis_a"] == primary or r["axis_b"] == primary
    ]
    primary_relationships.sort(key=lambda r: abs(r["strength"]), reverse=True)
    if primary_relationships:
        top_rel = primary_relationships[0]
        other = top_rel["axis_b"] if top_rel["axis_a"] == primary else top_rel["axis_a"]
        parts.append(
            f"파급 효과: {CLINICAL_AXIS_KOREAN[primary]} 개선 → "
            f"{CLINICAL_AXIS_KOREAN[other]} 영향 (강도 {abs(top_rel['strength']):.2f})"
        )
    
    return " | ".join(parts)


# ============================================================
# 메인 리포트 생성
# ============================================================

def generate_clinical_report(
    patient_id: str,
    cognitive_levels: dict[CognitiveAxis, float],
    mapper: CognitiveClinicalMapper,
    patient_choice: Optional[ClinicalAxis] = None,
) -> ClinicalReport:
    """
    Fischer 5축 → 임상 5축 예측 + 관계 + 추천 + 대안.
    환자에게 보여줄 자리.
    """
    # 1. 5축 예측
    clinical_state = mapper.predict_clinical_state(cognitive_levels)
    
    # 2. 관계 매트릭스
    raw_relationships = mapper.compute_pairwise_relationships(clinical_state)
    
    # 3. 각 축의 leverage
    axis_leverages = {ax: {} for ax in CLINICAL_AXES}
    for rel in raw_relationships:
        a, b = rel["axis_a"], rel["axis_b"]
        axis_leverages[a][b] = rel["strength"]
        axis_leverages[b][a] = rel["strength"]
    
    # 4. 5축 리포트 구성
    axes_reports = {}
    priority_inputs = {}
    
    for axis in CLINICAL_AXES:
        state = clinical_state[axis]
        severity = mapper.get_severity_tier(axis, state["score"])
        priority = compute_recommendation_priority(
            axis=axis,
            score=state["score"],
            severity_tier=severity,
            patient_choice=patient_choice,
            impact_on_others=axis_leverages[axis],
        )
        
        axes_reports[axis] = ClinicalAxisReport(
            axis=axis,
            axis_korean=CLINICAL_AXIS_KOREAN[axis],
            score=state["score"],
            confidence=state["confidence"],
            interpretation=state["interpretation"],
            severity_tier=severity,
            contributing_cognitive_axes=state["contributing_cognitive"],
            recommendation_priority=priority,
        )
        priority_inputs[axis] = priority
    
    # 5. 관계 구성
    relationships = []
    for rel in raw_relationships:
        score_a = clinical_state[rel["axis_a"]]["score"]
        score_b = clinical_state[rel["axis_b"]]["score"]
        weakness_factor = (2.0 - score_a - score_b) / 2.0
        leverage = abs(rel["strength"]) * weakness_factor
        
        relationships.append(AxisRelationship(
            axis_a=rel["axis_a"],
            axis_b=rel["axis_b"],
            strength=rel["strength"],
            type=rel["type"],
            description=rel["description"],
            leverage_score=round(leverage, 3),
        ))
    
    relationships.sort(key=lambda r: r.leverage_score, reverse=True)
    
    # 6. 1순위 추천
    if patient_choice:
        primary = patient_choice
        rationale = f"환자 선택: {CLINICAL_AXIS_KOREAN[patient_choice]}. 환자 자율성 우선."
    else:
        primary = min(priority_inputs.items(), key=lambda x: x[1])[0]
        rationale = build_rationale(primary, axes_reports, raw_relationships)
    
    # 7. 대안 경로
    alternatives = []
    for axis in CLINICAL_AXES:
        if axis == primary:
            continue
        alternatives.append(AlternativePath(
            axis=axis,
            axis_korean=CLINICAL_AXIS_KOREAN[axis],
            expected_collateral_benefit=compute_collateral_benefit(
                axis, axes_reports, raw_relationships
            ),
            preview_text=build_alternative_preview(
                axis, axes_reports, raw_relationships
            ),
        ))
    
    alternatives.sort(key=lambda a: a.expected_collateral_benefit, reverse=True)
    
    return ClinicalReport(
        patient_id=patient_id,
        timestamp=datetime.utcnow(),
        cognitive_levels=dict(cognitive_levels),
        axes=axes_reports,
        relationships=relationships,
        primary_recommendation=primary,
        rationale=rationale,
        alternative_paths=alternatives,
    )


# ============================================================
# 표 출력
# ============================================================

def format_report_as_table(report: ClinicalReport) -> str:
    """리포트 → 한국어 표 출력 (CLI/콘솔용)."""
    lines = []
    lines.append("=" * 72)
    lines.append(f"임상 자료 리포트 — 환자 {report.patient_id}")
    lines.append(f"생성: {report.timestamp.strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 72)
    lines.append("")
    
    # Section 1: Fischer 인지 측정
    lines.append("【 Fischer 인지 5축 측정 자료 】")
    lines.append("-" * 72)
    for axis in COGNITIVE_AXES:
        level = report.cognitive_levels.get(axis, 0.0)
        bar_len = int((level - 7.0) / 6.0 * 30)
        bar = "█" * max(0, bar_len) + "░" * (30 - max(0, bar_len))
        axis_kr = COGNITIVE_AXIS_KOREAN[axis]
        lines.append(f"  {axis_kr:14s} [{bar}] L{level:.1f}")
    lines.append("")
    
    # Section 2: 임상 5축 예측표
    lines.append("【 임상 5축 예측 자료 】")
    lines.append("-" * 72)
    lines.append(f"  {'영역':<14s} {'점수':<8s} {'단계':<18s} {'우선':<6s} 주요 기여 인지축")
    lines.append("  " + "-" * 68)
    
    sorted_axes = sorted(
        report.axes.values(),
        key=lambda a: a.recommendation_priority,
    )
    for ax in sorted_axes:
        tier_display = {
            "strong": "매우 우수 ★",
            "good": "우수 ✓",
            "moderate": "보통",
            "needs_attention": "주의 ⚠",
            "priority": "임상 우선 ⚠⚠",
        }.get(ax.severity_tier, ax.severity_tier)
        
        if ax.contributing_cognitive_axes:
            top = max(ax.contributing_cognitive_axes.items(), key=lambda x: abs(x[1]))
            top_kr = COGNITIVE_AXIS_KOREAN.get(top[0], top[0])
            top_str = f"{top_kr} ({top[1]:+.2f})"
        else:
            top_str = "-"
        
        lines.append(
            f"  {ax.axis_korean:<14s} {ax.score:.2f}    "
            f"{tier_display:<18s} #{ax.recommendation_priority}    "
            f"{top_str}"
        )
    lines.append("")
    
    # Section 3: 5축 관계표
    lines.append("【 5축 간 관계 자료 (Leverage 순) 】")
    lines.append("-" * 72)
    lines.append(f"  {'A 축':<14s} {'관계':<14s} {'B 축':<14s} {'강도':<8s} Leverage")
    lines.append("  " + "-" * 68)
    
    for rel in report.relationships:
        rel_type_kr = "동반 변화" if rel.type == "positive_coupling" else "반대 변화"
        rel_arrow = "↑↑" if rel.strength > 0 else "↑↓"
        a_kr = CLINICAL_AXIS_KOREAN[rel.axis_a]
        b_kr = CLINICAL_AXIS_KOREAN[rel.axis_b]
        lines.append(
            f"  {a_kr:<14s} "
            f"{rel_arrow + ' ' + rel_type_kr:<14s} "
            f"{b_kr:<14s} "
            f"{abs(rel.strength):.2f}     "
            f"{rel.leverage_score:.2f}"
        )
    lines.append("")
    
    # Section 4: 시스템 추천
    lines.append("【 시스템 추천 】")
    lines.append("-" * 72)
    lines.append(f"  1순위: {CLINICAL_AXIS_KOREAN[report.primary_recommendation]}")
    lines.append(f"  근거: {report.rationale}")
    lines.append("")
    
    # Section 5: 환자 선택 대안
    lines.append("【 환자 선택 대안 자료 】")
    lines.append("-" * 72)
    lines.append("  환자가 다른 영역 선택해도 OK. 각 자리 부수 효과:")
    for i, alt in enumerate(report.alternative_paths[:4], 1):
        lines.append(f"  {i}. {alt.preview_text}")
        lines.append(f"     부수 효과 점수: {alt.expected_collateral_benefit:.2f}")
    lines.append("")
    
    # Section 6: 다음 단계
    lines.append("【 다음 단계 】")
    lines.append("-" * 72)
    lines.append("  환자가 영역 결정 → 자동 훈련 프로토콜 생성")
    lines.append("  → Loop 4 Deliver (임상가 검토 + 환자 전달)")
    lines.append("=" * 72)
    
    return "\n".join(lines)
