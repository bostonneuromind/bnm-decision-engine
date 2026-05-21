"""
CNA v7 — Main Orchestrator (Round 7-10 통합)

새 추가 작업:
  - Differential Diagnosis Engine (DDE)
  - Comorbidity Decomposition
  - Cognitive Simulator (Counterfactual)
  - Adaptive Re-routing (outcome 기반 재진단)

Loop 1 Sense → Loop 2 Locate → Loop 2.5 Diagnosis (NEW) → Loop 3 Decide
→ Loop 4 Deliver → Loop 7 Feedback (with Re-routing)

Boston Neuromind LLC · 2026
"""

import uuid
from datetime import datetime
from typing import Optional

from cna_core.types import (
    V1State, V2Desire, V3Skill, V4Trajectory,
    Card, ScoredCard, DecisionEpisode, SystemState,
    ClinicalReport, TrainingProtocol, ClinicalAxis, SafetyFlag,
)
from cna_core.cognitive_clinical_mapper import CognitiveClinicalMapper
from cna_core.free_energy_scorer import FreeEnergyScorer
from cna_core.clinical_report import generate_clinical_report
from cna_core.protocol_generator import generate_training_protocol
from cna_core.crisis_detection import detect_crisis, has_imminent_flag
from cna_core.variational_update import variational_belief_update
from cna_core.card_deck import get_default_card_deck
from cna_core.differential_diagnosis import (
    DifferentialDiagnosisEngine, DifferentialDiagnosisResult, TemporalHistory,
)
from cna_core.comorbidity_decomposition import (
    ComorbidityDecomposer, ComorbidityProfile,
)
from cna_core.cognitive_simulator import (
    CognitiveSimulator, InterventionRanking, CardSequenceSimulation,
)
from cna_core.adaptive_rerouting import (
    AdaptiveRerouter, TreatmentResponse, ReroutingDecision,
)


class CNAOrchestrator:
    """
    전체 시스템 통합 — v7 강화 버전.
    
    Loop 1-2: Sense + Locate (인지/임상 5축)
    Loop 2.5: Diagnosis (DDE + Decomposition + Simulator)  [NEW]
    Loop 3: Decide (Free Energy)
    Loop 4: Deliver (Protocol)
    Loop 7: Feedback (Variational + Re-routing)  [NEW]
    """
    
    def __init__(self, system_state: Optional[SystemState] = None):
        self.mapper = CognitiveClinicalMapper()
        self.scorer = FreeEnergyScorer()
        self.card_deck = get_default_card_deck()
        
        # NEW: Round 7-10 모듈
        self.dde = DifferentialDiagnosisEngine()
        self.decomposer = ComorbidityDecomposer(self.mapper, self.dde)
        self.simulator = CognitiveSimulator(self.mapper)
        self.rerouter = AdaptiveRerouter(self.dde)
        
        # System state 초기화
        if system_state:
            self.state = system_state
        else:
            self.state = SystemState(
                weights={
                    "accuracy_symptom": 0.20,
                    "accuracy_biomarker": 0.15,
                    "complexity_penalty": 0.15,
                    "preference": 0.15,
                    "epistemic": 0.25,
                    "pragmatic": 0.10,
                },
                fixed_components=["complexity_penalty", "epistemic"],
            )
        
        # 환자별 진단 자료 히스토리 (re-routing용)
        self.patient_diagnosis_history: dict[str, list[DifferentialDiagnosisResult]] = {}
    
    # ========================================
    # Loop 1-2: Sense + Locate
    # ========================================
    
    def assess_patient(
        self,
        patient_id: str,
        cognitive_levels: dict[str, float],
        v1_state: V1State,
        v2_desire: V2Desire,
        v4_trajectory: Optional[V4Trajectory] = None,
        temporal_history: Optional[TemporalHistory] = None,
    ) -> dict:
        """
        Loop 1-2 + Loop 2.5: Sense + Locate + Diagnosis.
        
        Returns:
            v3_skill, v4_trajectory, clinical_report, safety_flags,
            differential_diagnosis (NEW),
            comorbidity_profile (NEW),
            intervention_ranking (NEW)
        """
        # V3 Skill
        v3 = V3Skill(
            axis_levels=cognitive_levels,
            confidence={k: 0.7 for k in cognitive_levels},
        )
        
        # V4 기본값
        v4 = v4_trajectory or V4Trajectory(n_sessions=0)
        
        # Crisis 검사
        recent_utterances = []
        if v2_desire.barriers:
            recent_utterances.extend(v2_desire.barriers)
        safety_flags = detect_crisis(recent_utterances, v1_state)
        
        # 임상 리포트 (5축 예측 + 관계)
        clinical_report = generate_clinical_report(
            patient_id=patient_id,
            cognitive_levels=cognitive_levels,
            mapper=self.mapper,
            patient_choice=v2_desire.primary_clinical_axis,
        )
        
        # ============================
        # Loop 2.5 NEW: Diagnosis layer
        # ============================
        
        # Clinical scores dict (DDE input)
        clinical_scores_dict = {
            axis: report.score
            for axis, report in clinical_report.axes.items()
        }
        
        # 1. Differential Diagnosis (REVISED: symptom + cognitive + biomarker + temporal)
        dde_result = self.dde.diagnose(
            patient_id=patient_id,
            cognitive_levels=cognitive_levels,
            clinical_scores=clinical_scores_dict,  # 호환성용, 사용 X
            symptom_vector=v1_state.symptom_vector,
            biomarkers=v1_state.biomarkers,
            temporal_history=temporal_history,
        )
        
        # 2. Comorbidity Decomposition
        clinical_scores_for_decomp = {
            axis: {"score": report.score}
            for axis, report in clinical_report.axes.items()
        }
        comorbidity_profile = self.decomposer.decompose(
            patient_id=patient_id,
            cognitive_levels=cognitive_levels,
            clinical_scores=clinical_scores_for_decomp,
            dde_result=dde_result,
        )
        
        # 3. Intervention Ranking (어느 인지축 훈련하는 게 가장 효과적?)
        intervention_ranking = self.simulator.rank_intervention_candidates(
            baseline_cognitive=cognitive_levels,
            target_clinical_axis=v2_desire.primary_clinical_axis,
        )
        
        # 4. Target Level 자동 추천
        target_levels = self.simulator.recommend_target_levels(
            baseline_cognitive=cognitive_levels,
            target_clinical_axis=v2_desire.primary_clinical_axis,
            target_clinical_score=0.65,
        )
        
        # 진단 자료 히스토리 저장
        if patient_id not in self.patient_diagnosis_history:
            self.patient_diagnosis_history[patient_id] = []
        self.patient_diagnosis_history[patient_id].append(dde_result)
        
        return {
            "v3_skill": v3,
            "v4_trajectory": v4,
            "clinical_report": clinical_report,
            "safety_flags": safety_flags,
            "imminent_safety": has_imminent_flag(safety_flags),
            
            # NEW
            "differential_diagnosis": dde_result,
            "comorbidity_profile": comorbidity_profile,
            "intervention_ranking": intervention_ranking,
            "target_levels": target_levels,
        }
    
    # ========================================
    # Loop 3: Decide
    # ========================================
    
    def decide_treatment(
        self,
        patient_id: str,
        v1: V1State,
        v2: V2Desire,
        v3: V3Skill,
        v4: V4Trajectory,
        safety_flags: list[SafetyFlag] = None,
        clinical_report: Optional[ClinicalReport] = None,
        dde_result: Optional[DifferentialDiagnosisResult] = None,
    ) -> dict:
        """
        Loop 3 Decide. DDE 결과로 카드 자료 filtering 강화.
        """
        safety_flags = safety_flags or []
        cards = self.card_deck
        
        # Safety filtering
        if has_imminent_flag(safety_flags):
            cards = [c for c in cards if c.safe_for_crisis]
            safety_filtered = True
        elif any(f.severity == "high" for f in safety_flags):
            cards = [c for c in cards if c.safe_for_crisis or c.cost_minutes <= 15]
            safety_filtered = True
        else:
            safety_filtered = False
        
        # NEW: DDE 기반 카드 자료 우선 박기
        # Primary 진단이 있으면 그 진단 자료가 영향 미치는 인지축 훈련하는 카드 우선
        diagnosis_aligned_cards = []
        if dde_result and dde_result.primary_diagnosis:
            pattern = self.dde.primary_patterns.get(dde_result.primary_diagnosis)
            if pattern:
                target_cog_axes = [
                    axis for axis, weakness in pattern["cognitive_signature"].items()
                    if weakness > 0.50
                ]
                # 이 인지축 훈련하는 카드 자료 우선
                for c in cards:
                    if any(axis in c.target_fischer_levels for axis in target_cog_axes):
                        diagnosis_aligned_cards.append(c)
        
        # Diagnosis-aligned 카드가 충분하면 우선 자료
        if len(diagnosis_aligned_cards) >= 5:
            cards = diagnosis_aligned_cards
        
        if not cards:
            raise ValueError("No cards available after safety filtering")
        
        # 임상 5축 점수 (emergency phase 자동 catch)
        clinical_scores = None
        emergency_active = False
        if clinical_report:
            clinical_scores = {
                axis: report.score
                for axis, report in clinical_report.axes.items()
            }
            for axis in ["anxiety", "depression"]:
                if clinical_scores.get(axis, 1.0) < 0.30:
                    emergency_active = True
                    break
        
        # Free Energy scoring
        scored = self.scorer.score(
            filtered_cards=cards,
            v1=v1, v2=v2, v3=v3, v4=v4,
            top_n=3,
            clinical_scores=clinical_scores,
        )
        
        return {
            "candidate_cards": scored,
            "top_recommendation": scored[0] if scored else None,
            "safety_filtered": safety_filtered,
            "emergency_phase_active": emergency_active,
            "n_cards_considered": len(cards),
            "diagnosis_aligned": len(diagnosis_aligned_cards) >= 5,
        }
    
    # ========================================
    # Loop 4: Protocol 생성
    # ========================================
    
    def generate_protocol(
        self,
        patient_id: str,
        selected_axis: ClinicalAxis,
        v1: V1State,
        v2: V2Desire,
        v3: V3Skill,
        v4: V4Trajectory,
        clinical_report: Optional[ClinicalReport] = None,
        custom_weeks: Optional[int] = None,
    ) -> TrainingProtocol:
        """환자 영역 선택 → 자동 프로토콜 생성."""
        return generate_training_protocol(
            patient_id=patient_id,
            selected_axis=selected_axis,
            v1=v1, v2=v2, v3=v3, v4=v4,
            clinical_report=clinical_report,
            custom_weeks=custom_weeks,
            available_cards=self.card_deck,
        )
    
    # ========================================
    # NEW: Counterfactual Simulation
    # ========================================
    
    def simulate_protocol_effect(
        self,
        baseline_cognitive: dict[str, float],
        protocol: TrainingProtocol,
    ) -> CardSequenceSimulation:
        """프로토콜 적용 후 예상 자료 시뮬레이션."""
        # 모든 카드 자료 추출
        all_cards = []
        for session in protocol.sessions:
            all_cards.extend(session.cards)
        
        return self.simulator.simulate_card_sequence(
            baseline_cognitive=baseline_cognitive,
            cards=all_cards,
            weeks=protocol.target_duration_weeks,
        )
    
    # ========================================
    # Loop 4-7: Episode 기록 + 학습
    # ========================================
    
    def commit_episode(
        self,
        patient_id: str,
        v1: V1State, v2: V2Desire, v3: V3Skill, v4: V4Trajectory,
        candidate_cards: list[ScoredCard],
        clinician_choice: Card,
        clinician_rationale: Optional[str] = None,
        safety_flags: Optional[list[SafetyFlag]] = None,
    ) -> DecisionEpisode:
        """Loop 4 Deliver 후 episode 기록."""
        top_card = candidate_cards[0].card if candidate_cards else clinician_choice
        agreement = (top_card.id == clinician_choice.id)
        
        episode = DecisionEpisode(
            episode_id=f"EP_{uuid.uuid4().hex[:8]}",
            timestamp=datetime.utcnow(),
            patient_id=patient_id,
            v1_state=v1, v2_desire=v2, v3_skill=v3, v4_trajectory=v4,
            candidate_cards=candidate_cards,
            system_top1=top_card,
            weights_used=(
                candidate_cards[0].breakdown.weights_used.copy()
                if candidate_cards else {}
            ),
            safety_anchors_triggered=[f.flag_type for f in (safety_flags or [])],
            clinician_choice=clinician_choice,
            clinician_rationale=clinician_rationale,
            agreement=agreement,
        )
        return episode
    
    def record_outcome_with_rerouting(
        self,
        episode: DecisionEpisode,
        outcome_score: float,
        cognitive_after: dict[str, float],
        clinical_after: dict[str, float],
        primary_intervention_axis: ClinicalAxis,
        intervention_card_ids: list[str],
        outcome_variance: float = 0.3,
        temporal_history: Optional[TemporalHistory] = None,
    ) -> dict:
        """
        Loop 7 outcome + adaptive re-routing.
        
        Returns:
            - episode (updated)
            - rerouting_decision (NEW)
            - new_diagnosis (if rerouted)
        """
        # Outcome 자료 기록
        episode.outcome_score = outcome_score
        episode.outcome_clinical_scores = clinical_after
        episode.outcome_variance = outcome_variance
        episode.outcome_timestamp = datetime.utcnow()
        
        # Variational update (기존)
        self.state = variational_belief_update(
            episode=episode,
            state=self.state,
            mapper=self.mapper,
        )
        
        # NEW: Adaptive Re-routing
        rerouting_decision = None
        new_diagnosis = None
        
        patient_id = episode.patient_id
        if patient_id in self.patient_diagnosis_history:
            history = self.patient_diagnosis_history[patient_id]
            if history:
                # 이전 진단
                previous_diagnosis = history[-1]
                
                # 변화량 계산
                cognitive_before = episode.v3_skill.axis_levels
                clinical_before_dict = {}
                # episode.v1_state에서 직접 자료는 없으므로 baseline 추정
                # (실 자료는 이전 record_outcome 시 저장된 자료를 사용)
                
                # 임시: 이전 진단의 clinical_signature 자료를 baseline으로 자료
                # (실 자료에서는 별도 저장 필요)
                cognitive_changes = {
                    axis: cognitive_after.get(axis, before) - before
                    for axis, before in cognitive_before.items()
                }
                
                # Treatment Response 구성
                tr = TreatmentResponse(
                    episode_id=episode.episode_id,
                    primary_intervention_axis=primary_intervention_axis,
                    intervention_cards=intervention_card_ids,
                    cognitive_before=cognitive_before,
                    cognitive_after=cognitive_after,
                    clinical_before={a: 0.5 for a in clinical_after},  # placeholder
                    clinical_after=clinical_after,
                    cognitive_changes=cognitive_changes,
                    clinical_changes={
                        a: clinical_after.get(a, 0.5) - 0.5
                        for a in clinical_after
                    },
                )
                
                # Re-routing 실행
                rerouting_decision = self.rerouter.reroute(
                    patient_id=patient_id,
                    previous_diagnosis=previous_diagnosis,
                    treatment_response=tr,
                    temporal_history=temporal_history,
                )
                
                # 진단이 변경되었으면 새 진단 저장
                if rerouting_decision.diagnosis_changed:
                    # 새 진단으로 DDE 재실행
                    new_diagnosis = self.dde.diagnose(
                        patient_id=patient_id,
                        cognitive_levels=cognitive_after,
                        clinical_scores=clinical_after,
                        symptom_vector=episode.v1_state.symptom_vector,
                        biomarkers=episode.v1_state.biomarkers,
                        temporal_history=temporal_history,
                    )
                    self.patient_diagnosis_history[patient_id].append(new_diagnosis)
        
        return {
            "episode": episode,
            "rerouting_decision": rerouting_decision,
            "new_diagnosis": new_diagnosis,
            "system_state": {
                "episode_count": self.state.episode_count,
                "alerts": self.state.alerts[-3:],
            },
        }
    
    # ========================================
    # 전체 사이클 (편의 함수)
    # ========================================
    
    def run_full_assessment_cycle(
        self,
        patient_id: str,
        cognitive_levels: dict[str, float],
        v1_state: V1State,
        v2_desire: V2Desire,
        v4_trajectory: Optional[V4Trajectory] = None,
        temporal_history: Optional[TemporalHistory] = None,
    ) -> dict:
        """
        Loop 1-2 + Loop 2.5 (Diagnosis) + Loop 3 + Protocol Preview.
        한 호출로 전체 자료.
        """
        # Loop 1-2 + Diagnosis
        assessment = self.assess_patient(
            patient_id, cognitive_levels, v1_state, v2_desire,
            v4_trajectory, temporal_history,
        )
        
        v3 = assessment["v3_skill"]
        v4 = assessment["v4_trajectory"]
        
        # Loop 3
        decision = self.decide_treatment(
            patient_id, v1_state, v2_desire, v3, v4,
            safety_flags=assessment["safety_flags"],
            clinical_report=assessment["clinical_report"],
            dde_result=assessment["differential_diagnosis"],
        )
        
        # 프로토콜 미리보기
        protocol_preview = self.generate_protocol(
            patient_id=patient_id,
            selected_axis=v2_desire.primary_clinical_axis,
            v1=v1_state, v2=v2_desire, v3=v3, v4=v4,
            clinical_report=assessment["clinical_report"],
        )
        
        # 프로토콜 효과 시뮬레이션
        protocol_simulation = self.simulate_protocol_effect(
            baseline_cognitive=cognitive_levels,
            protocol=protocol_preview,
        )
        
        return {
            "assessment": assessment,
            "decision": decision,
            "protocol_preview": protocol_preview,
            "protocol_simulation": protocol_simulation,
            "system_state_snapshot": {
                "episode_count": self.state.episode_count,
                "global_learning_pause": self.state.global_learning_pause,
                "weights": self.state.weights,
            },
        }
