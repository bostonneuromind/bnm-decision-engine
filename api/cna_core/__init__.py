"""
CNA v7 — Boston Neuromind LLC

Active Inference framework + DSM-5-TR Differential Diagnosis 통합.

Main components:
  - CognitiveClinicalMapper: Fischer 5축 → 임상 5축 매핑
  - FreeEnergyScorer: 6-Component Free Energy 의사결정
  - ClinicalReport: 5축 예측표 + 관계
  - TrainingProtocol: 자동 프로토콜 생성
  - VariationalBeliefUpdate: Loop 7 학습
  - DifferentialDiagnosisEngine: DSM-5-TR + 시간이 + Bayesian (NEW)
  - ComorbidityDecomposer: 임상 점수 source별 분해 (NEW)
  - CognitiveSimulator: Counterfactual 시뮬레이션 (NEW)
  - AdaptiveRerouter: outcome 기반 재진단 (NEW)
  - CNAOrchestrator: 전체 통합

Boston Neuromind LLC · 2026
"""

from cna_core.types import (
    CognitiveAxis, ClinicalAxis,
    COGNITIVE_AXES, CLINICAL_AXES,
    COGNITIVE_AXIS_KOREAN, CLINICAL_AXIS_KOREAN,
    V1State, V2Desire, V3Skill, V4Trajectory,
    Card, ScoredCard, ComponentBreakdown,
    SafetyFlag,
    DecisionEpisode, SystemState,
    ClinicalAxisReport, AxisRelationship, AlternativePath, ClinicalReport,
    ProtocolSession, TrainingProtocol,
    FischerLevel,
)

from cna_core.cognitive_clinical_mapper import CognitiveClinicalMapper
from cna_core.free_energy_scorer import (
    FreeEnergyScorer,
    compute_phase_weights,
    accuracy_symptom, accuracy_biomarker, complexity_penalty,
    preference_match, epistemic_value, pragmatic_value,
)
from cna_core.clinical_report import (
    generate_clinical_report,
    format_report_as_table,
)
from cna_core.protocol_generator import (
    generate_training_protocol,
    format_protocol_as_table,
)
from cna_core.crisis_detection import (
    detect_crisis,
    has_imminent_flag,
    get_highest_severity,
    format_safety_alert,
    CRISIS_RULES,
)
from cna_core.variational_update import (
    variational_belief_update,
    meta_learning_review,
)
from cna_core.card_deck import get_default_card_deck
from cna_core.biomarker_normalization import (
    normalize_biomarker,
    normalize_v1_biomarkers,
    normalize_card_profile,
    BIOMARKER_DEFINITIONS,
)

# NEW: Round 7-10 모듈
from cna_core.differential_diagnosis import (
    DifferentialDiagnosisEngine,
    DifferentialDiagnosisResult,
    DiagnosticHypothesis,
    TemporalHistory,
    TemporalOnset,
    TemporalCourse,
)
from cna_core.comorbidity_decomposition import (
    ComorbidityDecomposer,
    ComorbidityProfile,
    DecomposedClinicalScore,
    SourceContribution,
    format_comorbidity_profile_table,
)
from cna_core.cognitive_simulator import (
    CognitiveSimulator,
    SingleAxisCounterfactual,
    CardSequenceSimulation,
    InterventionRanking,
)
from cna_core.adaptive_rerouting import (
    AdaptiveRerouter,
    TreatmentResponse,
    ReroutingDecision,
    format_rerouting_decision_table,
)

from cna_core.orchestrator import CNAOrchestrator


__version__ = "7.0.0"
__author__ = "Alex Kwon, Boston Neuromind LLC"
