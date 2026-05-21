"""
CNA v6 — Variational Belief Update (Loop 7 Feedback)

Friston Active Inference framework:
  학습 = prediction_error × precision × learning_rate × contribution

DecisionEpisode 한 번 commit하면 4가지 진화 자리 동시 update:
  1. Free Energy 가중치 학습
  2. Cognitive→Clinical 매핑 학습
  3. Pattern library 자료 누적
  4. Crisis FN/FP 추적

안전 장치:
  - Imperturbable anchor (학습 면역)
  - Clinician override always wins
  - Discrepancy logging
  - Volatility rollback

Boston Neuromind LLC · 2026
"""

from datetime import datetime
from typing import Optional
from pathlib import Path
import yaml
import numpy as np

from cna_core.types import DecisionEpisode, SystemState
from cna_core.cognitive_clinical_mapper import CognitiveClinicalMapper
from cna_core.free_energy_scorer import FreeEnergyScorer


CONFIG_PATH = Path(__file__).parent.parent / "config" / "free_energy_weights.yaml"


def _load_learning_config(config_path: Optional[Path] = None) -> dict:
    """학습 자료 설정 로드."""
    path = config_path or CONFIG_PATH
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def variational_belief_update(
    episode: DecisionEpisode,
    state: SystemState,
    mapper: CognitiveClinicalMapper,
    config: Optional[dict] = None,
) -> SystemState:
    """
    Outcome 자료 있는 episode → 4가지 진화 자리 동시 update.
    
    Active Inference 원리:
      update_magnitude = prediction_error × precision × learning_rate × contribution
    """
    if episode.outcome_score is None:
        return state
    
    if state.global_learning_pause:
        state.alerts.append(f"Episode {episode.episode_id}: learning paused")
        return state
    
    config = config or _load_learning_config()
    learning_cfg = config["learning"]
    
    # ========================================
    # 0. 통합 신호 (Active Inference)
    # ========================================
    predicted_outcome = episode.system_top1.expected_outcome
    observed_outcome = episode.outcome_score
    prediction_error = observed_outcome - predicted_outcome
    
    outcome_precision = 1.0 / (episode.outcome_variance + 1e-3)
    outcome_precision = min(outcome_precision, 5.0)
    
    # 임상가 disagreement 신호
    expert_signal = 0.0
    if not episode.agreement:
        clinician_in_candidates = next(
            (c for c in episode.candidate_cards if c.card.id == episode.clinician_choice.id),
            None,
        )
        if clinician_in_candidates:
            clinician_predicted = clinician_in_candidates.card.expected_outcome
            clinician_residual = abs(observed_outcome - clinician_predicted)
            system_residual = abs(prediction_error)
            expert_signal = (system_residual - clinician_residual) * 0.5
    
    expert_multiplier = learning_cfg["safety"]["expert_signal_multiplier"]
    
    # ========================================
    # 1. 진화 A: Free Energy 가중치 update
    # ========================================
    weight_changes = {}
    breakdown_dict = episode.candidate_cards[0].breakdown.model_dump()
    
    for component_name in [
        "accuracy_symptom", "accuracy_biomarker",
        "preference", "epistemic_value", "pragmatic_value",
        "complexity_penalty",
    ]:
        # System state weights key 매핑
        weight_key = {
            "epistemic_value": "epistemic",
            "pragmatic_value": "pragmatic",
        }.get(component_name, component_name)
        
        if weight_key not in state.weights:
            continue
        
        # Fixed component 면역
        if weight_key in state.fixed_components:
            continue
        
        contribution = breakdown_dict.get(component_name, 0.0)
        if not isinstance(contribution, (int, float)):
            continue
        
        # Update magnitude
        delta_outcome = (
            prediction_error
            * contribution
            * outcome_precision
            * state.learning_rate["weights"]
        )
        delta_expert = (
            expert_signal
            * contribution
            * state.learning_rate["weights"]
            * expert_multiplier
        )
        delta = delta_outcome + delta_expert
        
        old = state.weights[weight_key]
        state.weights[weight_key] = float(np.clip(old + delta, 0.05, 0.40))
        weight_changes[weight_key] = state.weights[weight_key] - old
    
    state.weight_change_history.append({
        "episode_id": episode.episode_id,
        "changes": weight_changes,
        "prediction_error": prediction_error,
        "expert_signal": expert_signal,
        "timestamp": datetime.utcnow().isoformat(),
    })
    
    # ========================================
    # 2. 진화 B: Cognitive→Clinical 매핑 update
    # ========================================
    if episode.outcome_clinical_scores:
        mapper.update_from_outcome(
            cognitive_levels=episode.v3_skill.axis_levels,
            observed_clinical=episode.outcome_clinical_scores,
            learning_rate=state.learning_rate["cognitive_clinical_mapping"],
            precision=outcome_precision,
        )
    
    # ========================================
    # 3. 진화 C: Prediction error 자료 누적
    # ========================================
    state.recent_prediction_errors.append(prediction_error)
    if len(state.recent_prediction_errors) > 50:
        state.recent_prediction_errors = state.recent_prediction_errors[-50:]
    
    # 구조적 misfit 감지
    if len(state.recent_prediction_errors) >= 10:
        recent_abs = [abs(e) for e in state.recent_prediction_errors[-10:]]
        if float(np.mean(recent_abs)) > 0.5:
            state.alerts.append(
                f"Structural model misfit detected. "
                f"Recent |error| mean: {np.mean(recent_abs):.3f}"
            )
    
    # ========================================
    # 4. 진화 D: Crisis FN 추적
    # ========================================
    if episode.in_session_change.get("crisis_emerged_post_hoc"):
        if not episode.safety_anchors_triggered:
            state.alerts.append(
                f"Crisis FN: episode {episode.episode_id}. Manual review 필요."
            )
    
    # ========================================
    # 5. 안전 장치: Volatility rollback
    # ========================================
    max_vol = learning_cfg["safety"]["max_volatility_5_episodes"]
    if len(state.weight_change_history) >= 5 and learning_cfg["safety"]["rollback_enabled"]:
        recent_changes = state.weight_change_history[-5:]
        total_volatility = sum(
            abs(c) for changes in recent_changes
            for c in changes["changes"].values()
        )
        if total_volatility > max_vol:
            if state.weight_snapshots:
                state.weights = state.weight_snapshots[-1].copy()
                state.alerts.append(
                    f"Volatility rollback triggered. Total change: {total_volatility:.3f}"
                )
    
    # ========================================
    # 6. Snapshot (매 10 episodes)
    # ========================================
    state.episode_count += 1
    if state.episode_count % 10 == 0:
        state.weight_snapshots.append(state.weights.copy())
        if len(state.weight_snapshots) > 20:
            state.weight_snapshots = state.weight_snapshots[-20:]
    
    return state


def meta_learning_review(
    state: SystemState,
    episodes_30d: list[DecisionEpisode],
    config: Optional[dict] = None,
) -> SystemState:
    """
    월별 메타-학습 자료.
    학습률 자체 조정.
    """
    config = config or _load_learning_config()
    meta_cfg = config["learning"]["meta"]
    
    if len(episodes_30d) < 10:
        return state
    
    outcomes = [e.outcome_score for e in episodes_30d if e.outcome_score is not None]
    if len(outcomes) < 5:
        return state
    
    mean_outcome = float(np.mean(outcomes))
    
    # 학습률 조정
    for level in state.learning_rate:
        if level == "crisis":
            continue
        
        if mean_outcome > 0.1:
            state.learning_rate[level] *= 1.05
        elif mean_outcome < -0.1:
            state.learning_rate[level] *= 0.95
        
        state.learning_rate[level] = float(np.clip(
            state.learning_rate[level], 0.005, 0.1
        ))
    
    # 전체 일시 정지 조건
    if mean_outcome < meta_cfg["pause_threshold_mean_outcome"]:
        state.global_learning_pause = True
        state.alerts.append(
            f"Meta-review: global learning paused. Mean outcome: {mean_outcome:.3f}"
        )
    elif state.global_learning_pause and mean_outcome > meta_cfg["resume_threshold"]:
        state.global_learning_pause = False
        state.alerts.append("Meta-review: learning resumed")
    
    state.last_meta_review = datetime.utcnow()
    return state
