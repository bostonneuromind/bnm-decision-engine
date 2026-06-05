"""pre-session raw 측정 → CNA 엔진 입력(cognitive_levels + biomarkers) 변환.

(a)안: decision Flask 변환 엔드포인트. learning은 raw 측정 + 정책(단계1 config)만 전달.
Fischer 변환은 measurement_mappings 5함수(learning ml/mappings 미러, 변경 금지)를 그대로 호출.

결측·정책 (REPORT_PLAN 단계1/2):
  - self_awareness: pre-session에 OMR 측정 없음 → 항상 policy 중립값.
  - emotional_regulation: HRV mock(quality.hrv_mock) + hrv_mock_block면 실측 미투입 → policy 중립값.
  - hrv_rmssd biomarker: 같은 조건이면 엔진 투입 금지(모의값 진단 오염 차단).
  - time: pre-session은 30초 target, 변환 함수는 1분 라벨 — error_pct(비율)는 timescale 무관이라
    one_min_error_pct로 직접 전달(정합), source 마커로 표기.
PII 0 — 측정값/정책만. 식별자(client_id)는 받지 않음.
"""

from measurement_mappings.cpt import cpt_to_sustained_attention_l
from measurement_mappings.nback import nback_to_working_memory_l
from measurement_mappings.hrv import hrv_to_emotional_regulation_l
from measurement_mappings.time_est import time_estimation_to_time_awareness_l

# learning 단계1 DEFAULT_CONFIG와 동형. learning이 policy 미전달 시 방어적 기본.
DEFAULT_POLICY = {
    "missing_cognitive_axes": {
        "self_awareness": {"level": 9.0, "confidence": 0.3},
        "emotional_regulation": {"level": 9.0, "confidence": 0.3, "only_when": "hrv_mock"},
    },
    "hrv_mock_block": True,
}

# 측정 결측 시(완주 안 한 케이스) 방어적 중립.
_MISSING_MEASURE = {"level": 9.0, "confidence": 0.3}

# curator 01 NORMS (CPT accuracy) — cpt_omissions_zscore 산출용.
_CPT_ACC_MEAN = 0.92
_CPT_ACC_SD = 0.06


def _neutral(policy_axis, fallback=None):
    rule = policy_axis or fallback or _MISSING_MEASURE
    return float(rule.get("level", 9.0)), float(rule.get("confidence", 0.3))


def measurements_to_levels(body):
    """raw 측정 → {cognitive_levels, confidence, markers, biomarkers, sources}."""
    m = (body or {}).get("measurements") or {}
    quality = (body or {}).get("quality") or {}
    policy = (body or {}).get("policy") or DEFAULT_POLICY
    missing = policy.get("missing_cognitive_axes") or DEFAULT_POLICY["missing_cognitive_axes"]
    hrv_mock_block = policy.get("hrv_mock_block", True)
    hrv_mock = bool(quality.get("hrv_mock"))

    levels, conf, markers, sources = {}, {}, {}, {}
    biomarkers = {}

    # --- sustained_attention ← CPT ---
    cpt = m.get("cpt")
    if cpt and all(k in cpt for k in ("accuracy", "rt_mean", "rt_cv")):
        fl = cpt_to_sustained_attention_l({
            "accuracy": cpt["accuracy"], "rt_mean": cpt["rt_mean"],
            "rt_cv": cpt["rt_cv"], "duration_min": cpt.get("duration_min", 2),
        })
        levels["sustained_attention"] = fl.level
        conf["sustained_attention"] = fl.confidence
        markers["sustained_attention"] = fl.markers_matched
        sources["sustained_attention"] = "cpt"
        # biomarkers (raw 직입 + omissions z)
        biomarkers["cpt_rt_variability"] = cpt["rt_cv"]
        z = (cpt["accuracy"] - _CPT_ACC_MEAN) / _CPT_ACC_SD
        biomarkers["cpt_omissions_zscore"] = max(-3.0, min(3.0, z))
    else:
        lv, cf = _neutral(None)
        levels["sustained_attention"] = lv
        conf["sustained_attention"] = cf
        markers["sustained_attention"] = ["missing_cpt"]
        sources["sustained_attention"] = "neutral_default(missing_cpt)"

    # --- working_memory ← N-back ---
    nb = m.get("nback")
    if nb and all(k in nb for k in ("n_level", "accuracy", "false_alarm_rate")):
        fl = nback_to_working_memory_l({
            "n_level": nb["n_level"], "accuracy": nb["accuracy"],
            "false_alarm_rate": nb["false_alarm_rate"], "rt_mean": nb.get("rt_mean", 0),
        })
        levels["working_memory"] = fl.level
        conf["working_memory"] = fl.confidence
        markers["working_memory"] = fl.markers_matched
        sources["working_memory"] = "nback"
        biomarkers["nback_accuracy"] = nb["accuracy"]
    else:
        lv, cf = _neutral(None)
        levels["working_memory"] = lv
        conf["working_memory"] = cf
        markers["working_memory"] = ["missing_nback"]
        sources["working_memory"] = "neutral_default(missing_nback)"

    # --- time_awareness ← Time estimation (30초→1분 정합) ---
    tm = m.get("time")
    if tm and "error_pct" in tm:
        fl = time_estimation_to_time_awareness_l({"one_min_error_pct": tm["error_pct"]})
        levels["time_awareness"] = fl.level
        conf["time_awareness"] = fl.confidence
        markers["time_awareness"] = fl.markers_matched
        sources["time_awareness"] = "time(30s_as_one_min)"
    else:
        lv, cf = _neutral(None)
        levels["time_awareness"] = lv
        conf["time_awareness"] = cf
        markers["time_awareness"] = ["missing_time"]
        sources["time_awareness"] = "neutral_default(missing_time)"

    # --- emotional_regulation ← HRV (mock이면 차단) ---
    hrv = m.get("hrv")
    block_hrv = hrv_mock and hrv_mock_block
    if hrv and "rmssd" in hrv and not block_hrv:
        fl = hrv_to_emotional_regulation_l({
            "rmssd": hrv["rmssd"], "lf_hf_ratio": hrv.get("lf_hf_ratio", 1.5),
        })
        levels["emotional_regulation"] = fl.level
        conf["emotional_regulation"] = fl.confidence
        markers["emotional_regulation"] = fl.markers_matched
        sources["emotional_regulation"] = "hrv"
        biomarkers["hrv_rmssd"] = hrv["rmssd"]
    else:
        lv, cf = _neutral(missing.get("emotional_regulation"))
        levels["emotional_regulation"] = lv
        conf["emotional_regulation"] = cf
        markers["emotional_regulation"] = ["hrv_mock_blocked"] if block_hrv else ["missing_hrv"]
        sources["emotional_regulation"] = (
            "neutral_default(hrv_mock_blocked)" if block_hrv else "neutral_default(missing_hrv)")

    # --- self_awareness ← OMR (pre-session에 측정 없음 → 항상 중립) ---
    lv, cf = _neutral(missing.get("self_awareness"))
    levels["self_awareness"] = lv
    conf["self_awareness"] = cf
    markers["self_awareness"] = ["omr_absent"]
    sources["self_awareness"] = "neutral_default(omr_absent)"

    return {
        "cognitive_levels": levels,
        "confidence": conf,
        "markers": markers,
        "biomarkers": biomarkers,
        "sources": sources,
        "quality": {"hrv_mock": hrv_mock, "hrv_blocked": block_hrv},
    }
