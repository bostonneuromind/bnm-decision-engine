"""
CNA v6 — Crisis Detection (Safety Layer) — Round 1 강화

PHQ-9 9번 + Columbia SSRS 자료 통합.
MA M.G.L. c. 119 §51A mandated reporter 자료 (BCN+PhD 해당).
10개 위기 룰. 영원 manual (학습 면역).

Severity:
  - moderate: 회기 내 임상가 검토
  - high: 회기 중단, 안전 프로토콜
  - imminent: 응급실/911

Boston Neuromind LLC · 2026
"""

from datetime import datetime
from typing import Optional
import re

from cna_core.types import SafetyFlag, V1State


# ============================================================
# Crisis Rules (학습 면역) — 강화 자료
# ============================================================

CRISIS_RULES = {
    "suicide_ideation_passive": {
        "name_ko": "수동적 자살 생각",
        "name_en": "Passive suicidal ideation",
        "trigger_keywords_ko": [
            "안 일어났으면", "안 깼으면", "죽었으면 좋겠다", "사라지고 싶",
            "없어지고 싶", "잠들고 안 깨면", "다 의미 없", "더는 못 견디",
            "내일이 안 왔으면", "그만 살고 싶", "이 세상에 없으면",
        ],
        "trigger_keywords_en": [
            "wished i didn't wake", "wish i were dead", "want to disappear",
            "better off not waking", "no point anymore", "can't go on",
            "wish it would end", "rather not exist",
        ],
        "severity": "moderate",
        "immediate_action": "회기 계속, 임상가 override 모드. 회기 내 안전 점검. PHQ-9 9번 직접 확인.",
        "resources_us": ["988 Suicide & Crisis Lifeline", "Crisis Text Line: text HOME to 741741"],
        "resources_ko": ["1393 자살예방상담전화", "1577-0199 정신건강상담전화"],
        "phq9_item_9_score_threshold": 1,  # PHQ-9 9번 ≥1 시 활성
    },
    "suicide_ideation_active": {
        "name_ko": "능동적 자살 생각",
        "name_en": "Active suicidal ideation",
        "trigger_keywords_ko": [
            "자살할 생각", "자해할 생각", "내 목숨 끊", "끝내고 싶",
            "스스로 죽고 싶", "내가 죽으면", "죽어버리고 싶",
            "자살 충동", "죽고 싶다는 생각",
        ],
        "trigger_keywords_en": [
            "thoughts of killing myself", "thoughts of suicide", "end my life",
            "suicidal thoughts", "want to die", "kill myself", "suicidal urges",
        ],
        "severity": "high",
        "immediate_action": "회기 중단. 안전 프로토콜 활성화. 당일 임상가 contact 필수. Columbia SSRS 정식 시행.",
        "resources_us": ["988", "Crisis Text Line: HOME to 741741"],
        "resources_ko": ["1393", "1577-0199"],
        "phq9_item_9_score_threshold": 2,
    },
    "suicide_plan_means": {
        "name_ko": "자살 계획/수단",
        "name_en": "Suicide plan or means",
        "trigger_keywords_ko": [
            "어떻게 자살할지", "방법을 정해", "준비한 게 있", "약을 모아",
            "장소를 정해", "유서를", "마지막으로 만나",
            "정리해 두었", "방법을 알아봤",
        ],
        "trigger_keywords_en": [
            "specific way", "made plans", "preparations",
            "have the means", "set a date", "wrote a note",
            "looked up methods", "have access to",
        ],
        "severity": "imminent",
        "immediate_action": (
            "긴급. 환자 혼자 두지 않음. 911 또는 ER 이송. 미성년이면 보호자 통보. "
            "crisis_log 즉시 기록. 안전 contract."
        ),
        "resources_us": ["911", "988", "Nearest ER"],
        "resources_ko": ["119", "가까운 응급실"],
        "phq9_item_9_score_threshold": 3,
    },
    "self_harm_recent": {
        "name_ko": "최근 자해",
        "name_en": "Recent self-harm",
        "trigger_keywords_ko": [
            "자기를 다치게", "긋", "화상", "부딪힘",
            "자해", "내 몸을 해", "팔에 흉터", "몸에 상처",
        ],
        "trigger_keywords_en": [
            "hurt myself", "cut myself", "self-harm", "burned myself",
            "harmed myself", "scars on my", "self-injury",
        ],
        "severity": "high",
        "immediate_action": "회기 중단. 자해 평가. 회기 내 안전 계획 필수. 의료 검토.",
        "resources_us": ["988", "Crisis Text Line"],
        "resources_ko": ["1393", "1577-0199"],
    },
    "homicidal_ideation": {
        "name_ko": "타살/타해 의도",
        "name_en": "Homicidal ideation",
        "trigger_keywords_ko": [
            "죽이고 싶", "해치고 싶", "복수", "그 사람 죽어",
            "다 죽여", "응징하고 싶",
        ],
        "trigger_keywords_en": [
            "kill them", "hurt them", "harm them", "want them dead",
            "make them pay", "revenge", "destroy them",
        ],
        "severity": "imminent",
        "immediate_action": (
            "긴급. 잠재 피해자 보호 의무 (Tarasoff v. Regents). "
            "법 집행 통보 검토. 임상가 supervisor 즉시 통보."
        ),
        "resources_us": ["911", "988"],
        "resources_ko": ["112", "119"],
    },
    "psychosis_active": {
        "name_ko": "정신증 활성",
        "name_en": "Active psychosis",
        "trigger_keywords_ko": [
            "환청", "환시", "나만 들리는", "음모",
            "감시당하", "조종당하", "마음이 읽힘", "특별한 사명",
        ],
        "trigger_keywords_en": [
            "hearing voices", "seeing things", "they're after me",
            "being watched", "mind being read", "special mission",
            "voices tell me", "visions",
        ],
        "severity": "high",
        "immediate_action": "표준 프로토콜 우회. 정신과 의뢰. 약물 평가 권장. 안전 환경 확보.",
        "resources_us": ["SAMHSA Helpline: 1-800-662-4357", "Local psychiatric ER"],
        "resources_ko": ["정신건강복지센터 1577-0199"],
    },
    "substance_acute_intoxication": {
        "name_ko": "급성 중독",
        "name_en": "Acute intoxication",
        "trigger_keywords_ko": [
            "술 마시고", "약 한 상태", "취한", "지금 취해",
            "한 잔 했", "약 먹은 상태",
        ],
        "trigger_keywords_en": [
            "drunk now", "high right now", "intoxicated",
            "had some drinks", "used drugs today",
        ],
        "severity": "high",
        "immediate_action": "회기 연기. 안전한 귀가 자료 (혼자 운전 금지). 다른 사람 contact 필요.",
        "resources_us": ["SAMHSA Helpline: 1-800-662-4357"],
        "resources_ko": ["1577-0199", "한국마약퇴치운동본부 1899-0893"],
    },
    "domestic_violence_active": {
        "name_ko": "가정폭력 진행 중",
        "name_en": "Active domestic violence",
        "trigger_keywords_ko": [
            "맞고 있", "위협받고", "감금", "남편이 때려",
            "파트너가 폭력", "위협을 당해", "겁이 나서 집에",
        ],
        "trigger_keywords_en": [
            "being hit", "being threatened", "trapped",
            "abuse at home", "afraid to go home", "partner violence",
        ],
        "severity": "imminent",
        "immediate_action": (
            "긴급. 안전 계획 우선 (탈출 경로). National DV Hotline 자료. "
            "미성년 자녀 있으면 MA DCF 51A 신고 필수."
        ),
        "resources_us": ["National DV Hotline: 1-800-799-7233", "911 if immediate danger"],
        "resources_ko": ["여성긴급전화 1366", "112"],
    },
    "child_abuse_disclosure": {
        "name_ko": "아동학대 공개",
        "name_en": "Child abuse disclosure",
        "trigger_keywords_ko": [
            "아이가 맞", "아이가 학대", "방치", "아이를 때려",
            "아이가 멍", "아이가 굶", "아이에게 손",
        ],
        "trigger_keywords_en": [
            "child being abused", "child neglected", "hitting the child",
            "child has bruises", "child going hungry",
        ],
        "severity": "imminent",
        "immediate_action": (
            "MA M.G.L. c. 119 §51A Mandated reporter 의무. "
            "DCF 즉시 신고: 800-792-5200 (밤/주말). 48시간 내 서면 보고. "
            "BCN+PhD = 'allied mental health professional' 카테고리."
        ),
        "resources_us": [
            "MA DCF Emergency: 1-800-792-5200",
            "Childhelp: 1-800-422-4453",
            "MA 51A online filing portal",
        ],
        "resources_ko": ["아동학대 신고 112", "아동권리보장원 02-6906-1000"],
    },
    "severe_dissociation": {
        "name_ko": "심한 해리",
        "name_en": "Severe dissociation",
        "trigger_keywords_ko": [
            "내가 누군지 모르", "기억이 없", "내가 아닌",
            "현실감이 없", "꿈같", "내 몸 같지 않",
        ],
        "trigger_keywords_en": [
            "don't know who i am", "missing time", "not myself",
            "derealization", "feels like a dream", "out of body",
        ],
        "severity": "moderate",
        "immediate_action": "Grounding 자료 우선 (5-4-3-2-1). 안전 환경 확인. PTSD/DID 평가 의뢰.",
        "resources_us": ["NAMI Helpline: 1-800-950-6264"],
        "resources_ko": ["정신건강복지센터 1577-0199"],
    },
}


# ============================================================
# Detection Functions — 키워드 + PHQ-9 통합
# ============================================================

def detect_crisis(
    recent_utterances: list[str],
    v1_state: Optional[V1State] = None,
    phq9_scores: Optional[dict] = None,
    interaction_history: Optional[list[dict]] = None,
    language: str = "ko",
) -> list[SafetyFlag]:
    """
    환자 발화 + 상태 + PHQ-9 자료로 위기 신호 감지.
    
    Returns: SafetyFlag 리스트.
    """
    flags = []
    
    # 발화 결합
    combined_text = " ".join(recent_utterances).lower() if recent_utterances else ""
    
    # PHQ-9 9번 자료 (자살 생각 정식 측정)
    phq9_item9 = None
    if phq9_scores:
        phq9_item9 = phq9_scores.get("item_9", phq9_scores.get("suicidal_ideation"))
    
    detected_rules = set()
    
    for rule_id, rule in CRISIS_RULES.items():
        # 키워드 매칭 (한/영)
        keywords_ko = rule.get("trigger_keywords_ko", [])
        keywords_en = rule.get("trigger_keywords_en", [])
        
        matched = False
        matched_keyword = None
        
        for kw in keywords_ko:
            if kw.lower() in combined_text:
                matched = True
                matched_keyword = kw
                break
        
        if not matched:
            for kw in keywords_en:
                if kw.lower() in combined_text:
                    matched = True
                    matched_keyword = kw
                    break
        
        # PHQ-9 자료 (자살 룰만)
        if not matched and phq9_item9 is not None:
            threshold = rule.get("phq9_item_9_score_threshold")
            if threshold is not None and phq9_item9 >= threshold:
                matched = True
                matched_keyword = f"PHQ-9 item 9 score: {phq9_item9}"
        
        if matched:
            detected_rules.add(rule_id)
            resources = {
                "us": rule.get("resources_us", []),
                "ko": rule.get("resources_ko", []),
            }
            
            flags.append(SafetyFlag(
                flag_type=rule_id,
                severity=rule["severity"],
                triggered_by=matched_keyword or "unknown",
                timestamp=datetime.utcnow(),
                immediate_action=rule["immediate_action"],
                resources=resources,
            ))
    
    return flags


def has_imminent_flag(flags: list[SafetyFlag]) -> bool:
    """Imminent 자리가 하나라도 있나?"""
    return any(f.severity == "imminent" for f in flags)


def get_highest_severity(flags: list[SafetyFlag]) -> Optional[str]:
    """가장 높은 severity 자리."""
    if not flags:
        return None
    severity_order = {"imminent": 3, "high": 2, "moderate": 1}
    sorted_flags = sorted(
        flags,
        key=lambda f: severity_order.get(f.severity, 0),
        reverse=True,
    )
    return sorted_flags[0].severity


def format_safety_alert(flags: list[SafetyFlag], language: str = "ko") -> str:
    """안전 경보 메시지 생성 (임상가 + 환자용)."""
    if not flags:
        return ""
    
    lines = []
    lines.append("⚠️ ⚠️ ⚠️  SAFETY ALERT  ⚠️ ⚠️ ⚠️")
    lines.append("=" * 60)
    
    for flag in flags:
        rule = CRISIS_RULES.get(flag.flag_type, {})
        name = rule.get(f"name_{language}", flag.flag_type)
        
        lines.append(f"\n[{flag.severity.upper()}] {name}")
        lines.append(f"  감지: {flag.triggered_by}")
        lines.append(f"  조치: {flag.immediate_action}")
        
        if flag.resources:
            res_key = "ko" if language == "ko" else "us"
            resources = flag.resources.get(res_key, [])
            if resources:
                lines.append(f"  자원: {', '.join(resources)}")
    
    lines.append("=" * 60)
    return "\n".join(lines)
