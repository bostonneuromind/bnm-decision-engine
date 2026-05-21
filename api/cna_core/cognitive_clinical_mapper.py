"""
CNA v6 — Cognitive → Clinical Mapper

Layer A (Fischer 인지 5축) → Layer B (임상 결과 5축) 변환.

Active Inference framework:
  - Fischer levels = hidden states z
  - Clinical predictions = observations o
  - This mapper = likelihood function P(o | z)

매핑 행렬(5x5)은 config/cognitive_clinical_mapping.yaml에 저장.
할비가 직접 수정 가능. 코드 변경 불필요.

Boston Neuromind LLC · 2026
"""

from pathlib import Path
from typing import Optional
import yaml
import numpy as np

from cna_core.types import (
    CognitiveAxis, ClinicalAxis,
    COGNITIVE_AXES, CLINICAL_AXES,
    COGNITIVE_AXIS_KOREAN, CLINICAL_AXIS_KOREAN,
)


CONFIG_PATH = Path(__file__).parent.parent / "config" / "cognitive_clinical_mapping.yaml"


def _load_config(config_path: Optional[Path] = None) -> dict:
    """YAML 설정 로드."""
    path = config_path or CONFIG_PATH
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _config_to_matrix(config_section: dict, rows: list, cols: list) -> np.ndarray:
    """Dict-of-dict → numpy 행렬 변환."""
    matrix = np.zeros((len(rows), len(cols)))
    for i, row in enumerate(rows):
        row_data = config_section.get(row, {})
        for j, col in enumerate(cols):
            matrix[i, j] = float(row_data.get(col, 0.0))
    return matrix


class CognitiveClinicalMapper:
    """
    Fischer 인지 → 임상 5축 매핑.
    
    핵심 IP. Fischer DST 직제자 자료 + BCN 임상 큐레이션.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """설정 파일에서 매핑 행렬 로드."""
        self.config = _load_config(config_path)
        
        self.W_pos = _config_to_matrix(
            self.config["positive_loading"],
            COGNITIVE_AXES,
            CLINICAL_AXES,
        )
        self.W_neg = _config_to_matrix(
            self.config["negative_loading"],
            COGNITIVE_AXES,
            CLINICAL_AXES,
        )
        self.W_int = _config_to_matrix(
            self.config["clinical_interaction"],
            CLINICAL_AXES,
            CLINICAL_AXES,
        )
        
        # 보호 셀 자료 (학습 면역)
        self.protected_cells = set()
        for cell in self.config.get("imperturbable", {}).get("protected_cells", []):
            cog_axis, clin_axis = cell
            cog_idx = COGNITIVE_AXES.index(cog_axis)
            clin_idx = CLINICAL_AXES.index(clin_axis)
            self.protected_cells.add((cog_idx, clin_idx))
        
        # 학습 이력
        self.calibration_history: list[dict] = []
    
    # ========================================
    # 핵심: 예측 함수
    # ========================================
    
    def predict_clinical_state(
        self,
        cognitive_levels: dict[CognitiveAxis, float],
    ) -> dict[ClinicalAxis, dict]:
        """
        Fischer 인지 자료 → 임상 5축 예측.
        
        Returns:
            각 임상축의:
              - score: 0.0-1.0 (Anxiety/Depression은 높을수록 좋음)
              - confidence: 예측 신뢰도
              - contributing_cognitive: 기여 인지축
              - interpretation: 한국어 임상 해석
        """
        # 인지 자료 벡터화 (L7=0, L13=1 정규화)
        z = np.array([
            self._normalize_level(cognitive_levels.get(axis, 9.0))
            for axis in COGNITIVE_AXES
        ])
        
        # 양의 기여 (인지 강 → 임상 좋음)
        positive_contribution = z @ self.W_pos
        
        # 음의 기여 (인지 약 → 임상 나쁨)
        z_weakness = 1.0 - z
        negative_contribution = z_weakness @ self.W_neg
        
        # 최종 예측
        raw_prediction = positive_contribution - negative_contribution
        
        # Sigmoid 정규화 (0.0 - 1.0)
        prediction_normalized = 1.0 / (1.0 + np.exp(-2 * (raw_prediction - 0.5)))
        
        # 임상축 간 상호작용 적용 (선형 1차)
        interaction_adjusted = (
            prediction_normalized
            + 0.2 * (self.W_int @ prediction_normalized - prediction_normalized)
        )
        interaction_adjusted = np.clip(interaction_adjusted, 0.0, 1.0)
        
        # 결과 dict 구성
        result = {}
        for i, axis in enumerate(CLINICAL_AXES):
            contributions = {}
            for j, cog_axis in enumerate(COGNITIVE_AXES):
                pos_contrib = z[j] * self.W_pos[j, i]
                neg_contrib = z_weakness[j] * self.W_neg[j, i]
                net = pos_contrib - neg_contrib
                if abs(net) > 0.02:
                    contributions[cog_axis] = round(float(net), 3)
            
            # Confidence
            n_calibrations = len([
                h for h in self.calibration_history
                if h.get("clinical_axis") == axis
            ])
            confidence = min(1.0, 0.5 + 0.05 * n_calibrations + 0.1 * len(contributions))
            
            result[axis] = {
                "score": round(float(interaction_adjusted[i]), 3),
                "confidence": round(confidence, 3),
                "contributing_cognitive": contributions,
                "interpretation": self._interpret_score(axis, float(interaction_adjusted[i])),
            }
        
        return result
    
    # ========================================
    # 관계 분석
    # ========================================
    
    def compute_pairwise_relationships(
        self,
        clinical_state: dict[ClinicalAxis, dict],
    ) -> list[dict]:
        """
        5개 임상축 간 관계 정량 자료.
        환자가 어느 축 선택해도 다른 축에 어떻게 영향 미칠지 분석.
        """
        relationships = []
        scores = np.array([clinical_state[a]["score"] for a in CLINICAL_AXES])
        
        for i, axis_a in enumerate(CLINICAL_AXES):
            for j, axis_b in enumerate(CLINICAL_AXES):
                if i >= j:
                    continue
                
                interaction_strength = float(self.W_int[i, j])
                
                if interaction_strength > 0:
                    relationship_type = "positive_coupling"
                    description = (
                        f"{CLINICAL_AXIS_KOREAN[axis_a]} 변화 → "
                        f"{CLINICAL_AXIS_KOREAN[axis_b]} 같은 방향 "
                        f"(강도 {interaction_strength:.2f})"
                    )
                else:
                    relationship_type = "inverse_coupling"
                    description = (
                        f"{CLINICAL_AXIS_KOREAN[axis_a]} 변화 → "
                        f"{CLINICAL_AXIS_KOREAN[axis_b]} 반대 방향 "
                        f"(강도 {abs(interaction_strength):.2f})"
                    )
                
                # 현재 상태 정합성
                expected_b_from_a = 0.5 + 0.5 * interaction_strength * (scores[j] - 0.5) * 2
                current_consistency = 1.0 - min(1.0, abs(scores[i] - expected_b_from_a))
                
                relationships.append({
                    "axis_a": axis_a,
                    "axis_b": axis_b,
                    "strength": round(interaction_strength, 3),
                    "type": relationship_type,
                    "description": description,
                    "current_state_consistency": round(float(current_consistency), 3),
                })
        
        relationships.sort(key=lambda r: abs(r["strength"]), reverse=True)
        return relationships
    
    # ========================================
    # 학습 (Variational Update에서 호출)
    # ========================================
    
    def update_from_outcome(
        self,
        cognitive_levels: dict[CognitiveAxis, float],
        observed_clinical: dict[ClinicalAxis, float],
        learning_rate: float = 0.03,
        precision: float = 1.0,
    ):
        """
        Loop 7 Feedback이 호출.
        실제 임상 결과 관측 → 매핑 행렬 update (variational gradient).
        
        Active Inference: prediction error → gradient update.
        Protected cells는 학습 면역.
        """
        predicted = self.predict_clinical_state(cognitive_levels)
        
        z = np.array([
            self._normalize_level(cognitive_levels.get(axis, 9.0))
            for axis in COGNITIVE_AXES
        ])
        
        for i, axis in enumerate(CLINICAL_AXES):
            pred = predicted[axis]["score"]
            obs = observed_clinical.get(axis)
            if obs is None:
                continue
            
            error = obs - pred
            
            # Gradient: ∂L/∂W_pos[j, i] = z[j] × error
            for j in range(len(COGNITIVE_AXES)):
                # Protected cell 면역
                if (j, i) in self.protected_cells:
                    continue
                
                gradient = z[j] * error * precision * learning_rate
                self.W_pos[j, i] += gradient
                self.W_pos[j, i] = float(np.clip(self.W_pos[j, i], 0.0, 1.0))
            
            self.calibration_history.append({
                "clinical_axis": axis,
                "cognitive_levels": dict(cognitive_levels),
                "predicted": pred,
                "observed": obs,
                "error": error,
            })
        
        # 행 정규화 (각 인지축의 영향력 합 = 1.0)
        for j in range(len(COGNITIVE_AXES)):
            row_sum = self.W_pos[j].sum()
            if row_sum > 0:
                # Protected cell은 건드리지 않고 나머지만 정규화
                non_protected_mask = np.ones(len(CLINICAL_AXES), dtype=bool)
                for (jj, ii) in self.protected_cells:
                    if jj == j:
                        non_protected_mask[ii] = False
                
                non_protected_sum = self.W_pos[j, non_protected_mask].sum()
                target_sum = 1.0 - self.W_pos[j, ~non_protected_mask].sum()
                
                if non_protected_sum > 0 and target_sum > 0:
                    self.W_pos[j, non_protected_mask] *= (target_sum / non_protected_sum)
    
    # ========================================
    # 유틸리티
    # ========================================
    
    def _normalize_level(self, level: float) -> float:
        """Fischer L7-L13 → 0.0-1.0 정규화."""
        return float(np.clip((level - 7.0) / 6.0, 0.0, 1.0))
    
    def _interpret_score(self, axis: ClinicalAxis, score: float) -> str:
        """임상축 점수 해석. 한국어 임상 표현."""
        tiers = self.config["severity_tiers"]
        
        if score >= tiers["strong"]:
            level = "매우 우수"
        elif score >= tiers["good"]:
            level = "우수"
        elif score >= tiers["moderate"]:
            level = "보통"
        elif score >= tiers["needs_attention"]:
            level = "주의 필요"
        else:
            level = "임상 개입 우선"
        
        axis_kr = CLINICAL_AXIS_KOREAN[axis]
        return f"{axis_kr}: {level}"
    
    def get_severity_tier(self, axis: ClinicalAxis, score: float) -> str:
        """점수 → 단계."""
        tiers = self.config["severity_tiers"]
        if score >= tiers["strong"]:
            return "strong"
        elif score >= tiers["good"]:
            return "good"
        elif score >= tiers["moderate"]:
            return "moderate"
        elif score >= tiers["needs_attention"]:
            return "needs_attention"
        else:
            return "priority"
