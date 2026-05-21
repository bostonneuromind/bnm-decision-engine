"""
CNA v6 — Shared Data Types

모든 모듈이 공유하는 자료 구조 정의.
Layer A (Fischer 인지) + Layer B (임상 결과) + Card + Episode.

Boston Neuromind LLC · 2026
"""

from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================
# Layer A: Cognitive Axes (Fischer 5축, L7-L13 측정)
# ============================================================

CognitiveAxis = Literal[
    "sustained_attention",   # 지속 주의력 (CPT)
    "working_memory",        # 작업기억 (N-back)
    "emotional_regulation",  # 정서조절 (HRV + VSR)
    "time_awareness",        # 시간감각 (시간추정)
    "self_awareness",        # 자기인지 (OMR)
]

COGNITIVE_AXES: list[CognitiveAxis] = [
    "sustained_attention",
    "working_memory",
    "emotional_regulation",
    "time_awareness",
    "self_awareness",
]

COGNITIVE_AXIS_KOREAN = {
    "sustained_attention": "지속 주의력",
    "working_memory": "작업기억",
    "emotional_regulation": "정서 조절",
    "time_awareness": "시간 감각",
    "self_awareness": "자기 인지",
}


# ============================================================
# Layer B: Clinical Axes (환자 선택 가능한 5개 영역)
# ============================================================

ClinicalAxis = Literal[
    "attention",          # 주의력 (ADHD 영역)
    "learning",           # 학습 효율
    "peak_performance",   # 수행 최적화
    "anxiety",            # 불안 관리
    "depression",         # 기분 안정
]

CLINICAL_AXES: list[ClinicalAxis] = [
    "attention",
    "learning",
    "peak_performance",
    "anxiety",
    "depression",
]

CLINICAL_AXIS_KOREAN = {
    "attention": "주의력",
    "learning": "학습 효율",
    "peak_performance": "수행 최적화",
    "anxiety": "불안 관리",
    "depression": "기분 안정",
}


# ============================================================
# Fischer Level (L7-L13, 성인 일반)
# ============================================================

class FischerLevel(BaseModel):
    """Fischer Dynamic Skill Theory Level."""
    level: float = Field(ge=7.0, le=13.0, description="L7.0 - L13.0")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    last_measured: Optional[datetime] = None


# ============================================================
# 4-Vector 입력
# ============================================================

class V1State(BaseModel):
    """
    V1: 현재 측정 상태 (Snapshot).
    Entry Protocol 5 측정 결과 + 증상 진술.
    """
    symptom_vector: dict[str, float] = Field(
        default_factory=dict,
        description="증상 점수, 예: {'inattention': 0.7, 'anxiety_somatic': 0.4}",
    )
    biomarkers: dict[str, float] = Field(
        default_factory=dict,
        description="객관 측정값, 예: {'cpt_omissions_zscore': -1.2, 'hrv_rmssd': 28}",
    )
    biomarker_variance: dict[str, float] = Field(
        default_factory=dict,
        description="측정 신뢰도 분산. 작을수록 신뢰",
    )
    subjective_state: dict[str, float] = Field(
        default_factory=dict,
        description="환자 주관 보고, 예: {'mood': 0.4, 'energy': 0.3}",
    )


class V2Desire(BaseModel):
    """
    V2: 환자 목표 (Preferences).
    환자가 무엇을 원하는지.
    """
    primary_clinical_axis: ClinicalAxis = Field(
        description="환자가 선택한 임상 영역"
    )
    preferred_outcomes: dict[str, float] = Field(
        default_factory=dict,
        description="구체적 원하는 결과, 예: {'focus_improvement': 0.7}",
    )
    motivation: float = Field(default=0.5, ge=0.0, le=1.0)
    barriers: list[str] = Field(default_factory=list, description="환자가 인식한 장애물")


class V3Skill(BaseModel):
    """
    V3: Fischer 5축 능력 (Hidden States).
    Loop 2 Locate 결과.
    """
    axis_levels: dict[str, float] = Field(
        description="각 인지축의 Fischer Level"
    )
    confidence: dict[str, float] = Field(
        default_factory=dict,
        description="각 축 측정 신뢰도"
    )


class V4Trajectory(BaseModel):
    """
    V4: 시간 흐름 (Trajectory).
    과거 회기 누적 자료.
    """
    n_sessions: int = 0
    past_card_outcomes: list[dict] = Field(
        default_factory=list,
        description="이전 카드별 outcome 기록"
    )
    axis_change_rates: dict[str, float] = Field(
        default_factory=dict,
        description="각 인지축의 변화 속도 (level/주)"
    )
    clinical_score_history: list[dict] = Field(
        default_factory=list,
        description="회기별 5축 임상 점수"
    )


# ============================================================
# Card (치료/훈련 카드)
# ============================================================

class Card(BaseModel):
    """
    치료/훈련 카드.
    Loop 3가 선택하고 Loop 4가 환자에게 전달.
    """
    id: str
    deck_id: str = "default_v1"
    
    # 타겟 자료
    target_symptoms: dict[str, float] = Field(default_factory=dict)
    expected_biomarker_profile: dict[str, float] = Field(default_factory=dict)
    target_fischer_levels: dict[str, float] = Field(default_factory=dict)
    target_clinical_axes: list[ClinicalAxis] = Field(default_factory=list)
    
    # 근거 자료
    evidence_d: float = Field(default=0.3, description="Cochrane effect size")
    citations: list[str] = Field(default_factory=list)
    
    # 운영 가이드
    state_requirements: dict[str, float] = Field(default_factory=dict)
    safe_for_crisis: bool = False
    cost_minutes: int = 15
    expected_outcome: float = Field(default=0.5, ge=-1.0, le=1.0)
    information_gain_class: Literal["high", "standard", "low"] = "standard"
    
    # 표시 자료
    text_ko: str = ""
    text_en: str = ""
    instruction_steps: list[str] = Field(default_factory=list)
    
    # 메타데이터
    domain: str = "learning_pp"
    areas: list[str] = Field(default_factory=list)
    validated: bool = False


class ComponentBreakdown(BaseModel):
    """6-component 점수 분해 자료. 로깅 + 학습 자료."""
    accuracy_symptom: float
    accuracy_biomarker: float
    complexity_penalty: float
    preference: float
    epistemic_value: float
    pragmatic_value: float
    weights_used: dict[str, float]
    final_score: float


class ScoredCard(BaseModel):
    """점수가 매겨진 카드."""
    card: Card
    score: float
    breakdown: ComponentBreakdown
    explanation: str


# ============================================================
# Safety
# ============================================================

class SafetyFlag(BaseModel):
    """Crisis detection 플래그."""
    flag_type: str
    severity: Literal["moderate", "high", "imminent"]
    triggered_by: str
    timestamp: datetime
    immediate_action: str
    resources: dict[str, list[str]] = Field(default_factory=dict)


# ============================================================
# Decision Episode (모든 진화 자리가 공유)
# ============================================================

class DecisionEpisode(BaseModel):
    """
    한 의사결정 사이클의 통합 자료.
    
    모든 진화 메커니즘이 이 객체를 봅니다.
    학습 신호가 따로 놀지 않도록 단일 자료 구조.
    """
    # 식별
    episode_id: str
    timestamp: datetime
    patient_id: str
    
    # 입력 (Loop 1-2)
    v1_state: V1State
    v2_desire: V2Desire
    v3_skill: V3Skill
    v4_trajectory: V4Trajectory
    
    # 시스템 추천 (Loop 3)
    candidate_cards: list[ScoredCard]
    system_top1: Card
    weights_used: dict[str, float]
    safety_anchors_triggered: list[str] = Field(default_factory=list)
    
    # 임상가 결정 (Loop 4)
    clinician_choice: Card
    clinician_rationale: Optional[str] = None
    agreement: bool
    
    # 환자 응답 (Loop 4 OMR + Loop 5)
    omr_response_text: Optional[str] = None
    in_session_change: dict = Field(default_factory=dict)
    
    # Outcome (Loop 7, 4주 후)
    outcome_score: Optional[float] = Field(default=None, ge=-1.0, le=1.0)
    outcome_clinical_scores: Optional[dict[str, float]] = None
    outcome_variance: float = Field(default=0.5, ge=0.0)
    outcome_timestamp: Optional[datetime] = None


# ============================================================
# System State (학습 진화 누적)
# ============================================================

class SystemState(BaseModel):
    """
    시스템 학습 상태 누적.
    매 episode 후 update 됩니다.
    """
    # 학습 자료
    weights: dict[str, float]
    weight_snapshots: list[dict] = Field(default_factory=list)
    
    # Anchor 자료
    fixed_components: list[str] = Field(default_factory=list)
    crisis_rules_version: str = "v1.0"
    
    # 학습률
    learning_rate: dict[str, float] = Field(default_factory=lambda: {
        "weights": 0.03,
        "cognitive_clinical_mapping": 0.02,
        "patterns": 0.01,
        "crisis": 0.0,
    })
    
    # 추적 자료
    episode_count: int = 0
    recent_prediction_errors: list[float] = Field(default_factory=list)
    weight_change_history: list[dict] = Field(default_factory=list)
    
    # 메타-학습
    last_meta_review: Optional[datetime] = None
    global_learning_pause: bool = False
    alerts: list[str] = Field(default_factory=list)


# ============================================================
# Clinical Report (환자 선택 단계)
# ============================================================

class ClinicalAxisReport(BaseModel):
    """한 임상축의 상태 보고."""
    axis: ClinicalAxis
    axis_korean: str
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    interpretation: str
    severity_tier: str
    contributing_cognitive_axes: dict[str, float]
    recommendation_priority: int = Field(ge=1, le=5)


class AxisRelationship(BaseModel):
    """두 임상축 간 관계."""
    axis_a: ClinicalAxis
    axis_b: ClinicalAxis
    strength: float = Field(ge=-1.0, le=1.0)
    type: str  # "positive_coupling" | "inverse_coupling"
    description: str
    leverage_score: float


class AlternativePath(BaseModel):
    """환자가 다른 축 선택 시 자료."""
    axis: ClinicalAxis
    axis_korean: str
    expected_collateral_benefit: float
    preview_text: str


class ClinicalReport(BaseModel):
    """5축 통합 임상 자료 보고서."""
    patient_id: str
    timestamp: datetime
    cognitive_levels: dict[str, float]
    axes: dict[str, ClinicalAxisReport]
    relationships: list[AxisRelationship]
    primary_recommendation: ClinicalAxis
    rationale: str
    alternative_paths: list[AlternativePath]


# ============================================================
# Training Protocol (환자 선택 후 자동 생성)
# ============================================================

class ProtocolSession(BaseModel):
    """프로토콜의 한 세션."""
    session_number: int
    week: int
    day_of_week: int  # 0=월, 6=일
    cards: list[Card]
    expected_duration_min: int
    measurement_focus: list[str]  # 이 회기에 측정할 자료


class TrainingProtocol(BaseModel):
    """
    환자 선택 → 자동 생성된 훈련 프로토콜.
    Loop 4 Deliver가 사용.
    """
    protocol_id: str
    patient_id: str
    selected_clinical_axis: ClinicalAxis
    target_duration_weeks: int = 4
    
    # 회기 자료
    sessions: list[ProtocolSession]
    
    # 측정 자료
    weekly_check_in: dict[str, list[str]]  # week → measurements
    final_outcome_measures: list[str]
    
    # 진화 자료
    expected_clinical_changes: dict[str, float]
    success_criteria: dict[str, float]
    
    # 메타데이터
    generated_at: datetime
    generator_version: str = "v6.0"
    rationale: str
