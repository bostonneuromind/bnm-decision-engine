"""
CNA Persistence Layer
임상 데이터 Supabase 영구 저장 헬퍼

Decision Catcher v7 — Boston Neuromind LLC
"""
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase import insert, select, update


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _to_jsonable(obj):
    """Pydantic 모델 또는 기타 자료를 dict로 변환"""
    if obj is None:
        return None
    if hasattr(obj, 'model_dump'):
        return obj.model_dump()
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, list):
        return [_to_jsonable(x) for x in obj]
    return obj


# ============================================================
# Client (환자) 관리
# ============================================================

def ensure_client(patient_id: str, **kwargs) -> dict:
    """
    환자 ID로 cna_clients row 가져오기. 없으면 생성.
    patient_id = 외부 식별자 (initials로 박힘)
    """
    existing = select('cna_clients', filters={'initials': f'eq.{patient_id}'})
    if existing and isinstance(existing, list) and len(existing) > 0:
        return existing[0]
    
    # 새 환자 생성
    new_client = {
        'initials': patient_id,
        'birth_year': kwargs.get('birth_year'),
        'gender': kwargs.get('gender'),
        'referral_source': kwargs.get('referral_source'),
        'primary_concerns': kwargs.get('primary_concerns', []),
        'medications': kwargs.get('medications', []),
        'beta_cohort': kwargs.get('beta_cohort', 'v7_pilot'),
    }
    result = insert('cna_clients', new_client)
    return result


def get_client_id(patient_id: str) -> Optional[str]:
    """patient_id (initials) → client_id (uuid) 변환"""
    client = ensure_client(patient_id)
    return client.get('client_id') if client else None


# ============================================================
# Assessment 영구 저장
# ============================================================

def save_locate_result(client_id: str, clinical_report) -> Optional[str]:
    """LOCATE 결과 (V1 → 임상 점수 매핑) 저장"""
    try:
        cr = _to_jsonable(clinical_report)
        row = {
            'client_id': client_id,
            'clinical_scores': cr.get('clinical_scores', {}),
            'contributing_cognitive': cr.get('contributing_cognitive', {}),
            'primary_clinical_axis': cr.get('primary_axis'),
        }
        result = insert('cna_locate_results', row)
        return result.get('locate_id') if result else None
    except Exception as e:
        print(f"[persistence] save_locate_result error: {e}", flush=True)
        return None


def save_differential_diagnosis(client_id: str, dde_result, episode_id: Optional[str] = None) -> Optional[str]:
    """감별 진단 결과 저장"""
    try:
        dr = _to_jsonable(dde_result)
        row = {
            'client_id': client_id,
            'episode_id': episode_id,
            'primary_diagnosis': dr.get('primary_diagnosis'),
            'secondary_diagnoses': dr.get('secondary_diagnoses', []),
            'comorbidity_pattern': dr.get('comorbidity_pattern'),
            'comorbidity_coverage': dr.get('comorbidity_coverage'),
            'hypotheses': dr.get('hypotheses', []),
            'treatment_priority_order': dr.get('treatment_priority_order', []),
            'treatment_rationale': dr.get('treatment_rationale'),
            'diagnostic_confidence': dr.get('diagnostic_confidence'),
            'flagged_for_review': dr.get('flagged_for_review', False),
            'review_reasons': dr.get('review_reasons', []),
        }
        result = insert('cna_differential_diagnosis', row)
        return result.get('dde_id') if result else None
    except Exception as e:
        print(f"[persistence] save_differential_diagnosis error: {e}", flush=True)
        return None


def save_comorbidity_decomposition(client_id: str, decomp_result, dde_id: Optional[str] = None) -> Optional[str]:
    """공존 진단 분해 결과 저장"""
    try:
        dr = _to_jsonable(decomp_result)
        row = {
            'client_id': client_id,
            'dde_id': dde_id,
            'decomposed_axes': dr.get('decomposed_axes', {}),
            'primary_source': dr.get('primary_source'),
            'secondary_sources': dr.get('secondary_sources', []),
            'intervention_priority': dr.get('intervention_priority', {}),
        }
        result = insert('cna_comorbidity_decomposition', row)
        return result.get('decomp_id') if result else None
    except Exception as e:
        print(f"[persistence] save_comorbidity_decomposition error: {e}", flush=True)
        return None


def save_cognitive_simulation(client_id: str, sim_result, protocol_sim=None) -> Optional[str]:
    """인지 시뮬레이션 결과 저장 (intervention ranking)"""
    try:
        sr = _to_jsonable(sim_result)
        row = {
            'client_id': client_id,
            'ranked_interventions': sr.get('ranked_interventions', []),
            'optimal_intervention': sr.get('optimal_intervention'),
            'expected_total_benefit': sr.get('expected_total_benefit'),
            'target_clinical_axis': sr.get('target_clinical_axis'),
            'target_clinical_score': sr.get('target_clinical_score'),
            'per_axis_recommendations': sr.get('per_axis_recommendations', {}),
            'protocol_simulation': _to_jsonable(protocol_sim) if protocol_sim else None,
        }
        result = insert('cna_cognitive_simulations', row)
        return result.get('sim_id') if result else None
    except Exception as e:
        print(f"[persistence] save_cognitive_simulation error: {e}", flush=True)
        return None


# ============================================================
# Decision Episode
# ============================================================

def save_decision_episode(client_id: str, candidate_cards, selected_card_id=None, rationale=None) -> Optional[str]:
    """카드 추천 / 선택 에피소드 저장"""
    try:
        cards = _to_jsonable(candidate_cards) if candidate_cards else []
        row = {
            'client_id': client_id,
            'candidate_cards': cards,
            'selected_card_id': selected_card_id,
            'selection_rationale': rationale,
            'clinician_override': False,
        }
        result = insert('cna_decision_episodes', row)
        return result.get('episode_id') if result else None
    except Exception as e:
        print(f"[persistence] save_decision_episode error: {e}", flush=True)
        return None


# ============================================================
# Safety / Crisis
# ============================================================

def save_crisis_flag(client_id: str, flag) -> Optional[str]:
    """위기 플래그 저장"""
    try:
        f = _to_jsonable(flag)
        row = {
            'client_id': client_id,
            'flag_type': f.get('flag_type', 'unknown'),
            'severity': f.get('severity', 'low'),
            'triggered_by': f.get('triggered_by'),
            'immediate_action': f.get('immediate_action'),
            'clinician_notified': False,
            'resolved': False,
        }
        result = insert('cna_crisis_log', row)
        return result.get('crisis_id') if result else None
    except Exception as e:
        print(f"[persistence] save_crisis_flag error: {e}", flush=True)
        return None


# ============================================================
# Rerouting
# ============================================================

def save_rerouting_decision(client_id: str, reroute_result, episode_id: Optional[str] = None) -> Optional[str]:
    """경로 재조정 결정 저장"""
    try:
        rr = _to_jsonable(reroute_result)
        row = {
            'client_id': client_id,
            'episode_id': episode_id,
            'previous_primary': rr.get('previous_primary'),
            'previous_secondary': rr.get('previous_secondary', []),
            'updated_primary': rr.get('updated_primary'),
            'updated_secondary': rr.get('updated_secondary', []),
            'diagnosis_changed': rr.get('diagnosis_changed', False),
            'change_type': rr.get('change_type'),
            'treatment_response_pattern': rr.get('treatment_response_pattern'),
            'rationale_ko': rr.get('rationale_ko'),
            'posterior_update_magnitude': rr.get('posterior_update_magnitude'),
            'flagged_for_review': rr.get('flagged_for_review', False),
        }
        result = insert('cna_rerouting_decisions', row)
        return result.get('reroute_id') if result else None
    except Exception as e:
        print(f"[persistence] save_rerouting_decision error: {e}", flush=True)
        return None


# ============================================================
# Training Protocol
# ============================================================

def save_training_protocol(client_id: str, protocol) -> Optional[str]:
    """훈련 프로토콜 저장"""
    try:
        p = _to_jsonable(protocol)
        row = {
            'client_id': client_id,
            'selected_axis': p.get('selected_axis'),
            'target_duration_weeks': p.get('target_duration_weeks'),
            'sessions': p.get('sessions', []),
            'weekly_progression': p.get('weekly_progression'),
            'success_criteria': p.get('success_criteria', {}),
        }
        result = insert('cna_training_protocols', row)
        return result.get('protocol_id') if result else None
    except Exception as e:
        print(f"[persistence] save_training_protocol error: {e}", flush=True)
        return None


# ============================================================
# Sense Measurements (5-Axis 측정)
# ============================================================

def save_sense_measurements(client_id: str, measurements: dict) -> Optional[str]:
    """5축 측정 데이터 저장"""
    try:
        row = {'client_id': client_id, **measurements}
        result = insert('cna_sense_measurements', row)
        return result.get('measurement_id') if result else None
    except Exception as e:
        print(f"[persistence] save_sense_measurements error: {e}", flush=True)
        return None


# ============================================================
# Session Updates (주간 진행)
# ============================================================

def save_session_update(client_id: str, session_data: dict, episode_id: Optional[str] = None) -> Optional[str]:
    """세션별 진행 상황 저장"""
    try:
        row = {
            'client_id': client_id,
            'episode_id': episode_id,
            'session_number': session_data.get('session_number'),
            'cards_completed': session_data.get('cards_completed', []),
            'omr_responses': session_data.get('omr_responses', {}),
            'cognitive_after': session_data.get('cognitive_after', {}),
            'clinical_after': session_data.get('clinical_after', {}),
        }
        result = insert('cna_session_updates', row)
        return result.get('update_id') if result else None
    except Exception as e:
        print(f"[persistence] save_session_update error: {e}", flush=True)
        return None


# ============================================================
# Outcomes (4주 outcome)
# ============================================================

def save_outcome(client_id: str, outcome_data: dict, protocol_id: Optional[str] = None) -> Optional[str]:
    """4주 outcome 평가 저장"""
    try:
        row = {
            'client_id': client_id,
            'protocol_id': protocol_id,
            'cognitive_before': outcome_data.get('cognitive_before', {}),
            'cognitive_after': outcome_data.get('cognitive_after', {}),
            'clinical_before': outcome_data.get('clinical_before', {}),
            'clinical_after': outcome_data.get('clinical_after', {}),
            'self_reported_improvement': outcome_data.get('self_reported_improvement'),
            'satisfaction': outcome_data.get('satisfaction'),
        }
        result = insert('cna_outcomes', row)
        return result.get('outcome_id') if result else None
    except Exception as e:
        print(f"[persistence] save_outcome error: {e}", flush=True)
        return None


# ============================================================
# Temporal History (병력)
# ============================================================

def save_temporal_history(client_id: str, history_data: dict) -> Optional[str]:
    """병력 (temporal history) 저장"""
    try:
        row = {'client_id': client_id, **history_data}
        result = insert('cna_temporal_history', row)
        return result.get('history_id') if result else None
    except Exception as e:
        print(f"[persistence] save_temporal_history error: {e}", flush=True)
        return None


# ============================================================
# Clinical Notes
# ============================================================

def save_clinical_note(client_id: str, note_text: str, note_type: str = 'general', clinician_id: Optional[str] = None) -> Optional[str]:
    """임상 노트 저장"""
    try:
        row = {
            'client_id': client_id,
            'clinician_id': clinician_id,
            'note_text': note_text,
            'note_type': note_type,
        }
        result = insert('cna_clinical_notes', row)
        return result.get('note_id') if result else None
    except Exception as e:
        print(f"[persistence] save_clinical_note error: {e}", flush=True)
        return None


# ============================================================
# Audit Log
# ============================================================

def audit(action: str, client_id: Optional[str] = None, actor_id: Optional[str] = None, details: Optional[dict] = None, ip: Optional[str] = None):
    """감사 로그 박기 (실패해도 조용히 통과)"""
    try:
        row = {
            'action': action,
            'client_id': client_id,
            'actor_id': actor_id,
            'details': details or {},
            'ip_address': ip,
        }
        insert('cna_audit_log', row)
    except Exception as e:
        print(f"[persistence] audit error: {e}", flush=True)


# ============================================================
# Client History 조회 (Orchestrator warm restore)
# ============================================================

def load_client_history(client_id: str) -> dict:
    """
    환자의 전체 임상 히스토리 조회
    - 최근 진단들
    - 최근 시뮬레이션
    - 최근 outcomes
    - temporal_history (병력)
    """
    try:
        history = {
            'client_id': client_id,
            'differential_diagnoses': select('cna_differential_diagnosis',
                filters={'client_id': f'eq.{client_id}', 'order': 'created_at.desc', 'limit': '10'}) or [],
            'comorbidity_decompositions': select('cna_comorbidity_decomposition',
                filters={'client_id': f'eq.{client_id}', 'order': 'created_at.desc', 'limit': '5'}) or [],
            'cognitive_simulations': select('cna_cognitive_simulations',
                filters={'client_id': f'eq.{client_id}', 'order': 'created_at.desc', 'limit': '5'}) or [],
            'rerouting_decisions': select('cna_rerouting_decisions',
                filters={'client_id': f'eq.{client_id}', 'order': 'created_at.desc', 'limit': '10'}) or [],
            'training_protocols': select('cna_training_protocols',
                filters={'client_id': f'eq.{client_id}', 'order': 'created_at.desc', 'limit': '5'}) or [],
            'outcomes': select('cna_outcomes',
                filters={'client_id': f'eq.{client_id}', 'order': 'created_at.desc', 'limit': '5'}) or [],
            'session_updates': select('cna_session_updates',
                filters={'client_id': f'eq.{client_id}', 'order': 'created_at.desc', 'limit': '20'}) or [],
            'sense_measurements': select('cna_sense_measurements',
                filters={'client_id': f'eq.{client_id}', 'order': 'measured_at.desc', 'limit': '10'}) or [],
            'crisis_flags': select('cna_crisis_log',
                filters={'client_id': f'eq.{client_id}', 'order': 'created_at.desc', 'limit': '10'}) or [],
            'temporal_history': select('cna_temporal_history',
                filters={'client_id': f'eq.{client_id}', 'order': 'collected_at.desc', 'limit': '1'}) or [],
            'clinical_notes': select('cna_clinical_notes',
                filters={'client_id': f'eq.{client_id}', 'order': 'created_at.desc', 'limit': '20'}) or [],
        }
        return history
    except Exception as e:
        print(f"[persistence] load_client_history error: {e}", flush=True)
        return {'client_id': client_id, 'error': str(e)}
