"""단계 2 변환 단위 검증 — convert.measurements_to_levels.
실행: <venv>/python api/measurement_mappings/_verify.py (cwd=repo root, sys.path=api).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from measurement_mappings import measurements_to_levels
from measurement_mappings.cpt import cpt_to_sustained_attention_l

results = []
def check(n, ok, d=""):
    results.append(f"{'PASS' if ok else 'FAIL'} {n}{' — ' + str(d) if d else ''}")

FULL = {
    "measurements": {
        "hrv": {"rmssd": 42.5, "duration_sec": 60},
        "time": {"target_sec": 30, "estimated_sec": 28.1, "error_pct": 6.3},
        "cpt": {"accuracy": 0.9, "rt_mean": 450, "rt_cv": 0.2, "duration_min": 2,
                "hits": 18, "misses": 2, "false_alarms": 1},
        "nback": {"n_level": 2, "accuracy": 0.8, "false_alarm_rate": 0.1, "rt_mean": 600},
        "vsr": {"valence": 0.3, "arousal": 0.5, "stem_phrase_id": "demo_1"},
    },
    "quality": {"hrv_mock": False, "vsr_demo": True},
    "policy": {
        "missing_cognitive_axes": {
            "self_awareness": {"level": 9.0, "confidence": 0.3},
            "emotional_regulation": {"level": 9.0, "confidence": 0.3, "only_when": "hrv_mock"},
        },
        "hrv_mock_block": True,
    },
}

# --- 미러 함수 출력 대조 (cpt acc 0.9→acc_l 10.0; rt_cv 0.2 는 <=0.20 경계라 cv_adj 0.0 → 10.0) ---
fl = cpt_to_sustained_attention_l({"accuracy": 0.9, "rt_mean": 450, "rt_cv": 0.2, "duration_min": 2})
check("cpt mirror level=10.0", abs(fl.level - 10.0) < 1e-9, fl.level)
# rt_cv 0.1(<=0.15)이면 cv_adj +0.2 → 10.0+0.1=10.1 로 변별 확인
fl2 = cpt_to_sustained_attention_l({"accuracy": 0.9, "rt_mean": 450, "rt_cv": 0.1, "duration_min": 2})
check("cpt mirror cv-sensitive=10.1", abs(fl2.level - 10.1) < 1e-9, fl2.level)

# --- 완주 케이스: 5축 전부 + biomarkers ---
r = measurements_to_levels(FULL)
cl = r["cognitive_levels"]
check("5 cognitive axes present",
      set(cl) == {"sustained_attention", "working_memory", "time_awareness", "emotional_regulation", "self_awareness"},
      list(cl))
check("sustained_attention from cpt", r["sources"]["sustained_attention"] == "cpt", cl["sustained_attention"])
check("working_memory from nback", r["sources"]["working_memory"] == "nback", cl["working_memory"])
check("time_awareness 30s_as_one_min", r["sources"]["time_awareness"] == "time(30s_as_one_min)", cl["time_awareness"])
check("ER from hrv (not mock)", r["sources"]["emotional_regulation"] == "hrv", cl["emotional_regulation"])
check("self_awareness omr_absent neutral", r["sources"]["self_awareness"] == "neutral_default(omr_absent)" and cl["self_awareness"] == 9.0)
check("all levels in L7-13", all(7.0 <= v <= 13.0 for v in cl.values()), cl)

bm = r["biomarkers"]
check("biomarker rt_variability raw", bm.get("cpt_rt_variability") == 0.2, bm)
check("biomarker nback_accuracy raw", bm.get("nback_accuracy") == 0.8)
check("biomarker omissions z = (0.9-0.92)/0.06", abs(bm.get("cpt_omissions_zscore") - ((0.9-0.92)/0.06)) < 1e-9, bm.get("cpt_omissions_zscore"))
check("biomarker hrv_rmssd present (not mock)", bm.get("hrv_rmssd") == 42.5)

# --- HRV mock 케이스: ER 중립 + hrv_rmssd 엔진 투입 금지 ---
mock = {k: (dict(v) if isinstance(v, dict) else v) for k, v in FULL.items()}
mock["quality"] = {"hrv_mock": True}
rm = measurements_to_levels(mock)
check("ER neutral when hrv_mock", rm["sources"]["emotional_regulation"] == "neutral_default(hrv_mock_blocked)", rm["sources"]["emotional_regulation"])
check("ER level = policy neutral 9.0", rm["cognitive_levels"]["emotional_regulation"] == 9.0)
check("hrv_rmssd EXCLUDED from biomarkers", "hrv_rmssd" not in rm["biomarkers"], list(rm["biomarkers"]))
check("quality flag hrv_blocked", rm["quality"]["hrv_blocked"] is True)

# --- 결측 케이스: cpt 없음 → 중립 + 마커 ---
miss = {"measurements": {"nback": FULL["measurements"]["nback"]}, "quality": {}, "policy": FULL["policy"]}
rmi = measurements_to_levels(miss)
check("missing cpt → neutral", rmi["sources"]["sustained_attention"] == "neutral_default(missing_cpt)")
check("missing cpt → still 5 axes", len(rmi["cognitive_levels"]) == 5)
check("missing cpt → no cpt biomarkers", "cpt_rt_variability" not in rmi["biomarkers"])

# --- policy 미전달 → DEFAULT_POLICY 방어 ---
rdef = measurements_to_levels({"measurements": FULL["measurements"], "quality": {"hrv_mock": True}})
check("default policy blocks hrv too", rdef["sources"]["emotional_regulation"].startswith("neutral_default"))

print("\n".join(results))
fails = [x for x in results if x.startswith("FAIL")]
print(f"\n{len(results)-len(fails)}/{len(results)} PASS")
sys.exit(1 if fails else 0)
