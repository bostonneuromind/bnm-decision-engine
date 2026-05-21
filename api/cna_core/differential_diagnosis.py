"""
CNA v7 — Differential Diagnosis Engine (DDE) — REVISED

핵심 catch한 결함:
  - 이전 자료는 임상 5축 점수에서 진단을 추론 ❌
  - 임상 5축 점수는 매핑 결과지 입력 ❌
  - 진단은 (1) 환자 증상 호소 (2) 시간 패턴 (3) biomarker (4) 인지 약점 으로 추론

REVISED 자료:
  - Primary signal: symptom_vector (환자가 호소하는 증상)
  - Supporting: cognitive_levels (Fischer 5축), biomarkers
  - Decisive: temporal_history (감별의 핵심)
  - 임상 5축 점수는 사용 X (circular reasoning 방지)

알고리즘:
  P(diagnosis | symptoms, cognitive, biomarkers, temporal) 
    ∝ P(symptoms | dx) × P(cog | dx) × P(bio | dx) × P(temporal | dx) × P(dx)

Boston Neuromind LLC · 2026
"""

from pathlib import Path
from typing import Optional, Literal
from datetime import datetime
import yaml
import numpy as np
from pydantic import BaseModel, Field

from cna_core.types import V1State


CONFIG_PATH = Path(__file__).parent.parent / "config" / "diagnostic_patterns.yaml"


# ============================================================
# Symptom signatures per diagnosis (NEW - 핵심 데이터)
# ============================================================

# 각 진단의 expected symptom 패턴
# Key: symptom name (V1State.symptom_vector key)
# Value: expected 강도 0.0-1.0
DIAGNOSIS_SYMPTOM_SIGNATURES = {
    "adhd_inattentive": {
        "inattention": 0.80,
        "distractibility": 0.70,
        "executive_dysfunction": 0.60,
        "anxiety_somatic": 0.20,
        "anxiety_cognitive": 0.20,
        "low_mood": 0.15,
        "low_motivation": 0.20,
    },
    "gad": {
        "anxiety_somatic": 0.75,
        "anxiety_cognitive": 0.80,
        "inattention": 0.40,        # 걱정으로 인한 2차
        "executive_dysfunction": 0.30,
        "low_mood": 0.30,
        "low_motivation": 0.25,
    },
    "mdd": {
        "low_mood": 0.85,
        "low_motivation": 0.75,
        "social_withdrawal": 0.55,
        "anxiety_cognitive": 0.40,
        "anxiety_somatic": 0.30,
        "inattention": 0.40,        # 무기력 인지 위축
        "executive_dysfunction": 0.50,
    },
}

# Biomarker patterns per diagnosis
DIAGNOSIS_BIOMARKER_SIGNATURES = {
    "adhd_inattentive": {
        "cpt_omissions_zscore": -1.5,      # Z-score (negative = impaired)
        "cpt_rt_variability": 1.2,
        "nback_accuracy": 0.65,
        "hrv_rmssd": 30.0,                 # Normal-low
    },
    "gad": {
        "hrv_rmssd": 20.0,                 # 자료 낮음 (sympathetic dominance)
        "hrv_lf_hf": 3.0,                  # 교감 우세
        "cpt_omissions_zscore": -0.5,
        "nback_accuracy": 0.70,
    },
    "mdd": {
        "hrv_rmssd": 25.0,
        "cpt_omissions_zscore": -0.7,      # 인지 위축
        "nback_accuracy": 0.65,
    },
}


# ============================================================
# Types
# ============================================================

TemporalOnset = Literal["childhood", "adolescence", "adult", "any_age", "unknown"]
TemporalCourse = Literal["chronic", "episodic", "fluctuating", "unknown"]


class TemporalHistory(BaseModel):
    """환자 시간이 (임상 인터뷰)."""
    onset_age: Optional[int] = None
    onset_category: TemporalOnset = "unknown"
    course: TemporalCourse = "unknown"
    duration_months: Optional[int] = None
    pervasiveness: Optional[str] = None
    stress_triggered: Optional[bool] = None
    family_history: list[str] = Field(default_factory=list)
    prior_treatment_response: dict[str, str] = Field(default_factory=dict)


class DiagnosticHypothesis(BaseModel):
    """한 진단의 가능성."""
    diagnosis_id: str
    name_ko: str
    name_en: str
    posterior_probability: float = Field(ge=0.0, le=1.0)
    likelihood: float
    prior: float
    
    # 4-source likelihoods (개별 매칭)
    symptom_match: float
    cognitive_match: float
    biomarker_match: float
    temporal_match: float
    
    is_primary: bool = False
    is_comorbid: bool = False
    differential_markers_met: list[str] = Field(default_factory=list)
    differential_markers_missed: list[str] = Field(default_factory=list)


class DifferentialDiagnosisResult(BaseModel):
    """전체 감별 진단 결과."""
    patient_id: str
    timestamp: datetime
    
    hypotheses: list[DiagnosticHypothesis]
    
    primary_diagnosis: Optional[str] = None
    secondary_diagnoses: list[str] = Field(default_factory=list)
    
    comorbidity_pattern: Optional[str] = None
    comorbidity_coverage: float = 0.0
    
    treatment_priority_order: list[str] = Field(default_factory=list)
    treatment_rationale: str = ""
    
    diagnostic_confidence: float = 0.0
    flagged_for_review: bool = False
    review_reasons: list[str] = Field(default_factory=list)


# ============================================================
# Engine
# ============================================================

class DifferentialDiagnosisEngine:
    """
    Symptoms + Cognitive + Biomarkers + Temporal 자료로 Bayesian 감별 진단.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        path = config_path or CONFIG_PATH
        with open(path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        
        self.primary_patterns = self.config["primary_patterns"]
        self.comorbidity_patterns = self.config["comorbidity_patterns"]
        self.population_priors = self.config["population_priors"]
        
        # 임상 진단만 (learning/peak performance는 별도)
        self.diagnosis_ids = [
            d for d in self.primary_patterns.keys()
            if d in ("adhd_inattentive", "gad", "mdd")
        ]
    
    # ========================================
    # 4-Source Likelihoods
    # ========================================
    
    def _symptom_likelihood(
        self,
        symptom_vector: dict[str, float],
        diagnosis_id: str,
    ) -> float:
        """
        환자 호소 증상 ↔ 진단의 expected 증상 패턴 매칭.
        
        Cosine similarity on shared symptom keys.
        가장 강한 신호 자료 (진단의 1차 근거).
        """
        expected = DIAGNOSIS_SYMPTOM_SIGNATURES.get(diagnosis_id, {})
        if not expected or not symptom_vector:
            return 0.5
        
        # 모든 공통 키
        all_keys = set(expected.keys()) | set(symptom_vector.keys())
        obs = np.array([symptom_vector.get(k, 0.0) for k in all_keys])
        exp = np.array([expected.get(k, 0.0) for k in all_keys])
        
        norm_obs = np.linalg.norm(obs)
        norm_exp = np.linalg.norm(exp)
        if norm_obs == 0 or norm_exp == 0:
            return 0.3  # 자료 부족 — 낮은 likelihood
        
        cosine = float(np.dot(obs, exp) / (norm_obs * norm_exp))
        return (cosine + 1.0) / 2.0  # 0-1 scale
    
    def _cognitive_likelihood(
        self,
        cognitive_levels: dict[str, float],
        diagnosis_id: str,
    ) -> float:
        """인지 5축 약화 패턴 매칭."""
        pattern = self.primary_patterns.get(diagnosis_id, {})
        expected = pattern.get("cognitive_signature", {})
        if not expected:
            return 0.5
        
        # 약화 정도 계산
        observed_weakness = {
            axis: 1.0 - max(0.0, min(1.0, (level - 7.0) / 6.0))
            for axis, level in cognitive_levels.items()
        }
        
        axes = list(expected.keys())
        obs = np.array([observed_weakness.get(a, 0.0) for a in axes])
        exp = np.array([expected[a] for a in axes])
        
        norm_obs = np.linalg.norm(obs)
        norm_exp = np.linalg.norm(exp)
        if norm_obs == 0 or norm_exp == 0:
            return 0.5
        
        cosine = float(np.dot(obs, exp) / (norm_obs * norm_exp))
        return (cosine + 1.0) / 2.0
    
    def _biomarker_likelihood(
        self,
        biomarkers: dict[str, float],
        diagnosis_id: str,
    ) -> float:
        """Biomarker 패턴 매칭 (Z-score 거리)."""
        expected = DIAGNOSIS_BIOMARKER_SIGNATURES.get(diagnosis_id, {})
        if not expected or not biomarkers:
            return 0.5
        
        # Z-score 거리 평균
        distances = []
        for bm_name, exp_value in expected.items():
            obs_value = biomarkers.get(bm_name)
            if obs_value is None:
                continue
            
            # Normalized distance (이미 z-score 또는 표준화된 단위 가정)
            # 거리가 크면 likelihood ↓
            if "zscore" in bm_name:
                # Z-score: 직접 거리
                dist = abs(obs_value - exp_value)
            elif "hrv_rmssd" in bm_name:
                # ms 단위, 약 15 ms = 1 SD
                dist = abs(obs_value - exp_value) / 15.0
            elif "lf_hf" in bm_name:
                dist = abs(obs_value - exp_value) / 1.0
            elif "accuracy" in bm_name:
                dist = abs(obs_value - exp_value) / 0.15
            else:
                dist = abs(obs_value - exp_value)
            
            # Gaussian likelihood
            distances.append(np.exp(-0.5 * dist ** 2))
        
        if not distances:
            return 0.5
        
        return float(np.mean(distances))
    
    def _temporal_likelihood(
        self,
        history: TemporalHistory,
        diagnosis_id: str,
    ) -> float:
        """시간 패턴 매칭 (감별의 결정적 자료)."""
        pattern = self.primary_patterns.get(diagnosis_id, {})
        expected = pattern.get("temporal_pattern", {})
        if not expected:
            return 0.5
        
        # Unknown 자료 — 중립
        if history.onset_category == "unknown" and history.course == "unknown":
            return 0.5
        
        n_matches = 0
        n_evidence = 0
        
        # Onset 매칭 (강한 신호)
        if history.onset_category != "unknown":
            n_evidence += 2  # 가중
            exp_onset = expected.get("onset", "any_age")
            if exp_onset == "any_age":
                n_matches += 1  # Neutral
            elif exp_onset == history.onset_category:
                n_matches += 2  # Strong match
            elif "or" in exp_onset and history.onset_category in exp_onset:
                n_matches += 2
        
        # Course 매칭
        if history.course != "unknown":
            n_evidence += 1
            exp_course = expected.get("course", "any")
            if "any" in exp_course or history.course in exp_course:
                n_matches += 1
        
        # Pervasiveness (ADHD 핵심 marker)
        if history.pervasiveness:
            n_evidence += 1
            exp_perv = expected.get("pervasiveness", "")
            if history.pervasiveness in exp_perv:
                n_matches += 1
            elif diagnosis_id == "adhd_inattentive" and history.pervasiveness == "cross_setting":
                n_matches += 1
        
        # Stress triggered
        if history.stress_triggered is not None:
            n_evidence += 1
            exp_var = expected.get("variability", "")
            if history.stress_triggered and "stress" in exp_var:
                n_matches += 1
            elif not history.stress_triggered and ("stable" in exp_var or "chronic" in exp_var):
                n_matches += 1
        
        # Duration check
        if history.duration_months is not None:
            n_evidence += 1
            if diagnosis_id == "adhd_inattentive":
                if history.duration_months >= 60:  # 5년+
                    n_matches += 1
            elif diagnosis_id == "mdd":
                if 0.5 <= history.duration_months <= 24:  # 2주~2년 (에피소드)
                    n_matches += 1
            elif diagnosis_id == "gad":
                if history.duration_months >= 6:
                    n_matches += 1
        
        if n_evidence == 0:
            return 0.5
        
        match_rate = n_matches / n_evidence
        # 시간이가 강한 신호 자료 — 0.1-0.95 범위
        return 0.1 + 0.85 * match_rate
    
    def _check_differential_markers(
        self,
        symptom_vector: dict[str, float],
        cognitive_levels: dict[str, float],
        biomarkers: dict[str, float],
        history: TemporalHistory,
        diagnosis_id: str,
    ) -> tuple[list[str], list[str]]:
        """Differential marker 체크."""
        pattern = self.primary_patterns.get(diagnosis_id, {})
        markers = pattern.get("differential_markers", [])
        
        met = []
        missed = []
        
        for marker in markers:
            marker_lower = marker.lower()
            matched = False
            
            if diagnosis_id == "adhd_inattentive":
                if "cross-setting" in marker_lower:
                    if history.pervasiveness == "cross_setting":
                        matched = True
                elif "before age 12" in marker_lower:
                    if history.onset_age is not None and history.onset_age < 12:
                        matched = True
                elif "not better explained" in marker_lower:
                    # 증상이 ADHD 패턴 vs mood/anxiety 패턴
                    inatt = symptom_vector.get("inattention", 0.0)
                    anxiety = symptom_vector.get("anxiety_cognitive", 0.0) + symptom_vector.get("anxiety_somatic", 0.0)
                    mood = symptom_vector.get("low_mood", 0.0)
                    if inatt > anxiety / 2 and inatt > mood:
                        matched = True
            
            elif diagnosis_id == "gad":
                if "6+ months" in marker_lower or "6 months" in marker_lower:
                    if history.duration_months is not None and history.duration_months >= 6:
                        matched = True
                elif "worry > attention" in marker_lower:
                    worry = symptom_vector.get("anxiety_cognitive", 0.0) + symptom_vector.get("anxiety_somatic", 0.0)
                    inatt = symptom_vector.get("inattention", 0.0)
                    if worry > inatt:
                        matched = True
                elif "hrv rmssd" in marker_lower:
                    rmssd = biomarkers.get("hrv_rmssd", 100)
                    if rmssd < 25:
                        matched = True
                elif "concentration" in marker_lower:
                    anxiety = symptom_vector.get("anxiety_cognitive", 0.0)
                    inatt = symptom_vector.get("inattention", 0.0)
                    if anxiety > 0.5 and inatt > 0.3:
                        matched = True
            
            elif diagnosis_id == "mdd":
                if "anhedonia" in marker_lower or "2+ weeks" in marker_lower:
                    if history.duration_months is not None and history.duration_months >= 0.5:
                        mood = symptom_vector.get("low_mood", 0.0)
                        if mood > 0.5:
                            matched = True
                elif "rumination" in marker_lower:
                    sa_level = cognitive_levels.get("self_awareness", 10.0)
                    mood = symptom_vector.get("low_mood", 0.0)
                    if sa_level < 8.5 and mood > 0.5:
                        matched = True
                elif "cognitive slowing" in marker_lower:
                    nback = biomarkers.get("nback_accuracy", 1.0)
                    if nback < 0.70:
                        matched = True
                elif "sleep" in marker_lower or "appetite" in marker_lower:
                    # 직접 측정 자료 ❌, neutral
                    pass
            
            if matched:
                met.append(marker)
            else:
                missed.append(marker)
        
        return met, missed
    
    # ========================================
    # 메인 진단
    # ========================================
    
    def diagnose(
        self,
        patient_id: str,
        cognitive_levels: dict[str, float],
        clinical_scores: dict[str, float],  # 호환성, 사용 X
        symptom_vector: Optional[dict[str, float]] = None,
        biomarkers: Optional[dict[str, float]] = None,
        temporal_history: Optional[TemporalHistory] = None,
        use_cohort_prior: bool = False,
        cohort_prior: Optional[dict] = None,
    ) -> DifferentialDiagnosisResult:
        """
        4-source Bayesian 감별 진단.
        
        Args:
            symptom_vector: 환자 호소 증상 (V1State.symptom_vector)
            biomarkers: 객관 측정 (V1State.biomarkers)
            temporal_history: 시간이
        """
        if temporal_history is None:
            temporal_history = TemporalHistory()
        symptom_vector = symptom_vector or {}
        biomarkers = biomarkers or {}
        
        # 각 진단별 4-source likelihood
        hypotheses = []
        
        for diag_id in self.diagnosis_ids:
            sym_lik = self._symptom_likelihood(symptom_vector, diag_id)
            cog_lik = self._cognitive_likelihood(cognitive_levels, diag_id)
            bio_lik = self._biomarker_likelihood(biomarkers, diag_id)
            tem_lik = self._temporal_likelihood(temporal_history, diag_id)
            
            # Likelihood 결합 — 증상 + 시간이 가중 (가장 강한 신호)
            likelihood = (
                0.40 * sym_lik         # 핵심: 환자 호소
                + 0.20 * cog_lik       # 인지 약점
                + 0.10 * bio_lik       # 객관 측정 (데이터 부족 시 작음)
                + 0.30 * tem_lik       # 시간 패턴 (감별 핵심)
            )
            
            # Prior
            if use_cohort_prior and cohort_prior:
                prior = cohort_prior.get(diag_id, self.population_priors.get(diag_id, 0.01))
            else:
                prior = self.population_priors.get(diag_id, 0.01)
            
            # Differential markers
            met, missed = self._check_differential_markers(
                symptom_vector, cognitive_levels, biomarkers,
                temporal_history, diag_id,
            )
            
            pattern = self.primary_patterns[diag_id]
            hyp = DiagnosticHypothesis(
                diagnosis_id=diag_id,
                name_ko=pattern["name_ko"],
                name_en=pattern["name_en"],
                posterior_probability=0.0,
                likelihood=likelihood,
                prior=prior,
                symptom_match=sym_lik,
                cognitive_match=cog_lik,
                biomarker_match=bio_lik,
                temporal_match=tem_lik,
                differential_markers_met=met,
                differential_markers_missed=missed,
            )
            hypotheses.append(hyp)
        
        # Bayesian normalization with adaptive prior weighting
        # 임상 원리: 환자 개인 데이터가 명백하면 일반 인구 통계는 무시
        # - Top likelihood가 0.9+: prior 영향 거의 없음 (강한 임상 신호)
        # - Top likelihood가 약함: prior가 도움
        max_lik = max(h.likelihood for h in hypotheses) if hypotheses else 0.5
        # max_lik이 1.0에 가까우면 prior_power = 0.1 (거의 무시)
        # max_lik이 0.5면 prior_power = 0.6 (의미 있음)
        prior_power = max(0.1, 0.8 - max_lik * 0.7)
        
        # Likelihood sharpening (확실한 가설을 더 분명히)
        lik_power = 2.5
        
        unnorm = {
            h.diagnosis_id: (h.likelihood ** lik_power) * (h.prior ** prior_power)
            for h in hypotheses
        }
        total = sum(unnorm.values())
        if total > 0:
            for h in hypotheses:
                h.posterior_probability = unnorm[h.diagnosis_id] / total
        
        hypotheses.sort(key=lambda h: h.posterior_probability, reverse=True)
        
        # Primary / Secondary
        primary = None
        secondary = []
        comorbidity = None
        comorbidity_coverage = 0.0
        
        if hypotheses:
            top = hypotheses[0]
            
            # 임계값 자료 catch: 가장 강한 자료가 압도적이지 않으면 검토
            if top.posterior_probability > 0.40:
                primary = top.diagnosis_id
                top.is_primary = True
                
                for h in hypotheses[1:]:
                    if h.posterior_probability > 0.20:
                        secondary.append(h.diagnosis_id)
                        h.is_comorbid = True
            elif top.posterior_probability > 0.30:
                # 약한 신호 — primary로 보지만 검토 필요
                primary = top.diagnosis_id
                top.is_primary = True
                for h in hypotheses[1:]:
                    if h.posterior_probability > 0.25:
                        secondary.append(h.diagnosis_id)
                        h.is_comorbid = True
            
            # Comorbidity pattern
            if primary and secondary:
                for co_id, co_data in self.comorbidity_patterns.items():
                    if (co_data["primary"] == primary 
                        and co_data["secondary"] in secondary):
                        comorbidity = co_id
                        comorbidity_coverage = co_data["coverage_rate"]
                        break
        
        # 치료 우선순위
        treatment_order, rationale = self._determine_treatment_priority(
            primary, secondary, comorbidity, hypotheses
        )
        
        confidence = self._compute_diagnostic_confidence(hypotheses, temporal_history)
        flag, reasons = self._should_flag_for_review(hypotheses, temporal_history, symptom_vector)
        
        return DifferentialDiagnosisResult(
            patient_id=patient_id,
            timestamp=datetime.utcnow(),
            hypotheses=hypotheses,
            primary_diagnosis=primary,
            secondary_diagnoses=secondary,
            comorbidity_pattern=comorbidity,
            comorbidity_coverage=comorbidity_coverage,
            treatment_priority_order=treatment_order,
            treatment_rationale=rationale,
            diagnostic_confidence=confidence,
            flagged_for_review=flag,
            review_reasons=reasons,
        )
    
    def _determine_treatment_priority(self, primary, secondary, comorbidity, hypotheses):
        if not primary:
            return [], "진단 신뢰도 부족. 추가 평가 필요."
        
        if comorbidity:
            co_data = self.comorbidity_patterns[comorbidity]
            return co_data["treatment_sequence"], (
                f"{co_data['name_ko']} 표준. 공존률 {co_data['coverage_rate']:.0%} 임상 패턴."
            )
        
        pattern = self.primary_patterns[primary]
        return [primary] + secondary, (
            f"Primary: {pattern['name_ko']}. {pattern['treatment_priority']}."
        )
    
    def _compute_diagnostic_confidence(self, hypotheses, history):
        if not hypotheses:
            return 0.0
        
        top = hypotheses[0]
        confidence = top.posterior_probability * 0.4
        
        if len(hypotheses) > 1:
            gap = top.posterior_probability - hypotheses[1].posterior_probability
            confidence += gap * 0.3
        
        if history.onset_category != "unknown":
            confidence += 0.10
        if history.course != "unknown":
            confidence += 0.05
        if history.pervasiveness:
            confidence += 0.05
        
        n_met = len(top.differential_markers_met)
        n_total = n_met + len(top.differential_markers_missed)
        if n_total > 0:
            confidence += 0.10 * (n_met / n_total)
        
        return min(1.0, confidence)
    
    def _should_flag_for_review(self, hypotheses, history, symptom_vector):
        reasons = []
        
        if not hypotheses:
            return True, ["No diagnostic hypotheses"]
        
        top = hypotheses[0]
        
        if top.posterior_probability < 0.40:
            reasons.append("진단 확실성 낮음 — 가장 강한 가설 < 40%")
        
        if history.onset_category == "unknown" and history.course == "unknown":
            reasons.append("시간 정보 부족 — 발병/경과 미수집")
        
        if not symptom_vector:
            reasons.append("증상 호소 정보 없음 — 진단 정보 불완전")
        
        if len(hypotheses) > 1:
            gap = top.posterior_probability - hypotheses[1].posterior_probability
            if gap < 0.10:
                reasons.append(f"감별 어려움 — {top.name_ko} vs {hypotheses[1].name_ko}")
        
        # ADHD 의심인데 발병 나이 확인 안 됨
        adhd_hyp = next((h for h in hypotheses if h.diagnosis_id == "adhd_inattentive"), None)
        if adhd_hyp and adhd_hyp.posterior_probability > 0.30:
            if history.onset_age is None:
                reasons.append("ADHD 의심 — 발병 나이 (<12) 확인 필요")
        
        return len(reasons) > 0, reasons
