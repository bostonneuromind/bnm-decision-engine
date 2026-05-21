"""
CNA v6 — Training Protocol Generator

할비 catch:
"환자가 영역 선택 → 자동 훈련 프로토콜 생성 자리"
"이것이 완벽하게 완결되면 이 세개에 대한 훈련 프로토콜을 짜는게 다음 목표야"

환자가 5축 중 하나 선택 → 4주 (또는 사용자 지정) 프로토콜 자동 생성.
프로토콜 = 카드 시퀀스 + 일정 + 측정 + 성공 기준.

Boston Neuromind LLC · 2026
"""

import uuid
from datetime import datetime
from typing import Optional

from cna_core.types import (
    ClinicalAxis, Card, V1State, V2Desire, V3Skill, V4Trajectory,
    TrainingProtocol, ProtocolSession, ClinicalReport,
)
from cna_core.free_energy_scorer import FreeEnergyScorer
from cna_core.card_deck import get_default_card_deck


# ============================================================
# 프로토콜 템플릿 (5축별)
# ============================================================

PROTOCOL_TEMPLATES = {
    "attention": {
        "target_duration_weeks": 4,
        "sessions_per_week": 3,
        "preferred_axes": ["sustained_attention", "working_memory"],
        "measurement_focus": ["cpt_omissions_zscore", "cpt_rt_variability", "nback_accuracy"],
        "weekly_progression": "complexity_ramp",  # 매주 난이도 ↑
        "success_criteria": {
            "cpt_omissions_zscore_improvement": 0.3,
            "self_report_focus": 0.5,
        },
    },
    "learning": {
        "target_duration_weeks": 4,
        "sessions_per_week": 4,
        "preferred_axes": ["working_memory", "sustained_attention", "self_awareness"],
        "measurement_focus": ["nback_accuracy", "learning_retention_24h"],
        "weekly_progression": "consolidation",  # 반복 + 확장
        "success_criteria": {
            "nback_accuracy_improvement": 0.10,
            "self_report_learning": 0.5,
        },
    },
    "peak_performance": {
        "target_duration_weeks": 4,
        "sessions_per_week": 3,
        "preferred_axes": ["time_awareness", "working_memory", "sustained_attention"],
        "measurement_focus": ["time_estimation_error_pct", "hrv_rmssd", "nback_accuracy"],
        "weekly_progression": "skill_stacking",
        "success_criteria": {
            "time_estimation_error_improvement_pct": 5.0,
            "nback_accuracy_improvement": 0.05,
        },
    },
    "anxiety": {
        "target_duration_weeks": 4,
        "sessions_per_week": 5,  # 더 자주
        "preferred_axes": ["emotional_regulation", "self_awareness"],
        "measurement_focus": ["hrv_rmssd", "anxiety_self_report", "vsr_consistency"],
        "weekly_progression": "exposure_gradient",  # 점진 노출
        "success_criteria": {
            "hrv_rmssd_improvement": 10.0,
            "self_report_anxiety_reduction": 0.4,
        },
    },
    "depression": {
        "target_duration_weeks": 8,  # BA 표준 (Dimidjian et al. 2006)
        "sessions_per_week": 4,
        "preferred_axes": ["self_awareness", "emotional_regulation"],
        "measurement_focus": ["mood_self_report", "behavioral_activation_count", "hrv_rmssd", "phq9_total"],
        "weekly_progression": "behavioral_activation",
        "success_criteria": {
            "mood_improvement": 0.4,
            "behavioral_activation_count": 5,  # 주당
            "phq9_total_reduction": 5,  # PHQ-9 5점 감소 = 임상적 유의 자료
        },
    },
}


# ============================================================
# 카드 시퀀싱 알고리즘
# ============================================================

def _filter_cards_for_axis(
    cards: list[Card],
    axis: ClinicalAxis,
) -> list[Card]:
    """해당 임상축 타겟 카드만 필터링."""
    return [c for c in cards if axis in c.target_clinical_axes]


def _sequence_cards_progressively(
    candidate_cards: list[Card],
    n_sessions: int,
    v3_initial: V3Skill,
    progression_type: str,
) -> list[list[Card]]:
    """
    n_sessions 동안 카드 시퀀싱.
    
    Progression types:
    - complexity_ramp: 매주 Fischer level 0.5씩 ↑
    - consolidation: 반복 + 확장
    - skill_stacking: 점진 누적
    - exposure_gradient: 짧은 노출에서 긴 노출로
    - behavioral_activation: 작은 활동 → 큰 활동
    """
    # 카드 난이도 순 정렬 (target Fischer level 평균)
    def difficulty(card: Card) -> float:
        if not card.target_fischer_levels:
            return 8.5
        return sum(card.target_fischer_levels.values()) / len(card.target_fischer_levels)
    
    sorted_cards = sorted(candidate_cards, key=difficulty)
    
    # 현재 환자 평균 level
    if v3_initial.axis_levels:
        current_avg = sum(v3_initial.axis_levels.values()) / len(v3_initial.axis_levels)
    else:
        current_avg = 9.0
    
    sessions_cards = []
    
    if progression_type == "complexity_ramp":
        # 매 세션마다 카드 회전 자료 - level matching + 다양성
        n_cards = len(sorted_cards)
        for i in range(n_sessions):
            target_level = current_avg + (i / n_sessions) * 1.5
            
            # Level matching 카드 자료
            level_matched = [
                card for card in sorted_cards
                if abs(difficulty(card) - target_level) < 0.7
            ]
            
            if level_matched:
                idx = i % len(level_matched)
                session_cards = [level_matched[idx]]
                if len(level_matched) > 1:
                    second_idx = (i + 1) % len(level_matched)
                    if second_idx != idx:
                        session_cards.append(level_matched[second_idx])
            else:
                session_cards = [sorted_cards[i % n_cards]]
            
            sessions_cards.append(session_cards)
    
    elif progression_type == "consolidation":
        # 처음 절반: 같은 핵심 3장 회전, 후반: 더 다양한 자료 확장
        n_cards = len(sorted_cards)
        half = n_sessions // 2
        for i in range(n_sessions):
            if i < half:
                # 반복 phase: 핵심 3장 자료 회전
                core_cards = sorted_cards[:min(3, n_cards)]
                idx = i % len(core_cards)
            else:
                # 확장 phase: 전체 회전
                idx = (i - half) % n_cards
            sessions_cards.append([sorted_cards[idx]])
    
    elif progression_type == "exposure_gradient":
        # 짧은 → 긴 카드 (점진 노출)
        by_duration = sorted(candidate_cards, key=lambda c: c.cost_minutes)
        n_cards = len(by_duration)
        for i in range(n_sessions):
            # 3단계 phase 자료
            phase_idx = int((i / n_sessions) * 3)  # 0, 1, 2
            phase_size = max(1, n_cards // 3)
            phase_start = phase_idx * phase_size
            phase_end = min(phase_start + phase_size, n_cards)
            phase_cards = by_duration[phase_start:phase_end]
            if not phase_cards:
                phase_cards = by_duration[-phase_size:] if n_cards > 0 else []
            
            if phase_cards:
                idx = i % len(phase_cards)
                sessions_cards.append([phase_cards[idx]])
            else:
                sessions_cards.append([by_duration[i % n_cards]])
    
    elif progression_type == "behavioral_activation":
        # safe_for_crisis 카드부터 → 더 도전적
        # 모든 카드 회전 자료 사용 (반복 방지)
        safe_first = sorted(
            candidate_cards,
            key=lambda c: (not c.safe_for_crisis, c.cost_minutes),
        )
        n_cards = len(safe_first)
        for i in range(n_sessions):
            # Phase 자료: 초반 1/3 = safe, 중반 1/3 = 중간, 후반 1/3 = 도전적
            phase = i / n_sessions
            phase_start = int(phase * n_cards * 0.7)
            phase_end = min(phase_start + 3, n_cards)
            available = safe_first[phase_start:phase_end]
            if not available:
                available = safe_first[-3:]
            # Phase 내에서 순환
            idx = i % len(available)
            sessions_cards.append([available[idx]])
    
    else:  # skill_stacking (default)
        # 카드 다양성 자료 보장
        n_cards = len(sorted_cards)
        for i in range(n_sessions):
            target_level = current_avg + (i / n_sessions) * 1.0
            session_cards = []
            
            # 난이도 매칭 카드 자료
            level_matched = [
                card for card in sorted_cards
                if abs(difficulty(card) - target_level) < 1.0
            ]
            
            if level_matched:
                # 회전 자료 적용 (반복 방지)
                rotated_idx = i % len(level_matched)
                session_cards = [level_matched[rotated_idx]]
                # 두 번째 카드 자료 (다른 카드)
                if len(level_matched) > 1:
                    second_idx = (i + 1) % len(level_matched)
                    if second_idx != rotated_idx:
                        session_cards.append(level_matched[second_idx])
            else:
                # Fallback: 전체에서 회전
                session_cards = [sorted_cards[i % n_cards]]
            
            sessions_cards.append(session_cards)
    
    return sessions_cards


# ============================================================
# 메인 프로토콜 생성
# ============================================================

def generate_training_protocol(
    patient_id: str,
    selected_axis: ClinicalAxis,
    v1: V1State,
    v2: V2Desire,
    v3: V3Skill,
    v4: V4Trajectory,
    clinical_report: Optional[ClinicalReport] = None,
    custom_weeks: Optional[int] = None,
    available_cards: Optional[list[Card]] = None,
) -> TrainingProtocol:
    """
    환자 선택 → 자동 훈련 프로토콜 생성.
    
    Process:
    1. 선택 축 템플릿 조회
    2. 해당 축 카드 필터링
    3. Free Energy scoring으로 후보 정렬
    4. Progressive sequencing
    5. 주간 측정 정보
    6. 성공 기준 + 예상 변화 자료
    """
    template = PROTOCOL_TEMPLATES[selected_axis]
    weeks = custom_weeks or template["target_duration_weeks"]
    sessions_per_week = template["sessions_per_week"]
    total_sessions = weeks * sessions_per_week
    
    # 카드 풀
    all_cards = available_cards or get_default_card_deck()
    axis_cards = _filter_cards_for_axis(all_cards, selected_axis)
    
    if not axis_cards:
        raise ValueError(f"No cards available for axis: {selected_axis}")
    
    # Free Energy로 우선순위 정렬 (현재 환자 자료 기준)
    scorer = FreeEnergyScorer()
    scored = scorer.score(axis_cards, v1, v2, v3, v4, top_n=len(axis_cards))
    top_cards = [s.card for s in scored]
    
    # Progressive sequencing
    sessions_card_lists = _sequence_cards_progressively(
        candidate_cards=top_cards,
        n_sessions=total_sessions,
        v3_initial=v3,
        progression_type=template["weekly_progression"],
    )
    
    # ProtocolSession 객체 구성
    sessions = []
    for i, session_cards in enumerate(sessions_card_lists):
        week = (i // sessions_per_week) + 1
        day_of_week = (i % sessions_per_week) * (7 // sessions_per_week)
        
        # 회기 시간 = 카드들 cost_minutes 합
        total_duration = sum(c.cost_minutes for c in session_cards)
        
        # 이 회기 측정 자료
        if i == 0:
            measurement_focus = template["measurement_focus"] + ["initial_assessment"]
        elif (i + 1) % sessions_per_week == 0:  # 매주 마지막 회기
            measurement_focus = template["measurement_focus"]
        else:
            measurement_focus = []
        
        sessions.append(ProtocolSession(
            session_number=i + 1,
            week=week,
            day_of_week=day_of_week,
            cards=session_cards,
            expected_duration_min=total_duration,
            measurement_focus=measurement_focus,
        ))
    
    # 주간 체크인
    weekly_check_in = {}
    for w in range(1, weeks + 1):
        if w == 1 or w == weeks:
            # 첫 주, 마지막 주: 전체 측정
            weekly_check_in[f"week_{w}"] = template["measurement_focus"]
        else:
            # 중간 주: 핵심만
            weekly_check_in[f"week_{w}"] = template["measurement_focus"][:1]
    
    # 예상 임상 변화 (현재 상태 기반)
    expected_changes = _estimate_expected_changes(
        selected_axis, clinical_report, weeks
    )
    
    # Rationale
    rationale = _build_protocol_rationale(
        selected_axis, weeks, sessions_per_week, template, clinical_report
    )
    
    return TrainingProtocol(
        protocol_id=f"PROTO_{uuid.uuid4().hex[:8]}",
        patient_id=patient_id,
        selected_clinical_axis=selected_axis,
        target_duration_weeks=weeks,
        sessions=sessions,
        weekly_check_in=weekly_check_in,
        final_outcome_measures=template["measurement_focus"] + ["clinical_global_impression"],
        expected_clinical_changes=expected_changes,
        success_criteria=template["success_criteria"].copy(),
        generated_at=datetime.utcnow(),
        rationale=rationale,
    )


def _estimate_expected_changes(
    selected_axis: ClinicalAxis,
    report: Optional[ClinicalReport],
    weeks: int,
) -> dict[str, float]:
    """프로토콜 기간 동안 예상되는 임상 변화."""
    base_improvement = 0.15  # 4주 기본 개선
    
    # 주 수에 따라 조정
    weeks_factor = weeks / 4.0
    
    changes = {selected_axis: base_improvement * weeks_factor}
    
    if report:
        # 관계 행렬에서 부수 효과 추정
        for rel in report.relationships:
            if rel.axis_a == selected_axis or rel.axis_b == selected_axis:
                other = rel.axis_b if rel.axis_a == selected_axis else rel.axis_a
                # 양의 coupling이면 동반 개선, 음의 coupling이면 반대 영향
                collateral = base_improvement * rel.strength * 0.5 * weeks_factor
                changes[other] = round(collateral, 3)
    
    return changes


def _build_protocol_rationale(
    selected_axis: ClinicalAxis,
    weeks: int,
    sessions_per_week: int,
    template: dict,
    report: Optional[ClinicalReport],
) -> str:
    """프로토콜 생성 이유."""
    from cna_core.types import CLINICAL_AXIS_KOREAN
    
    axis_kr = CLINICAL_AXIS_KOREAN[selected_axis]
    progression_kr = {
        "complexity_ramp": "난이도 점진 증가",
        "consolidation": "반복 후 확장",
        "skill_stacking": "스킬 누적",
        "exposure_gradient": "점진 노출",
        "behavioral_activation": "행동 활성화",
    }.get(template["weekly_progression"], template["weekly_progression"])
    
    parts = [
        f"선택 영역: {axis_kr}",
        f"기간: {weeks}주 ({sessions_per_week}회/주)",
        f"진행 방식: {progression_kr}",
        f"주요 측정: {', '.join(template['measurement_focus'][:2])}",
    ]
    
    if report:
        primary = report.primary_recommendation
        if primary != selected_axis:
            parts.append(
                f"참고: 시스템 1순위는 {CLINICAL_AXIS_KOREAN[primary]}였으나 환자 선택 우선."
            )
    
    return " | ".join(parts)


# ============================================================
# 프로토콜 표 출력
# ============================================================

def format_protocol_as_table(protocol: TrainingProtocol) -> str:
    """프로토콜 → 한국어 표 출력."""
    from cna_core.types import CLINICAL_AXIS_KOREAN
    
    lines = []
    lines.append("=" * 72)
    lines.append(f"훈련 프로토콜 — {protocol.protocol_id}")
    lines.append(f"환자: {protocol.patient_id}")
    lines.append(f"영역: {CLINICAL_AXIS_KOREAN[protocol.selected_clinical_axis]}")
    lines.append(f"기간: {protocol.target_duration_weeks}주 / 총 {len(protocol.sessions)}회기")
    lines.append("=" * 72)
    lines.append("")
    
    lines.append("【 프로토콜 개요 】")
    lines.append("-" * 72)
    lines.append(f"  {protocol.rationale}")
    lines.append("")
    
    lines.append("【 예상 임상 변화 】")
    lines.append("-" * 72)
    for axis, change in protocol.expected_clinical_changes.items():
        axis_kr = CLINICAL_AXIS_KOREAN.get(axis, axis)
        sign = "+" if change >= 0 else ""
        lines.append(f"  {axis_kr:<14s}: {sign}{change:.3f}")
    lines.append("")
    
    lines.append("【 회기별 일정 】")
    lines.append("-" * 72)
    lines.append(f"  {'#':<4s} {'주':<4s} {'요일':<6s} {'시간':<8s} 카드")
    lines.append("  " + "-" * 68)
    
    days = ["월", "화", "수", "목", "금", "토", "일"]
    for session in protocol.sessions:
        day_str = days[min(session.day_of_week, 6)]
        cards_str = ", ".join(c.id for c in session.cards)
        lines.append(
            f"  {session.session_number:<4d} "
            f"W{session.week:<3d} "
            f"{day_str:<6s} "
            f"{session.expected_duration_min}분{'':<3s} "
            f"{cards_str}"
        )
    lines.append("")
    
    lines.append("【 주간 측정 자료 】")
    lines.append("-" * 72)
    for week_key, measures in protocol.weekly_check_in.items():
        lines.append(f"  {week_key}: {', '.join(measures)}")
    lines.append("")
    
    lines.append("【 성공 기준 】")
    lines.append("-" * 72)
    for criterion, target in protocol.success_criteria.items():
        lines.append(f"  {criterion}: ≥ {target}")
    lines.append("")
    
    lines.append("=" * 72)
    return "\n".join(lines)
