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

_COGNITIVE_AXIS_KO = {
    "sustained_attention": "지속 주의력",
    "working_memory": "작업기억",
    "emotional_regulation": "정서 조절",
    "time_awareness": "시간 감각",
    "self_awareness": "자기 인지",
}

_COGNITIVE_AXIS_EN = {
    "sustained_attention": "Sustained Attention",
    "working_memory": "Working Memory",
    "emotional_regulation": "Emotional Regulation",
    "time_awareness": "Time Awareness",
    "self_awareness": "Self-Awareness",
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

_CLINICAL_AXIS_KO = {
    "attention": "주의력",
    "learning": "학습 효율",
    "peak_performance": "수행 최적화",
    "anxiety": "불안 관리",
    "depression": "기분 안정",
}

_CLINICAL_AXIS_EN = {
    "attention": "Attention",
    "learning": "Learning Efficiency",
    "peak_performance": "Peak Performance",
    "anxiety": "Anxiety Management",
    "depression": "Mood Stability",
}

import contextvars as _ctxvars
from collections.abc import Mapping as _Mapping
_BNM_LANG = _ctxvars.ContextVar("bnm_lang", default="ko")
def set_language(language):
    _BNM_LANG.set("en" if str(language or "ko").lower().startswith("en") else "ko")
def get_language():
    return _BNM_LANG.get()
class _LangMap(_Mapping):
    __slots__ = ("_ko", "_en")
    def __init__(self, ko, en):
        self._ko, self._en = ko, en
    def _active(self):
        return self._en if _BNM_LANG.get() == "en" else self._ko
    def __getitem__(self, key):
        return self._active()[key]
    def __iter__(self):
        return iter(self._active())
    def __len__(self):
        return len(self._active())
COGNITIVE_AXIS_KOREAN = _LangMap(_COGNITIVE_AXIS_KO, _COGNITIVE_AXIS_EN)
CLINICAL_AXIS_KOREAN  = _LangMap(_CLINICAL_AXIS_KO, _CLINICAL_AXIS_EN)

_PHRASES_KO = {
  "co_improve":"{x} 동반 개선","co_stabilize":"{x} 부수 안정",
  "alt_preview":"{axis} 선택 시: 현재 {interp}, 부수 효과 — {coll}",
  "rat_top":"1순위 추천: {x}","rat_current":"현재 상태: {x}",
  "rat_cog_impact":"주요 인지 영향: {x} (기여도 {y})","rat_ripple":"파급 효과: {x} 개선 → ",
  "rat_influence":"{x} 영향 (강도 {y})","patient_choice":"환자 선택: {x}. 환자 자율성 우선.",
  "sim_set":"{axis} L{a} → L{b} (Δ{d}) 박으면, ","sim_biggest":"가장 큰 효과 자료: {x} {v}. ",
  "sim_total":"총 임상 개선: {t}.","rank_target_top":"{x} 개선이 1순위 자료. ",
  "rank_overall":"전체 임상 5축 종합 개선 자료. ","rank_effective":"가장 효과적: {a} +{b} Level → ",
  "assume_mapping":"Linear evidence → level change 매핑 (d={d})","assume_avg":"평균 카드 반복 {n}회",
  "assume_time":"시간이: {weeks}주 (4주 기준 자료 비례)",
  "assume_carryover":"Carry-over 효과 ❌ (각 카드 독립 가정)","assume_respond":"환자 개인 반응성 ❌ (평균 effect 적용)",
  "role_primary":"1차","role_coexist":"공존","role_possible":"가능",
  "src_head":"{name} ({role}, 사후확률 {p}) → ","src_tail":"{clin} 약화의 {c} 기여",
  "intpri_primary":"Primary 진단 자료 1순위 — {x}","intpri_coexist":"공존 자료 {i}순위 — primary 치료 후 잔존 증상 평가",
  "tx_low_conf":"진단 신뢰도 부족. 추가 평가 필요.","tx_comorbid":"{name} 표준. 공존률 {r} 임상 패턴.",
  "tx_primary":"Primary: {name}. {priority}.","rev_low_cert":"진단 확실성 낮음 — 가장 강한 가설 < 40%",
  "rev_no_temporal":"시간 정보 부족 — 발병/경과 미수집","rev_no_symptoms":"증상 호소 정보 없음 — 진단 정보 불완전",
  "rev_hard_diff":"감별 어려움 — {a} vs {b}","rev_adhd_age":"ADHD 의심 — 발병 나이 (<12) 확인 필요",
  "lvl_excellent":"매우 우수","lvl_strong":"우수","lvl_moderate":"보통","lvl_attention":"주의 필요","lvl_clinical":"임상 개입 우선",
  "prog_difficulty":"난이도 점진 증가","prog_expand":"반복 후 확장","prog_skill":"스킬 누적",
  "prog_exposure":"점진 노출","prog_activation":"행동 활성화",
  "proto_area":"선택 영역: {axis}","proto_duration":"기간: {weeks}주 ({per}회/주)",
  "proto_progression":"진행 방식: {prog}","proto_measure":"주요 측정: {x}",
  "proto_note":"참고: 시스템 1순위는 {x}였으나 환자 선택 우선.",
}
_PHRASES_EN = {
  "co_improve":"co-improvement in {x}","co_stabilize":"secondary stabilization of {x}",
  "alt_preview":"If {axis} is selected: currently {interp}; secondary effects — {coll}",
  "rat_top":"Top recommendation: {x}","rat_current":"Current status: {x}",
  "rat_cog_impact":"Primary cognitive impact: {x} (contribution {y})","rat_ripple":"Ripple effect: improving {x} → ",
  "rat_influence":"{x} effect (strength {y})","patient_choice":"Patient choice: {x}. Patient autonomy prioritized.",
  "sim_set":"Setting {axis} L{a} → L{b} (Δ{d}), ","sim_biggest":"Largest effect: {x} {v}. ",
  "sim_total":"Total clinical improvement: {t}.","rank_target_top":"Improving {x} is the top priority. ",
  "rank_overall":"Comprehensive improvement across all 5 clinical axes. ","rank_effective":"Most effective: {a} +{b} levels → ",
  "assume_mapping":"Linear evidence → level-change mapping (d={d})","assume_avg":"Average card repetition: {n}x",
  "assume_time":"Timeframe: {weeks} weeks (scaled to a 4-week baseline)",
  "assume_carryover":"Carry-over effect ❌ (each card assumed independent)","assume_respond":"Individual patient responsiveness ❌ (average effect applied)",
  "role_primary":"primary","role_coexist":"comorbid","role_possible":"possible",
  "src_head":"{name} ({role}, posterior {p}) → ","src_tail":"{c} contribution to {clin} deficit",
  "intpri_primary":"Primary diagnosis, top priority — {x}","intpri_coexist":"Comorbid, priority {i} — assess residual symptoms after primary treatment",
  "tx_low_conf":"Insufficient diagnostic confidence. Further assessment needed.","tx_comorbid":"{name} standard. Comorbidity rate {r} clinical pattern.",
  "tx_primary":"Primary: {name}. {priority}.","rev_low_cert":"Low diagnostic certainty — strongest hypothesis < 40%",
  "rev_no_temporal":"Insufficient temporal data — onset/course not collected","rev_no_symptoms":"No symptom report — diagnostic information incomplete",
  "rev_hard_diff":"Differentiation difficult — {a} vs {b}","rev_adhd_age":"ADHD suspected — confirm age of onset (<12)",
  "lvl_excellent":"Excellent","lvl_strong":"Strong","lvl_moderate":"Moderate","lvl_attention":"Needs attention","lvl_clinical":"Clinical intervention priority",
  "prog_difficulty":"Gradual difficulty increase","prog_expand":"Repeat then expand","prog_skill":"Skill accumulation",
  "prog_exposure":"Gradual exposure","prog_activation":"Behavioral activation",
  "proto_area":"Selected area: {axis}","proto_duration":"Duration: {weeks} weeks ({per}/week)",
  "proto_progression":"Progression: {prog}","proto_measure":"Primary measure: {x}",
  "proto_note":"Note: system top priority was {x}, but patient choice takes precedence.",
}
def T(key, **kw):
    m = _PHRASES_EN if _BNM_LANG.get()=="en" else _PHRASES_KO
    s = m.get(key);  s = s if s is not None else _PHRASES_KO.get(key, key)
    try: return s.format(**kw) if kw else s
    except Exception: return s
def nm(ko, en):
    return en if (_BNM_LANG.get()=="en" and en) else ko


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
