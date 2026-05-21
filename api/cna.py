"""
Vercel Serverless Function — Decision Catcher API

CNA v7 백엔드를 Vercel에 호스팅합니다.
모든 cna_core 모듈 자료가 같은 directory에 있다고 가정.

배포:
  Vercel CLI: vercel deploy
  
구조:
  /api/cna.py     ← 이 파일 (모든 API 자료)
  /api/cna_core/  ← v7 모듈 자료 (symlink 또는 복사)
"""

import sys
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

# cna_core 자료 경로
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

try:
    from cna_core import (
        CNAOrchestrator, V1State, V2Desire, V3Skill, V4Trajectory,
        TemporalHistory, DifferentialDiagnosisResult, TreatmentResponse,
        detect_crisis, format_safety_alert,
        get_default_card_deck, CLINICAL_AXES,
    )
    CNA_AVAILABLE = True
except ImportError as e:
    print(f"CNA import error: {e}")
    CNA_AVAILABLE = False


# Global orchestrator (Lambda warm reuse)
_orchestrator = None

def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = CNAOrchestrator()
    return _orchestrator


# ============================================================
# Vercel Handler
# ============================================================

class handler(BaseHTTPRequestHandler):
    
    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str, ensure_ascii=False).encode('utf-8'))
    
    def _send_error(self, status, message):
        self._send_json(status, {'error': message})
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _read_json(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw)
    
    def do_GET(self):
        path = urlparse(self.path).path
        # /api 자료 stripping
        if path.startswith('/api'):
            path = path[4:]
        
        if not CNA_AVAILABLE:
            self._send_error(500, 'CNA core not available')
            return
        
        if path == '/health' or path == '':
            orch = get_orchestrator()
            self._send_json(200, {
                'status': 'ok',
                'version': '7.0.0',
                'episode_count': orch.state.episode_count,
                'cna_available': True,
            })
        elif path == '/cards':
            cards = get_default_card_deck()
            self._send_json(200, {
                'n_cards': len(cards),
                'cards': [c.model_dump() for c in cards],
            })
        elif path == '/system/state':
            orch = get_orchestrator()
            self._send_json(200, {
                'episode_count': orch.state.episode_count,
                'weights': orch.state.weights,
                'global_learning_pause': orch.state.global_learning_pause,
                'alerts': orch.state.alerts[-5:] if orch.state.alerts else [],
            })
        else:
            self._send_error(404, f'Not found: {path}')
    
    def do_POST(self):
        path = urlparse(self.path).path
        if path.startswith('/api'):
            path = path[4:]
        
        if not CNA_AVAILABLE:
            self._send_error(500, 'CNA core not available')
            return
        
        try:
            body = self._read_json()
        except Exception as e:
            self._send_error(400, f'Invalid JSON: {e}')
            return
        
        try:
            if path == '/full-cycle':
                self._handle_full_cycle(body)
            elif path == '/assess':
                self._handle_assess(body)
            elif path == '/diagnose':
                self._handle_diagnose(body)
            elif path == '/decompose':
                self._handle_decompose(body)
            elif path == '/simulate/intervention':
                self._handle_simulate_intervention(body)
            elif path == '/simulate/target-levels':
                self._handle_simulate_target_levels(body)
            elif path == '/reroute':
                self._handle_reroute(body)
            elif path == '/safety/check':
                self._handle_safety_check(body)
            elif path == '/protocol/generate':
                self._handle_protocol_generate(body)
            else:
                self._send_error(404, f'Not found: {path}')
        except Exception as e:
            import traceback
            self._send_error(500, f'{type(e).__name__}: {e}\n{traceback.format_exc()}')
    
    # ============================================================
    # Handlers
    # ============================================================
    
    def _handle_full_cycle(self, body):
        orch = get_orchestrator()
        
        v1 = V1State(
            symptom_vector=body.get('symptom_vector', {}),
            biomarkers=body.get('biomarkers', {}),
            biomarker_variance=body.get('biomarker_variance', {}),
        )
        v2 = V2Desire(
            primary_clinical_axis=body['primary_clinical_axis'],
            preferred_outcomes=body.get('preferred_outcomes', {}),
            motivation=body.get('motivation', 0.5),
            barriers=body.get('barriers', []),
        )
        v4 = V4Trajectory(n_sessions=body.get('n_sessions', 0))
        
        temporal = None
        if body.get('temporal_history'):
            temporal = TemporalHistory(**body['temporal_history'])
        
        result = orch.run_full_assessment_cycle(
            patient_id=body['patient_id'],
            cognitive_levels=body['cognitive_levels'],
            v1_state=v1,
            v2_desire=v2,
            v4_trajectory=v4,
            temporal_history=temporal,
        )
        
        # Serialize
        out = {
            'assessment': {
                'clinical_report': result['assessment']['clinical_report'].model_dump(),
                'safety_flags': [f.model_dump() for f in result['assessment']['safety_flags']],
                'imminent_safety': result['assessment']['imminent_safety'],
                'v3_skill': result['assessment']['v3_skill'].model_dump(),
                'differential_diagnosis': result['assessment']['differential_diagnosis'].model_dump(),
                'comorbidity_profile': result['assessment']['comorbidity_profile'].model_dump(),
                'intervention_ranking': result['assessment']['intervention_ranking'].model_dump(),
                'target_levels': result['assessment']['target_levels'],
            },
            'decision': {
                'candidate_cards': [sc.model_dump() for sc in result['decision']['candidate_cards']],
                'top_recommendation': result['decision']['top_recommendation'].model_dump() if result['decision']['top_recommendation'] else None,
                'safety_filtered': result['decision']['safety_filtered'],
                'emergency_phase_active': result['decision']['emergency_phase_active'],
                'diagnosis_aligned': result['decision']['diagnosis_aligned'],
                'n_cards_considered': result['decision']['n_cards_considered'],
            },
            'protocol_preview': result['protocol_preview'].model_dump(),
            'protocol_simulation': result['protocol_simulation'].model_dump() if result.get('protocol_simulation') else None,
            'system_state_snapshot': result['system_state_snapshot'],
        }
        
        self._send_json(200, out)
    
    def _handle_assess(self, body):
        # full-cycle 보다 짧은 자료 — assessment만
        orch = get_orchestrator()
        v1 = V1State(
            symptom_vector=body.get('symptom_vector', {}),
            biomarkers=body.get('biomarkers', {}),
        )
        v2 = V2Desire(
            primary_clinical_axis=body['primary_clinical_axis'],
            motivation=body.get('motivation', 0.5),
            barriers=body.get('barriers', []),
        )
        v4 = V4Trajectory(n_sessions=body.get('n_sessions', 0))
        
        temporal = None
        if body.get('temporal_history'):
            temporal = TemporalHistory(**body['temporal_history'])
        
        result = orch.assess_patient(
            patient_id=body['patient_id'],
            cognitive_levels=body['cognitive_levels'],
            v1_state=v1,
            v2_desire=v2,
            v4_trajectory=v4,
            temporal_history=temporal,
        )
        
        self._send_json(200, {
            'clinical_report': result['clinical_report'].model_dump(),
            'safety_flags': [f.model_dump() for f in result['safety_flags']],
            'differential_diagnosis': result['differential_diagnosis'].model_dump(),
            'comorbidity_profile': result['comorbidity_profile'].model_dump(),
            'intervention_ranking': result['intervention_ranking'].model_dump(),
            'target_levels': result['target_levels'],
        })
    
    def _handle_diagnose(self, body):
        orch = get_orchestrator()
        temporal = TemporalHistory(**body['temporal_history']) if body.get('temporal_history') else None
        result = orch.dde.diagnose(
            patient_id=body['patient_id'],
            cognitive_levels=body['cognitive_levels'],
            clinical_scores=body.get('clinical_scores', {}),
            symptom_vector=body.get('symptom_vector', {}),
            biomarkers=body.get('biomarkers', {}),
            temporal_history=temporal,
        )
        self._send_json(200, result.model_dump())
    
    def _handle_decompose(self, body):
        orch = get_orchestrator()
        dde = DifferentialDiagnosisResult(**body['dde_result'])
        result = orch.decomposer.decompose(
            patient_id=body['patient_id'],
            cognitive_levels=body['cognitive_levels'],
            clinical_scores=body['clinical_scores'],
            dde_result=dde,
        )
        self._send_json(200, result.model_dump())
    
    def _handle_simulate_intervention(self, body):
        orch = get_orchestrator()
        result = orch.simulator.rank_intervention_candidates(
            baseline_cognitive=body['baseline_cognitive'],
            target_clinical_axis=body.get('target_clinical_axis'),
            target_delta=body.get('target_delta', 1.0),
        )
        self._send_json(200, result.model_dump())
    
    def _handle_simulate_target_levels(self, body):
        orch = get_orchestrator()
        result = orch.simulator.recommend_target_levels(
            baseline_cognitive=body['baseline_cognitive'],
            target_clinical_axis=body['target_clinical_axis'],
            target_clinical_score=body.get('target_clinical_score', 0.65),
        )
        self._send_json(200, result)
    
    def _handle_reroute(self, body):
        orch = get_orchestrator()
        prev = DifferentialDiagnosisResult(**body['previous_diagnosis'])
        
        cog_before = body['cognitive_before']
        cog_after = body['cognitive_after']
        clin_before = body['clinical_before']
        clin_after = body['clinical_after']
        
        tr = TreatmentResponse(
            episode_id=body['episode_id'],
            primary_intervention_axis=body['primary_intervention_axis'],
            intervention_cards=body.get('intervention_cards', []),
            cognitive_before=cog_before,
            cognitive_after=cog_after,
            clinical_before=clin_before,
            clinical_after=clin_after,
            cognitive_changes={k: cog_after.get(k, v) - v for k, v in cog_before.items()},
            clinical_changes={k: clin_after.get(k, v) - v for k, v in clin_before.items()},
        )
        
        temporal = TemporalHistory(**body['temporal_history']) if body.get('temporal_history') else None
        
        result = orch.rerouter.reroute(
            patient_id=body['patient_id'],
            previous_diagnosis=prev,
            treatment_response=tr,
            temporal_history=temporal,
        )
        self._send_json(200, result.model_dump())
    
    def _handle_safety_check(self, body):
        flags = detect_crisis(
            recent_utterances=body.get('recent_utterances', []),
            phq9_scores=body.get('phq9_scores'),
            language=body.get('language', 'ko'),
        )
        self._send_json(200, {
            'n_flags': len(flags),
            'flags': [f.model_dump() for f in flags],
            'alert_text': format_safety_alert(flags, body.get('language', 'ko')) if flags else None,
        })
    
    def _handle_protocol_generate(self, body):
        orch = get_orchestrator()
        v1 = V1State(
            symptom_vector=body.get('symptom_vector', {}),
            biomarkers=body.get('biomarkers', {}),
        )
        v2 = V2Desire(
            primary_clinical_axis=body['primary_clinical_axis'],
            motivation=body.get('motivation', 0.5),
        )
        v3 = V3Skill(axis_levels=body['cognitive_levels'])
        v4 = V4Trajectory(n_sessions=body.get('n_sessions', 0))
        
        if body['selected_axis'] not in CLINICAL_AXES:
            self._send_error(400, f"selected_axis must be one of {CLINICAL_AXES}")
            return
        
        protocol = orch.generate_protocol(
            patient_id=body['patient_id'],
            selected_axis=body['selected_axis'],
            v1=v1, v2=v2, v3=v3, v4=v4,
            custom_weeks=body.get('custom_weeks'),
        )
        self._send_json(200, protocol.model_dump())
